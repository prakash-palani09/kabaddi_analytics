# Kabaddi Analytics - Demo Files

This folder contains demonstration files for the project review presentation.

## 📁 Files Overview

### **Main Demo Runner**
- `demo_runner.py` - Interactive menu to run all demonstrations

### **Step-by-Step Demonstrations**
- `step1.py` - Basic Player Detection and Tracking
- `step2.py` - Court Setup and Raid Detection

### **Advanced Features**
- `enhanced_data_extract.py` - Enhanced tracking with MediaPipe pose estimation
- `video_data_extractor.py` - Comprehensive video analytics extractor

### **Requirements**
- `enhanced_requirements.txt` - Additional dependencies for advanced features

## 🚀 How to Run Demo

### **Quick Start:**
```bash
cd demo
python demo_runner.py
```

### **Individual Steps:**
```bash
# Step 1: Player Detection
python step1.py

# Step 2: Court Setup and Raids
python step2.py

# Enhanced Analytics
python enhanced_data_extract.py
```

## 📋 Prerequisites

1. **Video File**: Place your kabaddi video at `../data/videos/current_video.mp4`
2. **YOLO Model**: Ensure `../yolov8n.pt` exists
3. **Dependencies**: Install requirements from parent directory

## 🎯 Demo Features

### **Step 1 - Player Detection**
- YOLOv8 person detection
- Multi-object tracking with ByteTrack
- Real-time statistics and progress bar
- Interactive controls (SPACE to pause, ESC to exit)

### **Step 2 - Court Setup**
- Interactive midline selection (click 2 points)
- Player side detection (Blue/Red teams)
- Automatic raid detection and tracking
- Real-time raid status display

### **Enhanced Features**
- MediaPipe pose estimation
- Position smoothing and stability
- Advanced movement analysis
- Robust tracking recovery

## 🎬 Presentation Flow

1. **Introduction**: Show project overview
2. **Step 1**: Demonstrate AI detection capabilities
3. **Step 2**: Show court setup and raid logic
4. **Full Pipeline**: Complete data extraction
5. **UI Dashboard**: Interactive interface (run from parent directory)

## 📊 Expected Outputs

- Real-time video processing with overlays
- Player detection with bounding boxes
- Raid tracking with highlighted raiders
- Statistics and progress information
- CSV data files with extracted metrics

## 🔧 Troubleshooting

- Ensure video file exists at correct path
- Check that YOLO model is downloaded
- Install all required dependencies
- Run from correct directory (demo folder)

---

**Note**: These demo files are designed for presentation purposes and showcase the core capabilities of the Kabaddi Analytics system.