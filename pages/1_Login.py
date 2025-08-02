import streamlit as st
import hashlib
import sqlite3
import os
from datetime import datetime, timedelta

# Page configuration
st.set_page_config(
    page_title="Admin Login - AI Event Monitor",
    page_icon="🔐",
    layout="centered"
)

# Custom CSS for login page
st.markdown("""
<style>
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
    .stButton > button {
        width: 100%;
        background: linear-gradient(45deg, #ff6b6b, #ee5a24);
        color: white;
        border: none;
        padding: 0.75rem;
        border-radius: 5px;
        font-weight: bold;
        margin-top: 1rem;
    }
    .stButton > button:hover {
        background: linear-gradient(45deg, #ee5a24, #ff6b6b);
    }
    .error-message {
        background: rgba(255, 0, 0, 0.2);
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
        border-left: 4px solid #ff0000;
    }
    .success-message {
        background: rgba(0, 255, 0, 0.2);
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
        border-left: 4px solid #00ff00;
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

def main():
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
                
                st.success("✅ Login successful! Redirecting to dashboard...")
                st.balloons()
                
                # Redirect to main dashboard
                st.switch_page("main_dashboard.py")
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
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main() 