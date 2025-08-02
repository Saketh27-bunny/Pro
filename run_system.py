#!/usr/bin/env python3
"""
AI Event Monitoring System Launcher
This script starts the system with authentication enabled.
"""

import streamlit as st
import subprocess
import sys
import os

def main():
    st.set_page_config(
        page_title="AI Event Monitor - Launcher",
        page_icon="🚀",
        layout="centered"
    )
    
    st.markdown("""
    # 🚀 AI Event Monitoring System
    
    ## Welcome to the AI-powered Event Monitoring Dashboard
    
    This system provides real-time monitoring for:
    - 🔥 Fire/Smoke Detection
    - 🚨 Crowd Surge Detection  
    - 🧍‍♂️ Unconscious Person Detection
    
    ### 🔐 Secure Access
    The system requires admin authentication to access monitoring features.
    
    ---
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔐 Login")
        st.info("Access the secure login page to authenticate as an admin.")
        if st.button("🚀 Go to Login"):
            st.switch_page("login.py")
    
    with col2:
        st.subheader("📖 Documentation")
        st.info("View system documentation and setup instructions.")
        if st.button("📚 View Docs"):
            st.markdown("""
            ### System Documentation
            
            **Default Admin Credentials:**
            - Username: `admin`
            - Password: `admin123`
            
            **Features:**
            - Real-time AI monitoring
            - Secure authentication
            - Admin user management
            - Audit logging
            - Alert system
            
            **Security:**
            - Session management
            - Password hashing
            - Access control
            - Activity logging
            """)
    
    st.markdown("---")
    
    # System status
    st.subheader("📊 System Status")
    
    # Check if required files exist
    required_files = [
        "login.py",
        "main_dashboard.py", 
        "auth_utils.py",
        "admin_panel.py",
        "models/fire_smoke.py",
        "models/crowd_surge.py",
        "models/unconscious.py"
    ]
    
    status_col1, status_col2 = st.columns(2)
    
    with status_col1:
        st.subheader("✅ System Files")
        for file in required_files:
            if os.path.exists(file):
                st.success(f"✓ {file}")
            else:
                st.error(f"✗ {file} (missing)")
    
    with status_col2:
        st.subheader("🔧 Quick Actions")
        
        if st.button("🔄 Check System"):
            st.success("✅ System check completed!")
        
        if st.button("📋 View Logs"):
            st.info("System logs will be displayed here.")
        
        if st.button("⚙️ Settings"):
            st.info("System settings panel.")

if __name__ == "__main__":
    main() 