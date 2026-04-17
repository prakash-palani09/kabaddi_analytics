# Tracking and Penetration — Implementation Notes

This document describes how tracking and penetration depth are currently implemented in the system. It reflects the actual code in `scripts/data_extract.py` and `court/simplified_court.py`.

---

## 📐 Penetration Depth Calculation

### Method: Perpendicular Distance Formula

File: `court/simplified_court.py` → `get_penetration_depth()`

```python
# Midline line equation: Ax + By + C = 0
A = y2 - y1
B = x1 - x2
C = x2 * y1 - x1 * y2

# Perpendicular distance from player point to midline
pixel_distance = |A*x + B*y + C| / sqrt(A² + B²)

# Reference: perpendicular distance from midline to END LINE CENTER
ex = (end_line[0][0] + end_line[1][0]) / 2
ey = (end_line[0][1] + end_line[1][1]) / 2
total_pixel_depth = |A*ex + B*ey + C| / sqrt(A² + B²)

# Convert to meters, clamp to [0, 6.5]
meters = (pixel_distance / total_pixel_depth) × 6.5
```

**Key design decisions:**
- Uses the **center of the end line** (average of both endpoints) as the reference point — more accurate than using a single endpoint
- Clamps result to `[0.0, 6.5]` meters hard
- Only keypoints confirmed inside the play box are used — outside-court points are ignored

### Line Crossing Detection

Baulk and bonus line depths are **measured from the calibration**, not assumed to be exactly 3.75m and 4.75m. The actual pixel positions of the clicked lines are projected onto the depth axis:

```python
# Example for baulk line
baulk_center = (baulk_line[0] + baulk_line[1]) / 2
baulk_vector = baulk_center - mid_center
baulk_projection = dot(baulk_vector, depth_direction)
baulk_depth_m = (baulk_projection / depth_magnitude) × 6.5

# Crossing check
crossed = (player_penetration_depth >= baulk_depth_m)
```

This means if the court was calibrated slightly off, the crossing thresholds adjust automatically.

---

## 🎯 Raid Detection

File: `scripts/data_extract.py`

### Baseline Establishment
- Uses first 15 frames of each player's side history
- Requires **11 out of 15** frames on the same side to lock baseline
- Players without an established baseline cannot trigger a raid

### Raid Start
- Sliding window of last **7 frames**
- Raid triggers when **6 of 7** frames are on the opponent side
- Only fires if no raid has been recorded yet (one raid per video)

### Raid End — Success
- Sliding window of last **5 frames**
- Raid ends successfully when **4 of 5** frames are back on the raider's baseline side

### Raid End — Timeout (Lost)
- If the locked raider ID is not detected for **120 consecutive frames**, the raid ends as lost
- A keyframe is saved as `raid_N_lost_frame_X.jpg`

---

## 🔒 Raider ID Locking

Once a raid starts, the raider's tracker ID is locked:

```python
self.raider_locked = True
self.raider_id = tid  # locked at raid start, never changes
```

During the raid:
- Only the exact same tracker ID is accepted as the raider
- If the ID disappears, `missing_frames` counter increments
- If the same ID reappears, `missing_frames` resets to 0
- **No ID switching** — the system never reassigns the raider to a different tracker ID

---

## 👤 Player Centering

Player center is computed from **torso keypoints** (shoulders + hips, indices 5, 6, 11, 12) for stability:

```python
torso_kpts = [kpts[5], kpts[6], kpts[11], kpts[12]]  # shoulders + hips
valid_torso = [k for k in torso_kpts if k[0] > 0 and k[1] > 0]
if len(valid_torso) >= 2:
    cx = mean([k[0] for k in valid_torso])
    cy = mean([k[1] for k in valid_torso])
```

Falls back to mean of all valid keypoints, then bounding box center if keypoints unavailable.

---

## 📍 Position Smoothing

Exponential Moving Average applied to player positions:

```python
alpha = 0.5 if is_far_player else 0.7
smooth_cx = alpha * cx + (1 - alpha) * last_pos[0]
smooth_cy = alpha * cy + (1 - alpha) * last_pos[1]
```

- `alpha=0.7` — normal players (more weight on new position)
- `alpha=0.5` — far/small players (more smoothing to reduce noise)
- Far player defined as: bounding box height < 80px or width < 40px

---

## 🧹 Player Cleanup

Players not seen for **90 frames** are removed from the tracking dictionary:

```python
lost_players = [tid for tid, data in all_players.items()
                if frame_count - data['last_seen'] > 90]
```

This is separate from the raider recovery timeout (120 frames).

---

## 📊 Tracking Parameters Summary

| Parameter | Value | Location |
|---|---|---|
| Detection confidence | 0.25 | `data_extract.py` → `model.track()` |
| IOU threshold | 0.3 | `data_extract.py` → `model.track()` |
| Image size | 1280px | `data_extract.py` → `model.track()` |
| Max detections | 50 | `data_extract.py` → `model.track()` |
| Baseline window | 15 frames | `data_extract.py` |
| Baseline consensus | 11/15 | `data_extract.py` |
| Raid start window | 7 frames | `data_extract.py` |
| Raid start threshold | 6/7 | `data_extract.py` |
| Raid end window | 5 frames | `data_extract.py` |
| Raid end threshold | 4/5 | `data_extract.py` |
| Raider recovery timeout | 120 frames | `data_extract.py` |
| Player cleanup timeout | 90 frames | `data_extract.py` |
| EMA alpha (normal) | 0.7 | `data_extract.py` |
| EMA alpha (far player) | 0.5 | `data_extract.py` |
| Far player threshold | height < 80px or width < 40px | `data_extract.py` |
| Position history kept | 30 frames | `data_extract.py` |

---

## 🧪 How to Verify

### Verify penetration is correct
```bash
python scripts/test_penetration.py data/videos/your_video.mp4
```
Should print baulk ~3.75m and bonus ~4.75m.

### Verify tracking during processing
```bash
python scripts/data_extract.py data/videos/your_video.mp4
```
Watch console for:
- `✓ Player X baseline established` — baseline locked correctly
- `🎯 Raid detected!` — raid start triggered
- `🏃 Raid started - Raider X LOCKED` — ID locked
- `⚡ Raider X reappeared` — recovery working
- `🔙 Raider returned to baseline` — success detection working

### Verify CSV output
```bash
python scripts/view_metrics.py data/extracted/your_video_raid_metrics.csv
```
Check `max_penetration` is in realistic range (2–6m for active raids).

---

**Status:** ✅ Implemented and stable
**Last verified against:** `scripts/data_extract.py`, `court/simplified_court.py`
