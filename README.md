# 🎥 AI Event Monitoring Dashboard

A real-time AI-powered crowd management and event monitoring system that detects fire/smoke, crowd surges, and unconscious persons using computer vision and machine learning.

## 🚀 Features

- **🔥 Fire/Smoke Detection**: Real-time detection of fire and smoke using color-based analysis
- **🚨 Crowd Surge Detection**: Monitors crowd density using YOLOv8 object detection with grid-based analysis
- **🧍‍♂️ Unconscious Person Detection**: Detects fallen or unconscious persons using pose analysis
- **📊 Real-time Dashboard**: Beautiful Streamlit interface with live video feed and alert system
- **⚙️ Configurable Settings**: Adjustable detection sensitivity and camera selection
- **📈 Statistics Tracking**: Monitor detection counts and system performance

## 🛠️ Installation

### Prerequisites
- Python 3.8 or higher
- Webcam or camera device
- CUDA-compatible GPU (optional, for faster inference)

### Setup Instructions

1. **Navigate to the project directory**
   ```bash
   cd event_monitor_dashboard
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Test the system**
   ```bash
   python test_models.py
   ```

4. **Run the dashboard**
   ```bash
   streamlit run main_dashboard.py
   ```

## 🎯 Usage

### Starting the Dashboard

1. Run the main dashboard:
   ```bash
   streamlit run main_dashboard.py
   ```

2. The dashboard will open in your web browser (usually at `http://localhost:8501`)

3. Use the sidebar controls to:
   - Select camera source
   - Adjust detection sensitivity
   - Start/stop monitoring

### Dashboard Interface

- **📹 Live Camera Feed**: Real-time video stream from your camera
- **🚨 Alert Panel**: Shows active alerts and system status
- **📊 Statistics**: Tracks detection counts and performance metrics
- **⚙️ Controls**: Camera selection and sensitivity settings

### Detection Models

#### Fire/Smoke Detection
- Uses HSV color space analysis
- Detects orange/yellow colors associated with fire
- Configurable sensitivity threshold

#### Crowd Surge Detection
- Uses YOLOv8 for person detection
- Grid-based analysis to monitor crowd density
- Alerts when too many people are in a single area

#### Unconscious Person Detection
- Uses YOLOv8 for person detection
- Analyzes person orientation (horizontal = potentially fallen)
- Confidence-based detection to reduce false positives

## 🔧 Configuration

### Detection Sensitivity
- **Fire Detection**: Adjust threshold (1000-5000) for fire/smoke sensitivity
- **Crowd Surge**: Set threshold (1-5) for maximum people per grid segment

### Camera Settings
- Select from multiple camera sources (0, 1, 2)
- Automatic camera detection and fallback

## 🐛 Troubleshooting

### Common Issues

1. **Camera not working**
   - Check if camera is connected and not in use by another application
   - Try different camera indices (0, 1, 2)
   - Ensure camera permissions are granted

2. **Models not loading**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Check internet connection (models are downloaded automatically)
   - Verify CUDA installation if using GPU

3. **Performance issues**
   - Reduce detection frequency by modifying the frame skip in `main_dashboard.py`
   - Use a smaller YOLO model (change `yolov8n.pt` to `yolov8s.pt` for faster inference)
   - Ensure adequate CPU/GPU resources

### Testing

Run the test script to verify all components:
```bash
python test_models.py
```

This will test:
- Camera access
- Fire/smoke detection
- Crowd surge detection
- Unconscious person detection

## 📁 Project Structure

```
event_monitor_dashboard/
├── main_dashboard.py          # Main Streamlit dashboard
├── test_models.py            # Test script for all models
├── requirements.txt          # Python dependencies
└── models/
    ├── __init__.py          # Package initialization
    ├── fire_smoke.py        # Fire/smoke detection model
    ├── crowd_surge.py       # Crowd surge detection model
    └── unconscious.py       # Unconscious person detection model
```

## 🔒 Security Considerations

- This system is designed for monitoring and alerting purposes
- Ensure compliance with local privacy laws and regulations
- Consider implementing data retention policies
- Secure camera feeds and detection data appropriately

## 🤝 Contributing

To improve the system:

1. Test with different lighting conditions
2. Adjust detection thresholds for your specific use case
3. Add new detection models as needed
4. Improve the UI/UX based on user feedback

## 📄 License

This project is for educational and monitoring purposes. Please ensure compliance with local regulations when deploying in production environments.

## 🆘 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Run the test script to identify specific problems
3. Verify all dependencies are correctly installed
4. Check camera permissions and connectivity

---

**🎉 Enjoy your AI-powered event monitoring system!** 