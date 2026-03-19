# Vision-Based Raid Analysis and Player Performance Profiling in Kabaddi

## 📌 Project Overview
Kabaddi is a fast-paced contact sport where player evaluation and tactical decisions are largely based on manual video analysis and subjective judgment. This project develops a **vision-based analytics system** that extracts meaningful raid-level and player-level performance metrics from **single-camera Kabaddi match videos**.

The system focuses on **movement-based and spatio-temporal analysis** rather than referee-level decision making. It is designed as a research-oriented prototype to support **player ranking, performance profiling, and team formation insights**.

---

## 🎯 Objectives
- Detect and track Kabaddi players from match videos using YOLOv8-Pose
- Identify raids automatically using court-aware logic and midline crossing detection
- Extract comprehensive spatio-temporal raid metrics (duration, penetration depth, engagement)
- Profile raiders based on performance indicators across multiple matches
- Rank players using analytically derived features and weighted scoring

---

## 🧠 Key Features

### Core Capabilities
- **Single-camera video input** (fixed, stable view)
- **YOLOv8-Pose detection** with multi-scale tracking for far players
- **BotSort tracking** with persistent player IDs and occlusion handling
- **Court geometry mapping** using pentagon play area with 4 parallel lines
- **Automatic raid detection** via baseline establishment and midline crossing
- **Raider recovery system** to handle temporary occlusions

### Extracted Metrics
- **Raid Duration** (seconds)
- **Penetration Depth** (meters) - calculated using perpendicular distance to midline
- **Line Crossings** - Baulk Line (3.75m), Bonus Line (4.75m), End Line (6.5m)
- **Defender Engagement Count** - unique defenders within proximity threshold
- **Reaction Time** - time until first defender engagement
- **Movement Analysis** - speed, direction changes, agility indicators
- **Success Detection** - raider return to baseline

### Analytics & Visualization
- Player performance profiling with success rates and averages
- Weighted player ranking system
- Interactive UI dashboard with player tables and keyframe viewer
- CSV export for further analysis

---

## 🏗️ Project Structure

```
kabaddi_analytics/
│
├── analytics/
│   ├── metrics.py              # Core metric computation functions
│   ├── profiling.py            # Player profile construction
│   ├── ranking.py              # Player ranking algorithms
│   ├── raid_extractor.py       # Raid metrics extraction engine
│   └── player_profile.py       # Player profile management system
│
├── court/
│   ├── setup_play_area.py      # Interactive court setup tool
│   └── simplified_court.py     # Court dynamics and geometry calculations
│
├── config/
│   └── play_area.json          # Saved court configurations per video
│
├── data/
│   ├── videos/                 # Input match videos (gitignored)
│   ├── extracted/              # Extracted raid metrics (CSV)
│   └── synthetic/              # Synthetic test data
│
├── docs/
│   ├── FORMULAS.md             # Mathematical formulas and calculations
│   ├── METRICS_EXTRACTION.md   # Detailed metrics documentation
│   └── architecture.png        # System architecture diagram
│
├── models/
│   ├── yolov8n.pt              # YOLOv8 nano model
│   └── yolov8n-pose.pt         # YOLOv8 pose estimation model
│
├── scripts/
│   ├── data_extract.py         # Main data extraction pipeline
│   ├── generate_synthetic_data.py  # Synthetic data generator
│   ├── view_metrics.py         # Metrics visualization tool
│   └── data/keyframes/         # Saved raid keyframes
│
├── src/
│   └── ui/
│       ├── kabaddi_ui_clean.py # Main UI application
│       ├── player_dashboard.py # Player statistics dashboard
│       ├── player_table.py     # Player ranking table
│       └── keyframe_viewer.py  # Raid keyframe viewer
│
├── requirements.txt            # Python dependencies
├── ui_requirements.txt         # UI-specific dependencies
├── MODEL_SCORES.md             # Model performance benchmarks
├── README.md
└── .gitignore
```


---

## 🛠️ Technologies & Dependencies

### Core Technologies
- **Python 3.10+**
- **OpenCV (cv2)** – video processing, visualization, and frame manipulation
- **YOLOv8-Pose (Ultralytics)** – player detection with pose estimation
- **BotSort Tracker** – multi-object tracking with persistent IDs
- **NumPy** – numerical computations and geometry calculations
- **Pandas** – data manipulation and CSV handling

### UI Framework
- **Tkinter** – native Python GUI framework
- **PIL (Pillow)** – image processing for UI

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/kabaddi_analytics.git
cd kabaddi_analytics

# Create virtual environment
python -m venv kabaddi_env

# Activate virtual environment
# Windows:
kabaddi_env\Scripts\activate
# Linux/Mac:
source kabaddi_env/bin/activate

# Install dependencies
pip install -r requirements.txt

# For UI components
pip install -r ui_requirements.txt
```

---

## 🚀 Quick Start Guide

### Step 1: Setup Court Geometry

Before extracting data, you need to define the court boundaries for your video:

```bash
python court/setup_play_area.py data/videos/your_video.mp4
```

**Instructions:**
1. Click **5 corners** of the play box (pentagon shape, clockwise)
2. Click **2 points** for the midline (left to right)
3. Click **2 points** for the baulk line (3.75m from midline)
4. Click **2 points** for the bonus line (4.75m from midline)
5. Click **2 points** for the end line (6.5m from midline)
6. Press **ENTER** to save, **ESC** to cancel

Configuration is saved to `config/play_area.json`

### Step 2: Extract Raid Data

Run the data extraction pipeline:

```bash
python scripts/data_extract.py data/videos/your_video.mp4
```

**What it does:**
- Detects and tracks all players using YOLOv8-Pose
- Establishes baseline sides for each player
- Automatically detects raid start (midline crossing)
- Tracks raider movement and calculates penetration depth
- Identifies defender engagements
- Detects raid end (return to baseline or timeout)
- Saves keyframes at critical moments (start, baulk, bonus, end)
- Exports metrics to CSV in `data/extracted/`

**Output:**
- `data/extracted/your_video_raid_metrics.csv` - Complete raid metrics
- `scripts/data/keyframes/` - Saved raid keyframes

### Step 3: View Metrics

```bash
python scripts/view_metrics.py data/extracted/your_video_raid_metrics.csv
```

Displays comprehensive raid statistics and individual raid breakdowns.

### Step 4: Launch UI Dashboard

```bash
python src/ui/kabaddi_ui_clean.py
```

**Features:**
- Load and analyze extracted CSV data
- View player rankings and statistics
- Browse raid keyframes
- Interactive player dashboard

---

## 📊 Analytics Philosophy

This project does **not** aim for perfect touch detection or referee-grade decisions.  
Instead, it focuses on:

- **Robust movement analysis** - Track player positions and trajectories
- **Temporal consistency** - Maintain player identities across frames
- **Interpretable metrics** - Provide meaningful, actionable insights
- **Practical usefulness** - Support coaching decisions and player evaluation

All results are **approximate but meaningful**, suitable for research and analytics use cases.

### Penetration Depth Calculation

Penetration is calculated using **perpendicular distance** from the raider's position to the midline:

```
distance = |Ax + By + C| / sqrt(A² + B²)
meters = (pixel_distance / total_court_depth) × 6.5m
```

Where the court depth is normalized to the official end line distance (6.5m from midline).

### Player Ranking Formula

Players are ranked using a weighted scoring system:

```
Score = 0.30 × success_rate 
      + 0.25 × normalized_points
      + 0.25 × normalized_penetration
      - 0.20 × duration_penalty
```

---

## ✅ Current Status

### Completed Features
- ✅ **YOLOv8-Pose player detection** with multi-scale tracking
- ✅ **BotSort tracking** with persistent IDs and occlusion handling
- ✅ **Interactive court setup tool** for geometry mapping
- ✅ **Simplified court dynamics** with perpendicular distance calculations
- ✅ **Automatic raid detection** via baseline establishment
- ✅ **Raider recovery system** for handling occlusions
- ✅ **Comprehensive metrics extraction** (duration, penetration, engagement)
- ✅ **Line crossing detection** (baulk, bonus, end lines)
- ✅ **Keyframe capture** at critical raid moments
- ✅ **Player profiling system** with statistics aggregation
- ✅ **Weighted ranking algorithm** for player evaluation
- ✅ **CSV export** for extracted metrics
- ✅ **Interactive UI dashboard** with player tables and keyframe viewer
- ✅ **Synthetic data generator** for testing

### In Progress
- 🔄 **Multi-match aggregation** - Combine data across multiple videos
- 🔄 **Advanced visualization** - Heatmaps and trajectory plots
- 🔄 **Team-level analytics** - Team performance metrics

---

## 🔮 Future Enhancements

### Short-term Goals
- **Defender profiling** - Track defensive actions and tackle success rates
- **Touch detection** - Approximate touch events using proximity and pose
- **Point calculation** - Estimate raid points based on touches and returns
- **Video stabilization** - Handle camera shake and movement
- **Batch processing** - Process multiple videos automatically

### Long-term Vision
- **Real-time analysis** - Live match analytics
- **Multi-camera fusion** - Combine multiple viewpoints
- **Deep learning classification** - Classify raid types and defensive strategies
- **Web dashboard** - Cloud-based analytics platform
- **Mobile app** - On-field coaching tool

---

## ⚠️ Limitations & Known Issues

### Technical Constraints
- **Single-camera assumption** - Requires fixed, stable camera view
- **Approximate interaction detection** - Touch detection is proximity-based
- **Tracking identity switches** - May occur during heavy occlusion or player overlap
- **Court setup required** - Manual geometry mapping needed per video
- **Lighting sensitivity** - Performance degrades in poor lighting conditions

### Scope Limitations
- **Not for official refereeing** - Results are analytical, not authoritative
- **No referee decisions** - Does not judge out/safe or point awards
- **Approximate metrics** - All measurements are estimates for analysis purposes

### Performance Notes
- Processing speed: ~15-20 FPS on CPU, ~30-40 FPS on GPU
- Best results with: 1080p video, good lighting, minimal camera movement
- Raider recovery timeout: 4 seconds (120 frames @ 30 FPS)

---

## 📝 Citation

If you use this project in your research, please cite:

```bibtex
@misc{kabaddi_analytics_2024,
  author = {Prakash},
  title = {Vision-Based Raid Analysis and Player Performance Profiling in Kabaddi},
  year = {2024},
  publisher = {GitHub},
  journal = {GitHub repository},
  howpublished = {\url{https://github.com/yourusername/kabaddi_analytics}}
}
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

### Areas for Contribution
- Improved tracking algorithms
- Better touch detection methods
- Additional metrics and analytics
- UI/UX improvements
- Documentation and tutorials

---

## 👤 Author

**Prakash**  
Final Year Project – Computer Vision & Sports Analytics

---

## 📜 License

This project is for **academic and research purposes only**.  
Not intended for commercial use or official match analysis.

---

## 📧 Contact

For questions, suggestions, or collaboration opportunities, please open an issue on GitHub.

---

**⭐ If you find this project useful, please consider giving it a star!**
