# Vision-Based Raid Analysis and Player Performance Profiling in Kabaddi

## 📌 Project Overview
Kabaddi is a fast-paced contact sport where player evaluation and tactical decisions are largely based on manual video analysis and subjective judgment. This project aims to develop a **vision-based analytics system** that extracts meaningful raid-level and player-level performance metrics from **single-camera Kabaddi match videos**.

The system focuses on **movement-based and spatio-temporal analysis** rather than referee-level decision making. It is designed as a research-oriented prototype to support **player ranking, performance profiling, and team formation insights**.

---

## 🎯 Objectives
- Detect and track Kabaddi players from match videos
- Identify raids using court-aware logic
- Extract spatio-temporal raid metrics
- Profile raiders and defenders based on performance indicators
- Rank players using analytically derived features

---

## 🧠 Key Features
- Single-camera video input (fixed, stable view)
- Player detection using YOLOv8
- Multi-object tracking with persistent IDs
- Court-aware raid segmentation
- Raid metrics extraction:
  - Raid duration
  - Penetration depth
  - Defender engagement count
  - Reaction time (approximate)
- Player performance profiling
- Player ranking logic based on extracted metrics

---

## 🏗️ Project Structure
kabaddi_analytics/
│
├── analytics/
│ ├── metrics.py # Metric computation logic
│ ├── profiling.py # Player profile construction
│ └── ranking.py # Player ranking algorithms
│
├── court/
│ ├── court_config.json
│ └── define_court.py
│
├── data/
│ └── videos/ # (Ignored in git)
│
├── detect_players.py # Player detection script
├── track_players.py # Player tracking script
├── test_analytics.py # Dummy data testing for analytics
├── main.py # Entry point (to be expanded)
├── README.md
└── .gitignore


---

## 🛠️ Technologies Used
- **Python 3.10**
- **OpenCV** – video processing and visualization
- **YOLOv8 (Ultralytics)** – player detection
- **ByteTrack** – multi-object tracking
- **NumPy** – numerical computations

---

## 📊 Analytics Philosophy
This project does **not** aim for perfect touch detection or referee-grade decisions.  
Instead, it focuses on:
- Robust movement analysis
- Temporal consistency
- Interpretable metrics
- Practical usefulness for performance evaluation

All results are **approximate but meaningful**, suitable for research and analytics use cases.

---

## 🚧 Current Status
- ✅ Player detection implemented
- ✅ Baseline player tracking implemented
- ✅ Analytics and ranking logic implemented using dummy data
- ⏳ Court geometry and raid segmentation (pending stable video input)
- ⏳ Metric extraction from real match videos
- ⏳ Player ranking and evaluation on real data

---

## 🔮 Future Work
- Integration with stabilized half-court match videos
- Court geometry mapping and midline detection
- Automated raid segmentation
- Visualization dashboard for analytics
- Multi-view extension (optional)

---

## ⚠️ Limitations
- Single-camera assumption
- Approximate interaction detection
- Tracking identity switches may occur during heavy occlusion
- Not intended for official refereeing or scoring

---

## 👤 Author
**Prakash**

Final Year Project – Computer Vision & Sports Analytics

---

## 📜 License
This project is for academic and research purposes.
