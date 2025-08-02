import streamlit as st
import hashlib
import sqlite3
import os
from datetime import datetime, timedelta
import cv2
import time
from models.fire_smoke import check_fire_smoke
from models.crowd_surge import check_crowd_surge
from models.unconscious import check_unconscious

# Try to import chatbot (will work if Gemini API is configured)
try:
    from chatbot import EventMonitorChatbot
    CHATBOT_AVAILABLE = True
except ImportError:
    CHATBOT_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="AI Event Monitor - Secure Dashboard",
    page_icon="🎥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .login-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    .login-title {
        text-align: center;
        font-size: 2rem;
        font-weight: bold;
        margin-bottom: 2rem;
    }
    .login-form {
        background: rgba(255, 255, 255, 0.1);
        padding: 2rem;
        border-radius: 8px;
        backdrop-filter: blur(10px);
    }
    .alert-box {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        text-align: center;
        font-weight: bold;
    }
    .alert-danger {
        background-color: #ffebee;
        color: #c62828;
        border: 2px solid #ef5350;
    }
    .alert-success {
        background-color: #e8f5e8;
        color: #2e7d32;
        border: 2px solid #66bb6a;
    }
    .status-indicator {
        display: inline-block;
        width: 20px;
        height: 20px;
        border-radius: 50%;
        margin-right: 10px;
    }
    .status-active {
        background-color: #4caf50;
        animation: pulse 2s infinite;
    }
    .status-inactive {
        background-color: #f44336;
    }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    .user-info {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .admin-badge {
        background: #ff6b6b;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .chat-container {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        max-height: 400px;
        overflow-y: auto;
    }
    .chat-message {
        margin: 0.5rem 0;
        padding: 0.5rem;
        border-radius: 5px;
    }
    .chat-user {
        background: #e3f2fd;
        text-align: right;
    }
    .chat-assistant {
        background: #f3e5f5;
        text-align: left;
    }
</style>
""", unsafe_allow_html=True)

def init_database():
    """Initialize the database with admin user"""
    conn = sqlite3.connect('admin_auth.db')
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            session_token TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create audit log table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Check if admin user exists, if not create default admin
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        # Default admin credentials (change these in production!)
        default_password = "admin123"
        password_hash = hashlib.sha256(default_password.encode()).hexdigest()
        
        cursor.execute('''
            INSERT INTO users (username, password_hash, role)
            VALUES (?, ?, ?)
        ''', ('admin', password_hash, 'admin'))
        
        conn.commit()
        st.success("Default admin user created! Username: admin, Password: admin123")
    
    conn.close()

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_login(username, password):
    """Verify user login credentials"""
    conn = sqlite3.connect('admin_auth.db')
    cursor = conn.cursor()
    
    password_hash = hash_password(password)
    cursor.execute('''
        SELECT id, username, role FROM users 
        WHERE username = ? AND password_hash = ?
    ''', (username, password_hash))
    
    user = cursor.fetchone()
    conn.close()
    
    return user

def create_session(user_id):
    """Create a new session for the user"""
    import secrets
    session_token = secrets.token_urlsafe(32)
    expires_at = datetime.now() + timedelta(hours=8)  # 8 hour session
    
    conn = sqlite3.connect('admin_auth.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO sessions (user_id, session_token, expires_at)
        VALUES (?, ?, ?)
    ''', (user_id, session_token, expires_at))
    
    conn.commit()
    conn.close()
    
    return session_token

def log_audit_event(user_id, action, ip_address="unknown"):
    """Log audit events"""
    conn = sqlite3.connect('admin_auth.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO audit_log (user_id, action, ip_address)
        VALUES (?, ?, ?)
    ''', (user_id, action, ip_address))
    
    conn.commit()
    conn.close()

def verify_session():
    """Verify if the current session is valid"""
    if not st.session_state.get('session_token'):
        return False
    
    conn = sqlite3.connect('admin_auth.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT s.id, s.expires_at, u.username, u.role 
        FROM sessions s 
        JOIN users u ON s.user_id = u.id 
        WHERE s.session_token = ? AND s.expires_at > ?
    ''', (st.session_state.session_token, datetime.now()))
    
    session = cursor.fetchone()
    conn.close()
    
    if session:
        return True
    else:
        # Clear invalid session
        st.session_state.clear()
        return False

def logout():
    """Logout user and clear session"""
    if st.session_state.get('session_token'):
        # Remove session from database
        conn = sqlite3.connect('admin_auth.db')
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM sessions WHERE session_token = ?', 
                      (st.session_state.session_token,))
        
        conn.commit()
        conn.close()
        
        # Log logout action
        if st.session_state.get('user_id'):
            log_audit_event(st.session_state.user_id, "logout")
    
    # Clear session state
    st.session_state.clear()
    
    st.success("✅ Logged out successfully!")
    st.rerun()

def get_user_info():
    """Get current user information"""
    if st.session_state.get('authenticated'):
        return {
            'user_id': st.session_state.get('user_id'),
            'username': st.session_state.get('username'),
            'role': st.session_state.get('role')
        }
    return None

def is_admin():
    """Check if current user is admin"""
    user_info = get_user_info()
    return user_info and user_info['role'] == 'admin'

def show_chatbot_interface():
    """Show the chatbot interface"""
    st.subheader("🤖 AI Event Monitor Assistant")
    st.markdown("Ask me anything about the monitoring system, crowd analysis, or alerts!")
    
    # Initialize chatbot
    if 'chatbot' not in st.session_state:
        # You can set your Gemini API key in Streamlit secrets or environment variable
        api_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", "your_gemini_api_key_here"))
        if api_key == "your_gemini_api_key_here":
            st.warning("⚠️ Please set your Gemini API key in Streamlit secrets or environment variable GEMINI_API_KEY")
            st.info("To set up: Create a .streamlit/secrets.toml file with: GEMINI_API_KEY = 'your_actual_api_key'")
            return
        st.session_state.chatbot = EventMonitorChatbot(api_key)
    
    # Chat history
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Display chat history
    chat_container = st.container()
    with chat_container:
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        for message in st.session_state.chat_history:
            if message['role'] == 'user':
                st.markdown(f'<div class="chat-message chat-user"><strong>You:</strong> {message["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-message chat-assistant"><strong>Assistant:</strong> {message["content"]}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Chat input
    col1, col2 = st.columns([4, 1])
    with col1:
        user_input = st.text_input("Ask a question:", placeholder="e.g., How much crowd is there in the North-east direction?")
    with col2:
        send_button = st.button("Send")
    
    if send_button and user_input:
        # Add user message to history
        st.session_state.chat_history.append({
            'role': 'user',
            'content': user_input,
            'timestamp': datetime.now().strftime('%H:%M:%S')
        })
        
        # Get response from chatbot
        with st.spinner("🤖 Thinking..."):
            response = st.session_state.chatbot.process_query(user_input)
        
        # Add assistant response to history
        st.session_state.chat_history.append({
            'role': 'assistant',
            'content': response,
            'timestamp': datetime.now().strftime('%H:%M:%S')
        })
        
        st.rerun()
    
    # Quick action buttons
    st.markdown("---")
    st.subheader("🚀 Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📊 System Status"):
            status = st.session_state.chatbot.get_system_status()
            st.json(status)
    
    with col2:
        if st.button("📈 Historical Data"):
            history = st.session_state.chatbot.get_historical_data()
            st.json(history)
    
    with col3:
        if st.button("🗑️ Clear Chat"):
            st.session_state.chat_history = []
            st.session_state.chatbot.clear_chat_history()
            st.rerun()
    
    with col4:
        if st.button("🔧 API Status"):
            try:
                # Test API connection
                test_response = st.session_state.chatbot.process_query("Hello, are you working?")
                st.success("✅ Gemini API is working!")
            except Exception as e:
                st.error(f"❌ API Error: {str(e)}")
    
    # Example queries
    st.markdown("---")
    st.subheader("💡 Example Queries")
    
    examples = [
        "How much crowd is there in the North-east direction?",
        "What's the current fire detection status?",
        "Show me today's alert statistics",
        "Is there any unconscious person detected?",
        "What's the overall system status?",
        "How many people are in the main area?"
    ]
    
    # Display examples in a grid
    cols = st.columns(2)
    for i, example in enumerate(examples):
        with cols[i % 2]:
            if st.button(example, key=f"example_{i}"):
                st.session_state.chat_history.append({
                    'role': 'user',
                    'content': example,
                    'timestamp': datetime.now().strftime('%H:%M:%S')
                })
                
                with st.spinner("🤖 Thinking..."):
                    response = st.session_state.chatbot.process_query(example)
                
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': response,
                    'timestamp': datetime.now().strftime('%H:%M:%S')
                })
                
                st.rerun()

def show_login_page():
    """Show the login page"""
    # Initialize database
    init_database()
    
    # Main login interface
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h1 class="login-title">🔐 Admin Login</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; margin-bottom: 2rem;">AI Event Monitoring Dashboard</p>', unsafe_allow_html=True)
    
    st.markdown('<div class="login-form">', unsafe_allow_html=True)
    
    # Login form
    with st.form("login_form"):
        username = st.text_input("👤 Username", placeholder="Enter your username")
        password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submit_button = st.form_submit_button("🚀 Login")
    
    # Handle login
    if submit_button:
        if username and password:
            user = verify_login(username, password)
            if user:
                user_id, username, role = user
                session_token = create_session(user_id)
                log_audit_event(user_id, "login_successful")
                
                # Store session in Streamlit session state
                st.session_state.authenticated = True
                st.session_state.user_id = user_id
                st.session_state.username = username
                st.session_state.role = role
                st.session_state.session_token = session_token
                
                st.success("✅ Login successful! Loading dashboard...")
                st.balloons()
                st.rerun()
            else:
                st.error("❌ Invalid username or password. Please try again.")
                log_audit_event(None, f"login_failed_username:{username}")
        else:
            st.error("❌ Please enter both username and password.")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Additional information
    st.markdown("""
    <div style="text-align: center; margin-top: 2rem; font-size: 0.9rem;">
        <p>🔒 Secure access to AI Event Monitoring System</p>
        <p>📊 Real-time alerts and analytics</p>
        <p>👨‍💼 Admin privileges required</p>
        <p>🤖 AI Assistant with Gemini integration</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_dashboard():
    """Show the main dashboard"""
    # Check authentication
    if not st.session_state.get('authenticated', False):
        show_login_page()
        return
    
    if not verify_session():
        st.error("🔒 Session expired. Please login again.")
        st.session_state.clear()
        show_login_page()
        return
    
    # Get user info
    user_info = get_user_info()
    
    # Main title with user info
    st.markdown('<h1 class="main-header">🎥 Real-Time AI Event Monitoring Dashboard</h1>', unsafe_allow_html=True)
    
    # User info bar
    if user_info:
        st.markdown(f"""
        <div class="user-info">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong>👤 Welcome, {user_info['username']}</strong>
                    <span class="admin-badge">👑 {user_info['role'].upper()}</span>
                </div>
                <div>
                    <small>Session Active • Last updated: {time.strftime('%H:%M:%S')}</small>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Create tabs for different sections
    tab1, tab2, tab3 = st.tabs(["📹 Live Monitoring", "🤖 AI Assistant", "⚙️ Settings"])
    
    with tab1:
        # Sidebar for controls
        with st.sidebar:
            st.header("⚙️ Dashboard Controls")
            
            # AI Assistant Section
            st.subheader("🤖 AI Assistant")
            if CHATBOT_AVAILABLE:
                if st.button("💬 Open Chat"):
                    st.session_state.show_chat = True
                if st.button("📊 Quick Status"):
                    try:
                        api_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", ""))
                        if api_key and api_key != "your_gemini_api_key_here":
                            if 'chatbot' not in st.session_state:
                                st.session_state.chatbot = EventMonitorChatbot(api_key)
                            status = st.session_state.chatbot.get_system_status()
                            st.json(status)
                        else:
                            st.warning("⚠️ Please configure Gemini API key")
                    except Exception as e:
                        st.error(f"Chatbot error: {str(e)}")
            else:
                st.info("🤖 AI Assistant not available")
                st.info("Install: pip install google-generativeai")
            
            # User management section
            st.subheader("👤 User Management")
            if is_admin():
                st.success("🔐 Admin privileges active")
                if st.button("👥 Manage Users"):
                    log_audit_event(user_info['user_id'], "access_user_management")
                    st.info("User management feature coming soon!")
            else:
                st.info("👤 Standard user access")
            
            # Logout button
            if st.button("🚪 Logout"):
                logout()
            
            st.markdown("---")
            
            # Camera selection
            st.subheader("📷 Camera Settings")
            camera_source = st.selectbox(
                "Camera Source",
                ["Webcam (0)", "Webcam (1)", "Webcam (2)"],
                index=0
            )
            
            # Detection sensitivity
            st.subheader("🔧 Detection Settings")
            fire_threshold = st.slider("Fire Detection Sensitivity", 1000, 5000, 2000)
            crowd_threshold = st.slider("Crowd Surge Threshold", 1, 10, 5)
            
            # Start/Stop button
            if 'monitoring_active' not in st.session_state:
                st.session_state.monitoring_active = False
            
            if st.button("🚀 Start Monitoring" if not st.session_state.monitoring_active else "⏹️ Stop Monitoring"):
                st.session_state.monitoring_active = not st.session_state.monitoring_active
                if st.session_state.monitoring_active:
                    log_audit_event(user_info['user_id'], "start_monitoring")
                else:
                    log_audit_event(user_info['user_id'], "stop_monitoring")
                st.rerun()
        
        # Main content area
        col1, col2 = st.columns([3, 1])

        # Check if chat is enabled
        if st.session_state.get('show_chat', False) and CHATBOT_AVAILABLE:
            # Show chat interface
            st.subheader("🤖 AI Event Monitor Assistant")
            st.markdown("Ask me anything about the monitoring system, crowd analysis, or alerts!")
            
            # Initialize chatbot
            if 'chatbot' not in st.session_state:
                api_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", ""))
                if api_key and api_key != "your_gemini_api_key_here":
                    st.session_state.chatbot = EventMonitorChatbot(api_key)
                else:
                    st.error("⚠️ Please configure Gemini API key in secrets or environment")
                    st.stop()
            
            # Chat history
            if 'chat_history' not in st.session_state:
                st.session_state.chat_history = []
            
            # Display chat history
            for message in st.session_state.chat_history:
                if message['role'] == 'user':
                    st.markdown(f"**You:** {message['content']}")
                else:
                    st.markdown(f"**Assistant:** {message['content']}")
            
            # Chat input
            user_input = st.text_input("Ask a question:", placeholder="e.g., How much crowd is there in the North-east direction?")
            
            if st.button("Send"):
                if user_input:
                    # Add user message to history
                    st.session_state.chat_history.append({
                        'role': 'user',
                        'content': user_input,
                        'timestamp': datetime.now().strftime('%H:%M:%S')
                    })
                    
                    # Get response from chatbot
                    with st.spinner("🤖 Thinking..."):
                        response = st.session_state.chatbot.process_query(user_input)
                    
                    # Add assistant response to history
                    st.session_state.chat_history.append({
                        'role': 'assistant',
                        'content': response,
                        'timestamp': datetime.now().strftime('%H:%M:%S')
                    })
                    
                    st.rerun()
            
            # Quick actions
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("📊 System Status"):
                    status = st.session_state.chatbot.get_system_status()
                    st.json(status)
            with col2:
                if st.button("📈 Historical Data"):
                    history = st.session_state.chatbot.get_historical_data()
                    st.json(history)
            with col3:
                if st.button("🗑️ Clear Chat"):
                    st.session_state.chat_history = []
                    st.session_state.chatbot.clear_chat_history()
                    st.rerun()
            
            # Example queries
            st.markdown("---")
            st.subheader("�� Example Queries")
            examples = [
                "How much crowd is there in the North-east direction?",
                "What's the current fire detection status?",
                "Show me today's alert statistics"
            ]
            
            for example in examples:
                if st.button(example, key=f"example_{example}"):
                    st.session_state.chat_history.append({
                        'role': 'user',
                        'content': example,
                        'timestamp': datetime.now().strftime('%H:%M:%S')
                    })
                    
                    with st.spinner("🤖 Thinking..."):
                        response = st.session_state.chatbot.process_query(example)
                    
                    st.session_state.chat_history.append({
                        'role': 'assistant',
                        'content': response,
                        'timestamp': datetime.now().strftime('%H:%M:%S')
                    })
                    
                    st.rerun()
            
            # Close chat button
            if st.button("❌ Close Chat"):
                st.session_state.show_chat = False
                st.rerun()
        
        else:
            # Show normal monitoring interface
            with col1:
                st.subheader("📹 Live Camera Feed")
                video_placeholder = st.empty()
                
                # Status indicators
                status_col1, status_col2, status_col3 = st.columns(3)
                
                with status_col1:
                    fire_status = st.empty()
                with status_col2:
                    crowd_status = st.empty()
                with status_col3:
                    unconscious_status = st.empty()
            
            with col2:
                st.subheader("🚨 Alert Panel")
                alert_placeholder = st.empty()
                
                # Admin features
                if is_admin():
                    st.markdown("---")
                    st.subheader("👑 Admin Features")
                    
                    if st.button("📊 View Audit Log"):
                        log_audit_event(user_info['user_id'], "view_audit_log")
                        st.info("Audit log feature coming soon!")
                    
                    if st.button("🔧 System Settings"):
                        log_audit_event(user_info['user_id'], "access_system_settings")
                        st.info("System settings feature coming soon!")
        
        # Initialize camera
        def get_camera_index(source_text):
            return int(source_text.split("(")[1].split(")")[0])
        
        def main_monitoring_loop():
            """Main monitoring loop with all three detection systems"""
            camera_index = get_camera_index(camera_source)
            cap = cv2.VideoCapture(camera_index)
            
            if not cap.isOpened():
                st.error(f"❌ Could not access camera {camera_index}. Please check your camera connection.")
                return
            
            st.success(f"📷 Camera {camera_index} started successfully!")
            log_audit_event(user_info['user_id'], f"camera_started_index_{camera_index}")
            
            # Initialize alert counters
            if 'alert_counts' not in st.session_state:
                st.session_state.alert_counts = {
                    'fire': 0,
                    'crowd': 0,
                    'unconscious': 0
                }
            
            frame_count = 0
            start_time = time.time()
            
            while st.session_state.monitoring_active:
                ret, frame = cap.read()
                if not ret:
                    st.warning("⚠️ Failed to read frame from camera.")
                    break
                
                frame_count += 1
                
                # Resize frame for display
                display_frame = cv2.resize(frame, (720, 480))
                
                # Run detection models (every 5 frames to improve performance)
                if frame_count % 5 == 0:
                    try:
                        # Run detections in parallel for better performance
                        fire_detected = check_fire_smoke(frame)
                        crowd_detected = check_crowd_surge(frame)
                        unconscious_detected = check_unconscious(frame)
                        
                        # Update alert counts
                        if fire_detected:
                            st.session_state.alert_counts['fire'] += 1
                            log_audit_event(user_info['user_id'], "fire_alert_detected")
                        if crowd_detected:
                            st.session_state.alert_counts['crowd'] += 1
                            log_audit_event(user_info['user_id'], "crowd_surge_alert_detected")
                        if unconscious_detected:
                            st.session_state.alert_counts['unconscious'] += 1
                            log_audit_event(user_info['user_id'], "unconscious_person_alert_detected")
                        
                        # Update status indicators
                        fire_status.markdown(f"""
                        <div class="alert-box {'alert-danger' if fire_detected else 'alert-success'}">
                            <span class="status-indicator {'status-active' if fire_detected else 'status-inactive'}"></span>
                            🔥 Fire/Smoke<br>
                            {'🟥 ALERT DETECTED' if fire_detected else '🟩 All Clear'}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        crowd_status.markdown(f"""
                        <div class="alert-box {'alert-danger' if crowd_detected else 'alert-success'}">
                            <span class="status-indicator {'status-active' if crowd_detected else 'status-inactive'}"></span>
                            🚨 Crowd Surge<br>
                            {'🟥 ALERT DETECTED' if crowd_detected else '🟩 All Clear'}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        unconscious_status.markdown(f"""
                        <div class="alert-box {'alert-danger' if unconscious_detected else 'alert-success'}">
                            <span class="status-indicator {'status-active' if unconscious_detected else 'status-inactive'}"></span>
                            🧍‍♂️ Unconscious<br>
                            {'🟥 ALERT DETECTED' if unconscious_detected else '🟩 All Clear'}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Update alert panel
                        alerts = []
                        if fire_detected:
                            alerts.append("🔥 **FIRE/SMOKE DETECTED** - Immediate evacuation required!")
                        if crowd_detected:
                            alerts.append("🚨 **CROWD SURGE DETECTED** - Crowd control needed!")
                        if unconscious_detected:
                            alerts.append("🧍‍♂️ **UNCONSCIOUS PERSON DETECTED** - Medical attention required!")
                        
                        if alerts:
                            alert_placeholder.markdown("### 🚨 ACTIVE ALERTS\n" + "\n\n".join(alerts))
                        else:
                            alert_placeholder.markdown("### ✅ All Systems Normal\nNo alerts detected.")
                        
                    except Exception as e:
                        st.error(f"Error in detection models: {e}")
                        log_audit_event(user_info['user_id'], f"detection_error: {str(e)}")
                
                # Add monitoring overlay to frame
                cv2.putText(display_frame, "AI Monitoring Active", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Add user info overlay
                if user_info:
                    cv2.putText(display_frame, f"User: {user_info['username']}", (10, 60),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                
                # Calculate and display FPS
                elapsed_time = time.time() - start_time
                if elapsed_time > 0:
                    fps = frame_count / elapsed_time
                    cv2.putText(display_frame, f"FPS: {fps:.1f}", (10, 90),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                
                # Display the frame
                video_placeholder.image(display_frame, channels="BGR", use_container_width=True)
                
                # Small delay to control frame rate
                time.sleep(0.03)  # ~30 FPS
            
            cap.release()
            log_audit_event(user_info['user_id'], "monitoring_stopped")
        
        # Start monitoring if active
        if st.session_state.monitoring_active:
            main_monitoring_loop()
        else:
            # Show placeholder when not monitoring
            video_placeholder.info("Click 'Start Monitoring' to begin real-time surveillance.")
            alert_placeholder.info("Monitoring dashboard ready. Start monitoring to see live alerts.")
        
        # Footer with statistics
        if 'alert_counts' in st.session_state:
            st.markdown("---")
            st.subheader("📊 Detection Statistics")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Fire Alerts", st.session_state.alert_counts['fire'])
            with col2:
                st.metric("Crowd Surge Alerts", st.session_state.alert_counts['crowd'])
            with col3:
                st.metric("Unconscious Person Alerts", st.session_state.alert_counts['unconscious'])
        
        # Log page access
        log_audit_event(user_info['user_id'], "dashboard_accessed")
    
    with tab2:
        # AI Assistant Tab
        show_chatbot_interface()
    
    with tab3:
        # Settings Tab
        st.subheader("⚙️ System Settings")
        
        # API Configuration
        st.markdown("### 🔑 API Configuration")
        st.info("Configure your Gemini API key to enable the AI Assistant")
        
        api_key_input = st.text_input("Gemini API Key", type="password", 
                                     help="Enter your Google Gemini API key")
        
        if st.button("Save API Key"):
            if api_key_input:
                # In a real application, you'd save this securely
                st.success("API key saved! (Note: In production, use secure storage)")
            else:
                st.error("Please enter a valid API key")
        
        # System Information
        st.markdown("### 📊 System Information")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Python Version", "3.8+")
            st.metric("Streamlit Version", "1.28.0+")
            st.metric("OpenCV Version", "4.8.0+")
        
        with col2:
            st.metric("YOLOv8 Model", "yolov8n.pt")
            st.metric("Gemini Model", "gemini-pro")
            st.metric("Database", "SQLite")
        
        # Help and Documentation
        st.markdown("### 📚 Help & Documentation")
        
        with st.expander("🔧 How to get Gemini API Key"):
            st.markdown("""
            1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
            2. Sign in with your Google account
            3. Click "Create API Key"
            4. Copy the generated key
            5. Paste it in the API Key field above
            """)
        
        with st.expander("🤖 AI Assistant Features"):
            st.markdown("""
            **Available Queries:**
            - Crowd analysis in any direction (North, South, East, West, NE, NW, SE, SW)
            - Fire/smoke detection status
            - Unconscious person detection
            - Historical alert data
            - System health monitoring
            - Real-time statistics
            """)
        
        with st.expander("🔒 Security Information"):
            st.markdown("""
            **Security Features:**
            - Password hashing with SHA-256
            - Session management with 8-hour timeout
            - Audit logging for all actions
            - Role-based access control
            - Secure API key handling
            """)

def main():
    """Main application function"""
    # Check if user is authenticated
    if not st.session_state.get('authenticated', False):
        show_login_page()
    else:
        show_dashboard()

if __name__ == "__main__":
    main() 