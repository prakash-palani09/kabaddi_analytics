# Raid Metrics Extraction

## Overview
Extract comprehensive raid-level metrics from tracked Kabaddi match videos.

## Metrics Extracted

### 🎯 Core Metrics
- **Duration**: Total raid time in seconds
- **Max Penetration**: Deepest point reached from midline (pixels)
- **Avg Penetration**: Average depth during raid

### 🏟️ Court Analysis
- **Crossed Bonus Line**: Boolean
- **Crossed Baulk Line**: Boolean
- **Deepest Zone**: safe_zone / mid_zone / deep_zone
- **Zones Visited**: Number of unique zones
- **Lateral Movement**: Left-right movement range
- **Sectors Visited**: Number of court sectors (left/center/right)

### 🤼 Engagement Metrics
- **Defenders Engaged**: Count of unique defenders within threshold
- **Reaction Time**: Time until first defender engagement

### 🏃 Movement Metrics
- **Avg Speed**: Movement speed in pixels/second
- **Direction Changes**: Agility indicator (significant angle changes)

## Usage

### 1. Extract Metrics from Video
```bash
python scripts/data_extract.py data/videos/your_video.mp4
```

This will:
- Track all players
- Detect raids (midline crossings)
- Extract metrics for each raid
- Save to CSV: `your_video_raid_metrics.csv`

### 2. View Results
```bash
python scripts/view_metrics.py data/videos/your_video_raid_metrics.csv
```

## Output Format

CSV with columns:
- raider_id
- duration
- max_penetration
- avg_penetration
- crossed_bonus
- crossed_baulk
- deepest_zone
- zones_visited
- lateral_movement
- sectors_visited
- defenders_engaged
- reaction_time
- avg_speed
- direction_changes
- start_frame
- end_frame

## Next Steps

Use extracted metrics for:
1. **Player Profiling** - Aggregate metrics per player
2. **Player Ranking** - Score players based on performance
3. **Team Analysis** - Compare raider vs defender performance
4. **Tactical Insights** - Identify patterns and strategies
