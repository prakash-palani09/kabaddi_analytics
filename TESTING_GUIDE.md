# Testing Guide — Kabaddi Analytics System

## ✅ Current System State

All core features are implemented and working. This guide covers how to test each component end-to-end.

---

## 🧪 Step 1 — Verify Court Calibration

```bash
python scripts/test_penetration.py data/videos/your_video.mp4
```

**Expected output:**
```
Midline center:  0.00m ✓
Baulk line at:  ~3.75m ✓
Bonus line at:  ~4.75m ✓
End line at:     6.50m ✓
```

If values are wrong, re-run court setup:
```bash
python court/setup_play_area.py data/videos/your_video.mp4
```

Click 13 points in order: play box corners (1–5) → midline (6–7) → baulk (8–9) → bonus (10–11) → end line (12–13). Press **ENTER** to save.

---

## 🧪 Step 2 — Process a Video

```bash
python scripts/data_extract.py data/videos/your_video.mp4
```

**Watch the console for these messages in order:**

| Message | Meaning |
|---|---|
| `✓ Model: YOLOv8m-pose` | Model loaded correctly |
| `✓ Video loaded: N frames @ X FPS` | Video opened |
| `✓ Court setup: ...` | Court geometry loaded, pixel ratios printed |
| `✓ Player X baseline established: side=Y` | Player's home side locked |
| `🎯 Raid detected! Player X crossed midline` | Raid start confirmed (6/7 frame window) |
| `🏃 Raid started - Raider X LOCKED at frame N` | Raider ID locked, no switching |
| `⚡ Raider X reappeared` | Same ID recovered after brief disappearance |
| `🔙 Raider returned to baseline, ending raid (SUCCESS)` | Raid ended successfully (4/5 frame window) |
| `❌ Raider lost, ending raid` | Raider ID missing for 120 frames — raid ended |
| `✅ Raid ended — Duration: X.XXs, Max Penetration: X.XXm` | Final metrics printed |

**Watch the video window for:**

| Colour | Meaning |
|---|---|
| Yellow polygon | Play box boundary |
| Cyan line | Midline |
| Red line | Baulk line |
| Green line | Bonus line |
| Magenta line | End line |
| Green box + `RAIDER (ID:X) LOCKED` | Active raider being tracked |
| Magenta dots on raider | Raider keypoints |
| Cyan dots on defenders | Defender keypoints |
| Gray box + `OUT` | Player outside play box, ignored |
| Orange circle + `SEARCHING N` | Raider missing, waiting for same ID to reappear |

Press **q** to stop processing early.

---

## 🧪 Step 3 — Check CSV Output

```bash
python scripts/view_metrics.py data/extracted/your_video_raid_metrics.csv
```

**Verify these columns:**

| Column | Expected Range | Notes |
|---|---|---|
| `max_penetration` | 1.0 – 6.5m | Realistic raid depth |
| `crossed_baulk` | True/False | True for most raids |
| `crossed_bonus` | True/False | True for deep raids |
| `success` | 0 or 1 | 1 = raider returned to baseline |
| `duration` | 2 – 15 sec | Typical raid duration |
| `avg_speed` | 1 – 5 m/s | Realistic movement speed |

---

## 🧪 Step 4 — Launch Dashboard and Add Data

```bash
python src/ui/kabaddi_ui_clean.py
```

**Steps:**
1. Go to **Video Processing** tab
2. Click **Select Video File** → choose your video
3. Click **Setup Court Lines** → interactive window opens, click 13 points, press ENTER
4. Click **Process Video** → processing runs, log appears in status box
5. When complete, a dialog appears — enter Match ID, Player ID, Team Name, points, success values
6. Click **Add to Rankings**
7. Go to **Player Rankings** tab — verify the player appears with realistic stats
8. Double-click any player row → Player Dashboard opens with radar chart
9. Go to **Analytics** tab — verify bar charts update
10. Go to **Teams** tab — click a team button → filtered player table appears

**To add data manually (without video):**
- In the **Player Rankings** tab, use the form at the top
- Fill in: Match ID, Player ID, Duration, Penetration, Success (1/0), Raid Points
- Click **Add Data**

**To delete a player:**
- In the **Player Rankings** tab, enter the Player ID in the Delete field
- Click **Delete Player** → confirm the dialog

---

## 🧪 Step 5 — Run Evaluation

```bash
# On synthetic data
python evaluate_metrics.py

# On real extracted data
python evaluate_metrics.py --csv data/extracted/your_video_raid_metrics.csv
```

Expected output: 6 tables covering Precision, Recall, F1, Accuracy, MAE, RMSE, Spearman ρ.

---

## 🧪 Step 6 — Generate Evaluation Graphs

```bash
python evaluation_graphs.py
```

Check `evaluation_plots/` folder — 8 PNG files should be created.

---

## 🐛 Troubleshooting

### Penetration values are too low (< 1m)
- Court setup is wrong — re-run `setup_play_area.py`
- Make sure end line (points 12–13) is clicked at the actual far end line, not the bonus line
- Run `test_penetration.py` to verify the pixel-to-meter ratio

### No raid detected
- Baseline establishment needs 15 frames with 11/15 on same side — make sure players are visible early
- Raid trigger needs 6 of last 7 frames on opponent side — slow crossings may not trigger
- Check that the raider is inside the play box (not filtered as `OUT`)

### Raider ID keeps switching
- This should not happen — raider ID is locked at raid start
- If a different player is being detected as raider, it means baseline was not established correctly
- Ensure the video starts with players on their correct sides for at least 15 frames

### Raid ends too early
- Raider disappears for more than 120 frames → raid times out
- Check for heavy occlusion or raider leaving the play box area
- The system only waits for the exact same tracker ID to reappear — it does not switch to another ID

### Config not found error
```
ValueError: No config for: your_video.mp4
```
- Run `python court/setup_play_area.py data/videos/your_video.mp4` first
- Config is keyed by full video path — if you moved the video file, re-run setup

### UI shows no data
- Synthetic data loads from `data/synthetic/synthetic_data.csv`
- If missing, the UI auto-generates sample data on first run
- Check console output for `LOADING DATA FROM:` path

### Keyframe viewer shows no frames
- Keyframes are saved to `data/keyframes/` relative to where the script is run from
- When launched via UI: `src/ui/data/keyframes/`
- When run directly: `data/keyframes/` from project root
- Click **View Live Process** in the Video Processing tab to open the viewer

---

## 📊 Expected Metric Ranges

| Metric | Typical Range | Notes |
|---|---|---|
| Max Penetration | 2.0 – 6.0m | Depends on raid aggressiveness |
| Raid Duration | 3 – 12 sec | Short raids = quick touch attempts |
| Success Rate | 50 – 75% | Varies by player skill |
| Avg Speed | 1.5 – 4.0 m/s | Court-calibrated |
| Direction Changes | 2 – 8 per raid | Agility indicator |
| Ranking Score | 0.2 – 0.7 | Weighted composite |

---

**Status:** ✅ All features implemented and working
