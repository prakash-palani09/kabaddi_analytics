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
- **YOLOv8m-Pose** — detects players with 17-point body keypoints per frame at 1280px resolution (conf=0.25, iou=0.3)
- **BotSort tracker** — maintains persistent player IDs using Kalman filter + Re-ID
- **Torso-based centering** — uses shoulder and hip keypoints (indices 5, 6, 11, 12) for stable player center
- **Far-player adaptive smoothing** — alpha=0.5 for small/distant players, alpha=0.7 for normal players
- **Play-box filtering** — players outside the court polygon are ignored entirely (gray box drawn, skipped)
- **Raider ID lock** — once a raider is identified, only that exact ID is tracked for the entire raid
- **One raid per video** — system only detects a new raid if no raid has been recorded yet

### Court Geometry
- **Interactive court setup** — click 13 points to define play box, midline, baulk, bonus, and end lines
- **Perpendicular distance formula** — calculates penetration depth in meters using `|Ax + By + C| / √(A² + B²)`
- **End line center reference** — uses midpoint of both end line endpoints as the reference for pixel-to-meter ratio
- **Ray casting** — determines if a player is inside the court polygon
- **Actual line depth measurement** — baulk and bonus line depths are measured from calibration, not assumed fixed
- **Inside-court keypoint filtering** — only keypoints confirmed inside the play box contribute to penetration

### Raid Detection & Metrics
- **Baseline establishment** — first 15 frames used, requires 11/15 consensus to lock a player's baseline side
- **Raid start detection** — sliding window: 6 of last 7 frames on opponent side triggers raid
- **Raid end detection** — sliding window: 4 of last 5 frames back on baseline side ends raid (success)
- **Raider recovery** — if raider disappears, system waits for the exact same ID to reappear for up to 120 frames before ending the raid
- **Lost player cleanup** — players not seen for 90 frames are removed from tracking
- **Penetration depth** — perpendicular distance from midline, measured in meters, clamped to [0, 6.5m]
- **Line crossing detection** — baulk and bonus crossings flagged when penetration depth ≥ measured line depth
- **Raid success** — detected when raider returns to their baseline (4/5 frame consensus)
- **Direction changes** — counts movement reversals using dot product sign test (dot < 0)
- **Keyframe capture** — saves JPEGs at raid start, baulk crossing, bonus crossing, end, and lost events

### Player Profiling & Ranking
- **Player profiles** — aggregates all raid metrics per player across matches
- **Weighted ranking score:**
  ```
  Score = 0.30 × success_rate
        + 0.25 × (avg_penetration / 5.0)
        + 0.25 × (avg_points / 3.0)
        - 0.20 × (avg_duration / 10.0)
  ```
- **Recent form** — ranking uses last 15 matches for scoring, all-time stats for display
- **Team management** — players grouped by team, team names saved to profiles
- **Auto team detection** — team name inferred from player ID prefix (e.g. `TeamA_P1` → `TeamA`)

### Dashboard (UI)
- **4-tab layout** — Video Processing, Player Rankings, Analytics, Teams
- **Player Rankings tab** — sortable table, double-click row opens player dashboard; includes Add/Delete player data form
- **Analytics tab** — 4 bar charts (scores, success rate, penetration, total points) for top 10 players
- **Player Dashboard** — stat cards + performance radar chart (Efficiency, Aggression, Impact, Control, Consistency)
- **Keyframe Viewer** — navigate raid events (Start → Baulk → Bonus → End) with jump-to-raid support
- **Teams tab** — team buttons with filtered player rankings table

### Evaluation
- **`evaluate_metrics.py`** — standalone evaluation script, outputs 6 tables (Precision, Recall, F1, MAE, RMSE, Spearman ρ)
- **`evaluation_graphs.py`** — generates 8 evaluation PNG plots saved to `evaluation_plots/`

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
│   └── simplified_court.py     # Court geometry — perpendicular distance, line crossing, ray casting
│
├── config/
│   └── play_area.json          # Saved court configurations keyed by video path
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
│   ├── yolov8m-pose.pt         # YOLOv8 medium pose model (primary, ~51MB, auto-downloaded)
│   └── yolov8n-pose.pt         # YOLOv8 nano pose model (baseline)
│
├── scripts/
│   ├── data_extract.py         # Main video processing pipeline (DataExtractor class)
│   ├── generate_synthetic_data.py  # Synthetic data generator
│   ├── test_penetration.py     # Penetration calculation verification tool
│   ├── view_metrics.py         # CLI metrics viewer
│   └── data/keyframes/         # Saved raid keyframe JPEGs (when run directly)
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
├── evaluation_graphs.py        # Generates 8 evaluation PNG plots → evaluation_plots/
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
| SciPy | Spearman correlation for evaluation metrics |

### Algorithms

| Algorithm | Where Used | Purpose |
|---|---|---|
| Kalman Filter | BotSort (internal) | Predict player position between frames |
| Hungarian Algorithm | BotSort (internal) | Match detections to existing tracks |
| CNN (YOLOv8m) | Ultralytics (internal) | Detect players and body keypoints |
| Non-Maximum Suppression | Ultralytics (internal) | Remove duplicate detections |
| Exponential Moving Average | `data_extract.py` | Smooth player positions (alpha=0.7 near, 0.5 far) |
| Cross Product Sign Test | `data_extract.py` | Determine which court side a player is on |
| Sliding Window Majority Vote | `data_extract.py` | Raid start (6/7 frames) and end (4/5 frames) detection |
| Mode Detection | `data_extract.py` | Establish each player's baseline side (11/15 consensus) |
| Ray Casting | `simplified_court.py` | Point-in-polygon test for court boundary |
| Perpendicular Distance | `simplified_court.py` | Penetration depth in meters via `\|Ax+By+C\|/√(A²+B²)` |
| Vector Projection (Dot Product) | `simplified_court.py` | Measure actual baulk/bonus line depths from midline |
| Dot Product Sign Test | `simplified_court.py` | Direction change detection (dot < 0 = reversal) |
| Min-Max Normalization | `ranking.py` | Normalize metrics for scoring |
| Weighted Linear Scoring | `ranking.py` | Multi-criteria player ranking |
| Euclidean Distance | `raid_extractor.py` | Defender proximity detection |
| Statistical Aggregation | `profiling.py` | Build player profiles (mean, sum) |

---

## 📦 Installation

### Requirements
- Python 3.10 or 3.11 (recommended)
- Windows / Linux / macOS
- GPU optional (CUDA 11.8+ for faster processing)

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

# Install all dependencies (single command)
pip install -r requirements.txt
```

**What gets installed:**

| Package | Version | Purpose |
|---|---|---|
| opencv-python | >=4.8.0 | Video reading, frame processing, visualization |
| ultralytics | >=8.0.0 | YOLOv8m-Pose detection + BotSort tracker |
| torch | >=2.0.0 | Deep learning backend for YOLO |
| torchvision | >=0.15.0 | Required by torch/ultralytics |
| numpy | >=1.24.0 | Geometry calculations, array operations |
| scipy | >=1.10.0 | Spearman correlation for evaluation |
| matplotlib | >=3.7.0 | Analytics charts, radar chart, evaluation graphs |
| Pillow | >=9.0.0 | Keyframe image display in UI |

> **Tkinter** is built into Python — no separate install needed.

> **BotSort** tracker is bundled inside `ultralytics` — no separate install needed.

> The YOLOv8m-pose model (~51MB) is downloaded automatically on first run and saved to `models/yolov8m-pose.pt`.

### GPU Setup (Optional but recommended)
For ~3x faster processing, install the CUDA version of PyTorch **before** running `pip install -r requirements.txt`:
```bash
# CUDA 11.8
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# CUDA 12.1
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# Then install the rest
pip install -r requirements.txt
```

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
| 8 – 9 | Baulk line (left to right) | ~3.75m |
| 10 – 11 | Bonus line (left to right) | ~4.75m |
| 12 – 13 | End line (left to right) | 6.5m |

Press **ENTER** to save, **ESC** to cancel.
Configuration saved to `config/play_area.json` keyed by the full video path.

> ⚠️ Accurate calibration is critical. A 10px error in court setup causes ~0.18m error in all penetration measurements.

---

### Step 2 — Verify Penetration Calculation (Optional)

```bash
python scripts/test_penetration.py data/videos/your_video.mp4
```

Expected output:
```
Midline center:  0.00m ✓
Baulk line at:  ~3.75m ✓
Bonus line at:  ~4.75m ✓
End line at:     6.50m ✓
```

---

### Step 3 — Extract Raid Data

```bash
python scripts/data_extract.py data/videos/your_video.mp4
```

**What happens internally:**
1. YOLOv8m-Pose detects all players every frame at 1280px (conf=0.25, iou=0.3, max_det=50)
2. BotSort assigns and maintains tracker IDs
3. Players outside the play box polygon are filtered out and skipped
4. Player center computed from torso keypoints (shoulders + hips); falls back to bounding box center
5. Position smoothed with EMA (alpha=0.7 normal, 0.5 for far/small players)
6. Each player's baseline side established from first 15 frames (needs 11/15 consensus)
7. Raid detected when a player has 6 of last 7 frames on the opponent side
8. Raider ID is locked — no switching to other players for entire raid duration
9. Penetration depth computed per frame using perpendicular distance formula, only inside-court keypoints used
10. Baulk and bonus crossings flagged when penetration ≥ measured line depth
11. Raid ends when raider has 4 of last 5 frames back on baseline (success), or raider ID missing for 120 frames (lost)
12. Players not seen for 90 frames are removed from tracking
13. Keyframes saved at start, baulk, bonus, end, and lost events
14. All metrics exported to CSV

**Output:**
- `data/extracted/{video_name}_raid_metrics.csv` — complete raid metrics
- `data/keyframes/` — raid event keyframe JPEGs

**On-screen display during processing:**
| Colour | Meaning |
|---|---|
| Yellow polygon | Play box boundary |
| Cyan line | Midline |
| Red line | Baulk line |
| Green line | Bonus line |
| Magenta line | End line |
| Green box + `RAIDER (ID:X) LOCKED` | Active raider |
| Magenta dots | Raider keypoints |
| Cyan dots | Defender keypoints |
| Gray box + `OUT` | Player outside play box |
| Orange circle + `SEARCHING N` | Raider missing, waiting for same ID |

**Console messages:**
| Message | Meaning |
|---|---|
| `✓ Player X baseline established` | Baseline side locked for player |
| `🎯 Raid detected!` | Midline crossing confirmed |
| `🏃 Raid started - Raider X LOCKED` | Raider ID locked |
| `⚡ Raider X reappeared` | Same ID recovered after disappearance |
| `🔙 Raider returned to baseline` | Successful raid completion |
| `❌ Raider lost, ending raid` | 120-frame timeout reached |

---

### Step 4 — Launch Dashboard

```bash
python src/ui/kabaddi_ui_clean.py
```

**Dashboard tabs:**

| Tab | Purpose |
|---|---|
| Video Processing | Select video, run court setup and extraction, view processing log |
| Player Rankings | Sortable rankings table — double-click row for player dashboard; Add/Delete player data form at top |
| Analytics | Bar charts for top 10 players across 4 metrics |
| Teams | Click a team button to view filtered player rankings |

**Adding extracted data to rankings:**
1. After video processing completes, a dialog appears automatically
2. Enter Match ID, Player ID, Team Name, raid points, and success values
3. Click **Add to Rankings** — data is saved and rankings update immediately
4. Or manually add a single raid via the form at the top of the Player Rankings tab

---

### Step 5 — Run Evaluation Metrics

```bash
# Evaluate on synthetic data (default)
python evaluate_metrics.py

# Evaluate on extracted real data
python evaluate_metrics.py --csv data/extracted/your_video_raid_metrics.csv
```

Outputs 6 evaluation tables: dataset statistics, raid success classification, line crossing classification, penetration depth regression, player ranking correlation, and summary.

---

### Step 6 — Generate Evaluation Graphs

```bash
python evaluation_graphs.py
```

Saves 8 PNG plots to `evaluation_plots/`:

| File | Graph |
|---|---|
| `1_raid_detection_metrics.png` | Precision / Recall / F1 / Accuracy bar chart |
| `2_penetration_scatter.png` | Predicted vs Ground Truth scatter with MAE/RMSE |
| `3_confusion_matrix.png` | Line crossing confusion matrix |
| `4_ranking_correlation.png` | Spearman ρ rank scatter |
| `5_system_radar.png` | Component-wise radar chart |
| `6_processing_speed.png` | CPU vs GPU FPS grouped bar |
| `7_raid_outcome_distribution.png` | Raid outcome pie chart |
| `8_summary_dashboard.png` | All panels in one figure |

---

## 📊 Key Formulas

### Penetration Depth
```
Midline equation:  Ax + By + C = 0
                   A = y2 - y1,  B = x1 - x2,  C = x2*y1 - x1*y2

Pixel distance:    d = |Ax + By + C| / √(A² + B²)

Reference depth:   total_px = |A*ex + B*ey + C| / √(A² + B²)
                   where (ex, ey) = center of end line endpoints

Meters:            depth = (d / total_px) × 6.5
Clamped to:        [0.0, 6.5] meters
```

### Raid Duration
```
duration (seconds) = (end_frame - start_frame) / FPS
```

### Average Speed
```
total_distance_px = Σ √((x₂-x₁)² + (y₂-y₁)²)  for consecutive positions
px_per_meter      = total_pixel_depth / 6.5
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
| Config keyed by full video path | Moving the video file requires re-running court setup |
| No touch detection | Raid success based on return to baseline only |
| Proximity-based engagement | Not actual physical contact detection |
| ID switches during heavy occlusion | Rare but possible in pile-ups |
| CPU processing is slow | Real-time requires GPU |
| One raid per video | Multi-raid videos need separate runs |
| Lighting sensitivity | Performance degrades in poor lighting |

---

## ✅ Completed Features

- ✅ YOLOv8m-Pose player detection with 17 keypoints at 1280px
- ✅ BotSort tracking with persistent IDs and Kalman filter
- ✅ Play-box filtering — outside-court players ignored
- ✅ Torso-based player centering (shoulders + hips keypoints)
- ✅ Adaptive EMA position smoothing (near vs far players)
- ✅ Interactive 13-point court calibration
- ✅ Perpendicular distance penetration formula with end line center reference
- ✅ Inside-court keypoint filtering for accurate penetration
- ✅ Automatic raid detection — 6/7 frame sliding window
- ✅ Strict raider ID lock — no switching to defenders mid-raid
- ✅ Single-raid-per-video guard
- ✅ Penetration depth clamped to [0–6.5m]
- ✅ Baulk and bonus line crossing via measured line depth
- ✅ Raid success detection — 4/5 frame baseline return consensus
- ✅ Raider recovery — waits 120 frames for same ID before ending raid
- ✅ Lost player cleanup after 90 frames
- ✅ Direction change counting via dot product sign test
- ✅ Keyframe capture at start, baulk, bonus, end, and lost events
- ✅ Player profiling with all-time and recent-form stats
- ✅ Weighted multi-criteria player ranking
- ✅ Team management with profile persistence and auto-detection
- ✅ 4-tab interactive desktop dashboard
- ✅ Sortable rankings table with double-click player dashboard
- ✅ Radar chart performance visualization (5 dimensions)
- ✅ Analytics bar charts for top 10 players
- ✅ Keyframe viewer with event navigation and jump-to-raid
- ✅ Evaluation metrics calculator (F1, MAE, RMSE, Spearman ρ)
- ✅ Evaluation graphs generator (8 PNG plots)
- ✅ Synthetic data generator (28 players, 4 teams, 12 matches)
- ✅ Penetration verification tool (`test_penetration.py`)

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
