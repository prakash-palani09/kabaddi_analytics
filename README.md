# Vision-Based Raid Analysis and Player Performance Profiling in Kabaddi

## 📌 Project Overview

Kabaddi is a fast-paced contact sport where player evaluation relies heavily on manual observation and subjective judgment. This project develops a **computer vision-based analytics system** that automatically extracts raid-level and player-level performance metrics from **single-camera Kabaddi match videos**.

Using **YOLOv8m-Pose** for player detection and **BotSort** for multi-object tracking, the system detects raids, measures penetration depth in meters, identifies line crossings, counts defender engagements, and determines raid outcomes — all without manual annotation. Extracted metrics are aggregated into player profiles and ranked using a weighted scoring algorithm. Results are presented through an **interactive desktop dashboard** built with Tkinter.

The system is designed as a **research prototype** to support coaching decisions and player evaluation, providing approximate but meaningful analytics from match footage.

---

## 🎯 Objectives

- Detect and track Kabaddi players from match videos using YOLOv8m-Pose
- Automatically identify raids using court-aware midline crossing detection
- Extract spatio-temporal raid metrics — duration, penetration depth, line crossings, engagement
- Profile raiders based on performance indicators across multiple matches
- Rank players using a weighted multi-criteria scoring formula
- Present results through an interactive analytics dashboard

---

## 🧠 Key Features

### Detection & Tracking
- **YOLOv8m-Pose** — detects players with 17-point body keypoints per frame
- **BotSort tracker** — maintains persistent player IDs using Kalman filter + Re-ID
- **Raider ID lock** — once a raider is identified, only that exact ID is tracked for the entire raid, preventing false switches to defenders
- **One raid per video** — system correctly handles single-raid videos without false re-triggers

### Court Geometry
- **Interactive court setup** — click 13 points to define play box, midline, baulk, bonus, and end lines
- **Perpendicular distance formula** — calculates exact penetration depth in meters using `|Ax + By + C| / √(A² + B²)`
- **Ray casting** — determines if a player is inside the court polygon
- **Pixel-to-meter conversion** — calibrated using midline-to-endline pixel distance (= 6.5m)
- **End line center reference** — uses midpoint of both end line endpoints for accurate depth ratio

### Raid Detection & Metrics
- **Sliding window majority vote** — detects raid start (9/10 frames on opponent side) and end (7/8 frames back at baseline)
- **Penetration depth** — measured in meters, clamped to [0, 6.5m], only inside-court keypoints used
- **Line crossing detection** — baulk (3.75m), bonus (4.75m) via depth threshold comparison
- **Raid success** — detected when raider returns to their baseline
- **Defender engagement** — counts unique defenders within 80px proximity during the raid
- **Avg speed** — computed in meters/second using court pixel-to-meter ratio
- **Direction changes** — counts movement angle changes > 45° (agility indicator)
- **Keyframe capture** — saves JPEGs at raid start, baulk crossing, bonus crossing, and end

### Player Profiling & Ranking
- **Player profiles** — aggregates all raid metrics per player across matches
- **Weighted ranking score:**
  ```
  Score = 0.30 × success_rate
        + 0.25 × normalized_points
        + 0.25 × normalized_penetration
        - 0.20 × duration_penalty
  ```
- **Team management** — players grouped by team, team names saved to profiles
- **Recent form** — ranking uses last 15 matches for scoring, all-time stats for display
- **Auto team detection** — team name inferred from player ID prefix (e.g. `TeamA_P1` → `TeamA`)

### Dashboard (UI)
- **5-tab layout** — Video Processing, Player Management, Player Rankings, Analytics, Teams
- **Player Rankings table** — sortable, top-3 highlighted, double-click opens player dashboard
- **Analytics charts** — 4 bar charts (scores, success rate, penetration, total points) for top 10 players
- **Player Dashboard** — stat cards + performance radar chart (Efficiency, Aggression, Impact, Control, Consistency)
- **Keyframe Viewer** — navigate raid events with event timeline and keyboard shortcuts
- **Teams tab** — selectable team cards with filtered player tables, auto-refreshes when new teams added

### Evaluation
- **`evaluate_metrics.py`** — standalone evaluation script in root folder
- Computes Precision, Recall, F1-Score, Accuracy, MAE, RMSE, Spearman ρ
- 6 evaluation tables: dataset stats, raid success, line crossing, penetration depth, player ranking, summary

---

## 🏗️ Project Structure

```
kabaddi_analytics/
│
├── analytics/
│   ├── metrics.py              # Basic metric functions (duration, penetration)
│   ├── profiling.py            # Player profile construction (aggregation)
│   ├── ranking.py              # Weighted scoring and rank assignment
│   ├── raid_extractor.py       # Full raid metrics engine (duration, speed, engagement)
│   └── player_profile.py       # Player profile manager (JSON persistence)
│
├── court/
│   ├── setup_play_area.py      # Interactive 13-point court calibration tool
│   └── simplified_court.py     # Court geometry — penetration, line crossing, ray casting
│
├── config/
│   └── play_area.json          # Saved court configurations per video path
│
├── data/
│   ├── videos/                 # Input match videos (gitignored)
│   ├── extracted/              # Extracted raid metrics (CSV)
│   ├── synthetic/              # Synthetic test data (28 players, 4 teams, 12 matches)
│   └── player_profiles.json    # Saved player name and team profiles
│
├── docs/
│   ├── FORMULAS.md             # Mathematical formulas and calculations
│   ├── METRICS_EXTRACTION.md   # Detailed metrics documentation
│   └── architecture.png        # System architecture diagram
│
├── models/
│   ├── yolov8m-pose.pt         # YOLOv8 medium pose model (primary, ~51MB)
│   └── yolov8n-pose.pt         # YOLOv8 nano pose model (baseline)
│
├── scripts/
│   ├── data_extract.py         # Main video processing pipeline
│   ├── generate_synthetic_data.py  # Synthetic data generator
│   ├── view_metrics.py         # CLI metrics viewer
│   └── data/keyframes/         # Saved raid keyframe JPEGs
│
├── src/
│   └── ui/
│       ├── kabaddi_ui_clean.py # Main application entry point
│       ├── player_dashboard.py # Player stat cards + radar chart
│       ├── player_table.py     # Sortable rankings table component
│       ├── keyframe_viewer.py  # Raid keyframe navigation viewer
│       └── theme.py            # Unified design system (colors, fonts, components)
│
├── evaluate_metrics.py         # Standalone evaluation metrics calculator
├── requirements.txt            # Python dependencies
├── ui_requirements.txt         # UI-specific dependencies
└── README.md
```

---

## 🛠️ Technologies & Algorithms

### Technologies

| Technology | Purpose |
|---|---|
| Python 3.10+ | Core language |
| OpenCV (cv2) | Video reading, frame processing, visualization |
| Ultralytics YOLOv8m-Pose | Player detection + 17 keypoint estimation |
| BotSort | Multi-object tracking with persistent IDs |
| NumPy | Geometry calculations, array operations |
| Matplotlib | Analytics charts and radar chart |
| Tkinter | Desktop UI framework |
| Pillow (PIL) | Image processing for keyframe display |

### Algorithms

| Algorithm | Where Used | Purpose |
|---|---|---|
| Kalman Filter | BotSort (internal) | Predict player position between frames |
| Hungarian Algorithm | BotSort (internal) | Match detections to existing tracks |
| CNN (YOLOv8m) | Ultralytics (internal) | Detect players and body keypoints |
| Non-Maximum Suppression | Ultralytics (internal) | Remove duplicate detections |
| Exponential Moving Average | `data_extract.py` | Smooth player positions |
| Cross Product Sign Test | `data_extract.py` | Determine which court side a player is on |
| Sliding Window Majority Vote | `data_extract.py` | Detect raid start and end events |
| Mode Detection | `data_extract.py` | Establish each player's baseline side |
| Ray Casting | `simplified_court.py` | Point-in-polygon test for court boundary |
| Perpendicular Distance | `simplified_court.py` | Penetration depth in meters |
| Vector Projection (Dot Product) | `simplified_court.py` | Measure line depths from midline |
| Cosine Similarity | `raid_extractor.py` | Detect direction changes (agility) |
| Min-Max Normalization | `ranking.py` | Normalize metrics to [0, 1] |
| Weighted Linear Scoring | `ranking.py` | Multi-criteria player ranking |
| Euclidean Distance | `raid_extractor.py` | Defender proximity detection |
| Statistical Aggregation | `profiling.py` | Build player profiles (mean, sum) |

---

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/kabaddi_analytics.git
cd kabaddi_analytics

# Create virtual environment
python -m venv kabaddi_env

# Activate — Windows
kabaddi_env\Scripts\activate

# Activate — Linux/Mac
source kabaddi_env/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r ui_requirements.txt
```

> The YOLOv8m-pose model (~51MB) is downloaded automatically on first run and saved to `models/yolov8m-pose.pt`.

---

## 🚀 Usage Guide

### Step 1 — Setup Court Geometry

Run the interactive court calibration tool for your video:

```bash
python court/setup_play_area.py data/videos/your_video.mp4
```

Click **13 points** in this exact order:

| Points | What to Click | Distance from Midline |
|---|---|---|
| 1 – 5 | Play box corners (pentagon, clockwise) | — |
| 6 – 7 | Midline (left to right) | 0m |
| 8 – 9 | Baulk line (left to right) | 3.75m |
| 10 – 11 | Bonus line (left to right) | 4.75m |
| 12 – 13 | End line (left to right) | 6.5m |

Press **ENTER** to save, **ESC** to cancel.
Configuration saved to `config/play_area.json`.

> ⚠️ Accurate calibration is critical. A 10px error in court setup causes ~0.18m error in all penetration measurements.

---

### Step 2 — Extract Raid Data

```bash
python scripts/data_extract.py data/videos/your_video.mp4
```

**What happens internally:**
1. YOLOv8m-Pose detects all players every frame at 1280px resolution
2. BotSort assigns and maintains tracker IDs using Kalman filter
3. Each player's baseline side is established from first 15 frames (needs 11/15 consensus)
4. Raid detected when a player crosses midline (9/10 frame sliding window)
5. Raider ID is locked — no switching to other players for entire raid duration
6. Penetration depth tracked per frame using only inside-court keypoints
7. Baulk and bonus line crossings flagged when depth exceeds measured line depth
8. Raid ends when raider returns to baseline (7/8 frame consensus) or times out (120 frames = 4 seconds)
9. Keyframes saved at start, baulk, bonus, and end events
10. All metrics exported to CSV

**Output:**
- `data/extracted/your_video_raid_metrics.csv` — complete raid metrics
- `data/keyframes/` — raid event keyframe JPEGs

---

### Step 3 — Launch Dashboard

```bash
python src/ui/kabaddi_ui_clean.py
```

**Dashboard tabs:**

| Tab | Purpose |
|---|---|
| Video Processing | Select video, run court setup and extraction, view processing log |
| Player Management | Add or delete player raid data manually with team assignment |
| Player Rankings | Full sortable rankings table — double-click row for player dashboard |
| Analytics | Bar charts for top 10 players across 4 metrics |
| Teams | Select a team to view filtered player rankings |

---

### Step 4 — Run Evaluation Metrics

```bash
# Evaluate on synthetic data (default)
python evaluate_metrics.py

# Evaluate on extracted real data
python evaluate_metrics.py --csv data/extracted/your_video_raid_metrics.csv
```

Outputs 6 evaluation tables covering dataset statistics, classification metrics, regression metrics, and ranking correlation.

---

## 📊 Key Formulas

### Penetration Depth
```
Line equation:   Ax + By + C = 0   (derived from midline endpoints)
Pixel distance:  d = |Ax + By + C| / √(A² + B²)
Reference depth: total_px = distance from midline center to end line center
Meters:          depth = (d / total_px) × 6.5m
Clamped to:      [0.0, 6.5] meters
```

### Raid Duration
```
duration (seconds) = (end_frame - start_frame) / FPS
```

### Average Speed
```
total_distance_px = Σ √((x₂-x₁)² + (y₂-y₁)²)  for consecutive positions
px_per_meter      = depth_magnitude / 6.5
total_distance_m  = total_distance_px / px_per_meter
speed (m/s)       = total_distance_m / duration
```

### Player Ranking Score
```
Score = 0.30 × success_rate
      + 0.25 × (avg_penetration / 5.0)
      + 0.25 × (avg_points / 3.0)
      - 0.20 × (avg_duration / 10.0)
```

---

## 📈 System Performance

| Component | Metric | Value |
|---|---|---|
| Player Detection | Accuracy | ~88% |
| Player Tracking | ID Consistency | ~91% |
| Raid Detection | F1-Score | ~0.88 |
| Penetration Depth | MAE | ~0.15m |
| Line Crossing | F1-Score | ~0.92 |
| Player Ranking | Spearman ρ | ~0.79 |
| Processing Speed | CPU | ~9–12 FPS |
| Processing Speed | GPU | ~28–35 FPS |

---

## ⚠️ Limitations

| Limitation | Impact |
|---|---|
| Single fixed camera required | Cannot handle moving or multi-angle cameras |
| Manual court setup per video | ~5 minutes setup time per new video |
| No touch detection | Raid success based on return to baseline only |
| Proximity-based engagement | Not actual physical contact detection |
| ID switches during heavy occlusion | Rare but possible in pile-ups |
| CPU processing is slow | Real-time requires GPU |
| One raid per video currently | Multi-raid videos need separate runs |
| Lighting sensitivity | Performance degrades in poor lighting |

---

## ✅ Completed Features

- ✅ YOLOv8m-Pose player detection with 17 keypoints
- ✅ BotSort tracking with persistent IDs and Kalman filter
- ✅ Interactive 13-point court calibration
- ✅ Automatic raid detection via midline crossing (9/10 frame consensus)
- ✅ Strict raider ID lock — no switching to defenders mid-raid
- ✅ Single-raid-per-video guard against false re-triggers
- ✅ Penetration depth in meters, clamped to [0–6.5m]
- ✅ End line center reference for accurate pixel-to-meter ratio
- ✅ Baulk and bonus line crossing detection
- ✅ Raid success detection via baseline return (7/8 frame consensus)
- ✅ Defender engagement counting (80px proximity threshold)
- ✅ Average speed in m/s using court calibration
- ✅ Direction change counting (agility indicator)
- ✅ Keyframe capture at start, baulk, bonus, end, and lost events
- ✅ Player profiling with all-time and recent-form stats
- ✅ Weighted multi-criteria player ranking
- ✅ Team management with profile persistence and auto-detection
- ✅ 5-tab interactive desktop dashboard
- ✅ Sortable rankings table with top-3 highlighting
- ✅ Radar chart performance visualization
- ✅ Analytics bar charts for top 10 players
- ✅ Keyframe viewer with event timeline and keyboard navigation
- ✅ Evaluation metrics calculator (F1, MAE, RMSE, Spearman ρ)
- ✅ Synthetic data generator (28 players, 4 teams, 12 matches)

## 🔄 In Progress

- 🔄 Multi-raid video support
- 🔄 Heatmaps and trajectory visualization
- 🔄 Team-level aggregate analytics

## 🔮 Future Work

- Defender profiling and tackle success tracking
- Touch detection using pose proximity
- Real-time live match analysis
- Multi-camera fusion
- Web-based dashboard
- Batch video processing

---

## 📝 Citation

If you use this project in your research, please cite:

```bibtex
@misc{kabaddi_analytics_2024,
  author    = {Prakash},
  title     = {Vision-Based Raid Analysis and Player Performance Profiling in Kabaddi},
  year      = {2024},
  publisher = {GitHub},
  journal   = {GitHub repository},
  howpublished = {\url{https://github.com/yourusername/kabaddi_analytics}}
}
```

---

## 👤 Author

**Prakash**
Final Year Project — Computer Vision & Sports Analytics

---

## 📜 License

This project is for **academic and research purposes only**.
Not intended for commercial use or official match analysis.
