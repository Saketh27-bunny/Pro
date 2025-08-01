import streamlit as st
import cv2
import time
import threading
from models.fire_smoke import check_fire_smoke
from models.crowd_surge import check_crowd_surge
from models.unconscious import check_unconscious

# Page configuration
st.set_page_config(
    page_title="AI Event Monitor Dashboard",
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
</style>
""", unsafe_allow_html=True)

# Main title
st.markdown('<h1 class="main-header">🎥 Real-Time AI Event Monitoring Dashboard</h1>', unsafe_allow_html=True)

# Sidebar for controls
with st.sidebar:
    st.header("⚙️ Dashboard Controls")
    
    # Camera selection
    camera_source = st.selectbox(
        "📷 Camera Source",
        ["Webcam (0)", "Webcam (1)", "Webcam (2)"],
        index=0
    )
    
    # Detection sensitivity
    st.subheader("🔧 Detection Settings")
    fire_threshold = st.slider("Fire Detection Sensitivity", 1000, 5000, 2000)
    crowd_threshold = st.slider("Crowd Surge Threshold", 1, 5, 2)
    
    # Start/Stop button
    if 'monitoring_active' not in st.session_state:
        st.session_state.monitoring_active = False
    
    if st.button("🚀 Start Monitoring" if not st.session_state.monitoring_active else "⏹️ Stop Monitoring"):
        st.session_state.monitoring_active = not st.session_state.monitoring_active
        st.rerun()

# Main content area
col1, col2 = st.columns([3, 1])

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
                if crowd_detected:
                    st.session_state.alert_counts['crowd'] += 1
                if unconscious_detected:
                    st.session_state.alert_counts['unconscious'] += 1
                
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
        
        # Add monitoring overlay to frame
        cv2.putText(display_frame, "AI Monitoring Active", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Calculate and display FPS
        elapsed_time = time.time() - start_time
        if elapsed_time > 0:
            fps = frame_count / elapsed_time
            cv2.putText(display_frame, f"FPS: {fps:.1f}", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Display the frame
        video_placeholder.image(display_frame, channels="BGR", use_column_width=True)
        
        # Small delay to control frame rate
        time.sleep(0.03)  # ~30 FPS
    
    cap.release()

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
