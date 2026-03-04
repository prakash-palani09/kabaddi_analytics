# Kabaddi Analytics System - Complete Formula Reference

## Table of Contents
1. [Geometric Calculations](#geometric-calculations)
2. [Temporal Metrics](#temporal-metrics)
3. [Spatial Metrics](#spatial-metrics)
4. [Movement Metrics](#movement-metrics)
5. [Engagement Metrics](#engagement-metrics)
6. [Player Profiling Metrics](#player-profiling-metrics)
7. [Ranking Metrics](#ranking-metrics)
8. [Performance Indicators](#performance-indicators)

---

## 1. Geometric Calculations

### 1.1 Penetration Depth (Perpendicular Distance Method)

**Purpose**: Calculate how far the raider penetrated into opponent's court in meters

**Formula**:
```
Given midline defined by two points (x₁, y₁) and (x₂, y₂):

Step 1: Calculate line equation coefficients (Ax + By + C = 0)
  A = y₂ - y₁
  B = x₁ - x₂
  C = x₂ × y₁ - x₁ × y₂

Step 2: Calculate perpendicular distance from raider point (x, y) to midline
  d_pixel = |A × x + B × y + C| / √(A² + B²)

Step 3: Calculate total perpendicular distance from midline to end line
  D_total = |A × x_end + B × y_end + C| / √(A² + B²)
  where (x_end, y_end) is a point on the end line

Step 4: Convert pixel distance to meters
  penetration_meters = (d_pixel / D_total) × 6.5

Step 5: Clamp to non-negative
  penetration = max(0, penetration_meters)
```

**Variables**:
- `(x₁, y₁), (x₂, y₂)`: Midline endpoints (pixels)
- `(x, y)`: Raider position (pixels)
- `(x_end, y_end)`: End line point (pixels)
- `6.5`: Official distance from midline to end line (meters)

**Output**: Penetration depth in meters [0, 6.5]

**Example**:
```
Midline: (100, 200) to (900, 220)
Raider at: (500, 450)
End line point: (500, 650)

A = 220 - 200 = 20
B = 100 - 900 = -800
C = 900 × 200 - 100 × 220 = 158000

d_pixel = |20 × 500 + (-800) × 450 + 158000| / √(20² + 800²)
        = |10000 - 360000 + 158000| / √(400 + 640000)
        = 192000 / 800.25
        = 239.9 pixels

D_total = |20 × 500 + (-800) × 650 + 158000| / 800.25
        = 368000 / 800.25
        = 459.8 pixels

penetration = (239.9 / 459.8) × 6.5 = 3.39 meters
```

---

### 1.2 Line Crossing Detection (Baulk/Bonus)

**Purpose**: Determine if raider crossed specific court lines

**Baulk Line Crossing Formula**:
```
Step 1: Calculate baulk line depth
  baulk_center = (baulk_p1 + baulk_p2) / 2
  baulk_vector = baulk_center - midline_center
  baulk_projection = baulk_vector · depth_direction
  baulk_depth = (baulk_projection / depth_magnitude) × 6.5

Step 2: Check crossing
  crossed_baulk = (raider_penetration ≥ baulk_depth)
```

**Bonus Line Crossing Formula**:
```
Same as baulk, but using bonus line points
  crossed_bonus = (raider_penetration ≥ bonus_depth)
```

**Variables**:
- `baulk_p1, baulk_p2`: Baulk line endpoints (pixels)
- `depth_direction`: Unit vector from midline to end line
- `depth_magnitude`: Distance from midline to end line (pixels)

**Output**: Boolean (True if crossed, False otherwise)

**Typical Values**:
- Baulk line: ~3.75 meters from midline
- Bonus line: ~4.75 meters from midline

---

### 1.3 Point-in-Polygon (Play Box Containment)

**Purpose**: Check if player is inside the play area

**Formula** (Ray Casting Algorithm):
```
Given point (x, y) and polygon with n vertices:

inside = False
p1 = polygon[0]

for i in range(1, n + 1):
    p2 = polygon[i % n]
    
    if y > min(p1.y, p2.y):
        if y ≤ max(p1.y, p2.y):
            if x ≤ max(p1.x, p2.x):
                if p1.y ≠ p2.y:
                    x_intersection = (y - p1.y) × (p2.x - p1.x) / (p2.y - p1.y) + p1.x
                
                if p1.x == p2.x or x ≤ x_intersection:
                    inside = not inside
    
    p1 = p2

return inside
```

**Explanation**: Cast a horizontal ray from the point to infinity. Count edge intersections. Odd count = inside, even count = outside.

**Complexity**: O(n) where n = number of vertices (5 for pentagon)

---

### 1.4 Side Determination (Midline Crossing)

**Purpose**: Determine which side of midline the player is on

**Formula** (Cross Product):
```
Given midline points (x₁, y₁) and (x₂, y₂), and player at (x, y):

side = sign((x₂ - x₁) × (y - y₁) - (y₂ - y₁) × (x - x₁))

where:
  sign(z) = +1 if z > 0
          = -1 if z < 0
          =  0 if z = 0
```

**Output**: 
- `+1`: Right side of midline
- `-1`: Left side of midline
- `0`: On the midline

**Usage**: Detect when raider crosses from baseline side to opposite side

---

## 2. Temporal Metrics

### 2.1 Raid Duration

**Purpose**: Calculate how long the raid lasted

**Formula**:
```
duration = (end_frame - start_frame) / fps

where:
  end_frame: Frame number when raid ended
  start_frame: Frame number when raid started
  fps: Frames per second of video (typically 30)
```

**Output**: Duration in seconds

**Example**:
```
start_frame = 1500
end_frame = 1680
fps = 30

duration = (1680 - 1500) / 30 = 180 / 30 = 6.0 seconds
```

---

### 2.2 Defender Reaction Time

**Purpose**: Time until first defender engages with raider

**Formula**:
```
reaction_time = (first_engagement_frame - raid_start_frame) / fps

where:
  first_engagement_frame: Frame when first defender comes within 80px of raider
  raid_start_frame: Frame when raid started
```

**Output**: Reaction time in seconds (null if no engagement)

**Example**:
```
raid_start = 1500
first_engagement = 1545
fps = 30

reaction_time = (1545 - 1500) / 30 = 45 / 30 = 1.5 seconds
```

---

## 3. Spatial Metrics

### 3.1 Maximum Penetration Depth

**Purpose**: Deepest point raider reached during raid

**Formula**:
```
max_penetration = max([get_penetration_depth(pos) for pos in raider_positions])

where:
  raider_positions: List of all raider positions during raid
  get_penetration_depth(): Function from section 1.1
```

**Enhancement**: Check all body parts (keypoints) for maximum
```
max_penetration = 0
max_point = feet_position

for each position in raid:
    # Check feet
    depth_feet = get_penetration_depth(feet)
    if depth_feet > max_penetration:
        max_penetration = depth_feet
    
    # Check all keypoints (ankles, knees, hands, etc.)
    for keypoint in body_keypoints:
        depth_kpt = get_penetration_depth(keypoint)
        if depth_kpt > max_penetration:
            max_penetration = depth_kpt
    
    # Check bounding box corners
    for corner in [(x1, y2), (x2, y2), (center_x, y2)]:
        depth_corner = get_penetration_depth(corner)
        if depth_corner > max_penetration:
            max_penetration = depth_corner
```

**Output**: Maximum penetration in meters [0, 6.5]

---

### 3.2 Average Penetration Depth

**Purpose**: Mean penetration throughout the raid

**Formula**:
```
avg_penetration = (Σ get_penetration_depth(posᵢ)) / n

where:
  n: Number of position samples
  posᵢ: i-th position of raider
```

**Output**: Average penetration in meters

**Example**:
```
Positions: [2.1m, 3.5m, 4.2m, 3.8m, 2.9m]
avg_penetration = (2.1 + 3.5 + 4.2 + 3.8 + 2.9) / 5 = 16.5 / 5 = 3.3 meters
```

---

### 3.3 Total Distance Traveled

**Purpose**: Total path length covered by raider

**Formula** (Euclidean Distance Sum):
```
total_distance = Σ √[(xᵢ₊₁ - xᵢ)² + (yᵢ₊₁ - yᵢ)²]  for i = 0 to n-1

where:
  (xᵢ, yᵢ): Position at frame i
  n: Total number of positions
```

**Output**: Distance in pixels

**Example**:
```
Positions: [(100, 200), (150, 250), (200, 280)]

d₁ = √[(150-100)² + (250-200)²] = √[2500 + 2500] = 70.7 px
d₂ = √[(200-150)² + (280-250)²] = √[2500 + 900] = 58.3 px

total_distance = 70.7 + 58.3 = 129.0 pixels
```

---

## 4. Movement Metrics

### 4.1 Average Speed

**Purpose**: Mean movement speed during raid

**Formula**:
```
avg_speed = total_distance / duration

where:
  total_distance: From section 3.3 (pixels)
  duration: From section 2.1 (seconds)
```

**Alternative Formula** (using positions with timestamps):
```
total_dist = Σ √[(xᵢ₊₁ - xᵢ)² + (yᵢ₊₁ - yᵢ)²]
duration = (tₙ - t₀) / fps

avg_speed = total_dist / duration
```

**Output**: Speed in pixels/second

**Example**:
```
total_distance = 450 pixels
duration = 6.0 seconds

avg_speed = 450 / 6.0 = 75 pixels/second
```

---

### 4.2 Direction Changes (Agility)

**Purpose**: Count significant direction changes indicating agility

**Formula** (Angle-based):
```
direction_changes = 0

for i in range(1, n-1):
    v₁ = posᵢ - posᵢ₋₁        # Vector from i-1 to i
    v₂ = posᵢ₊₁ - posᵢ        # Vector from i to i+1
    
    # Calculate angle between vectors
    if |v₁| > 5 and |v₂| > 5:  # Ignore small movements
        cos_angle = (v₁ · v₂) / (|v₁| × |v₂|)
        angle = arccos(cos_angle)
        
        if angle > 45°:  # Significant change threshold
            direction_changes += 1
```

**Dot Product Formula**:
```
v₁ · v₂ = v₁.x × v₂.x + v₁.y × v₂.y
```

**Magnitude Formula**:
```
|v| = √(v.x² + v.y²)
```

**Output**: Count of direction changes

**Example**:
```
Positions: [(100, 200), (150, 250), (140, 300), (180, 320)]

v₁ = (150-100, 250-200) = (50, 50)
v₂ = (140-150, 300-250) = (-10, 50)

v₁ · v₂ = 50×(-10) + 50×50 = -500 + 2500 = 2000
|v₁| = √(50² + 50²) = 70.7
|v₂| = √(10² + 50²) = 51.0

cos_angle = 2000 / (70.7 × 51.0) = 0.555
angle = arccos(0.555) = 56.3°

Since 56.3° > 45°, this counts as a direction change.
```

---

### 4.3 Lateral Movement

**Purpose**: Movement perpendicular to depth direction

**Formula**:
```
For each position change:
  movement_vector = posᵢ₊₁ - posᵢ
  
  # Project onto depth direction
  forward_component = movement_vector · depth_direction
  
  # Lateral is the perpendicular component
  lateral_vector = movement_vector - (forward_component × depth_direction)
  lateral_distance = |lateral_vector|

total_lateral = Σ lateral_distance
```

**Output**: Total lateral movement in pixels

---

## 5. Engagement Metrics

### 5.1 Defenders Engaged

**Purpose**: Count unique defenders who came close to raider

**Formula**:
```
engaged_defenders = {}

for each raider_position (rₓ, rᵧ, rₜ):
    for each defender_id and their positions:
        for each defender_position (dₓ, dᵧ, dₜ):
            # Check if same time window
            if |rₜ - dₜ| ≤ 2 frames:
                # Calculate distance
                distance = √[(rₓ - dₓ)² + (rᵧ - dᵧ)²]
                
                # Check if within engagement threshold
                if distance < 80 pixels:
                    engaged_defenders.add(defender_id)
                    break

defenders_engaged = len(engaged_defenders)
```

**Threshold**: 80 pixels ≈ 1-1.5 meters (typical engagement distance)

**Output**: Count of unique defenders engaged

---

## 6. Player Profiling Metrics

### 6.1 Success Rate

**Purpose**: Percentage of successful raids

**Formula**:
```
success_rate = (successful_raids / total_raids) × 100

where:
  successful_raids: Count of raids where raider returned to baseline
  total_raids: Total number of raids attempted
```

**Output**: Percentage [0, 100]

**Example**:
```
Total raids: 50
Successful raids: 32

success_rate = (32 / 50) × 100 = 64.0%
```

---

### 6.2 Average Points per Raid

**Purpose**: Mean scoring contribution per raid

**Formula**:
```
avg_points = total_points / total_raids

where:
  total_points: Sum of all raid points
  total_raids: Total number of raids
```

**Output**: Average points per raid

**Example**:
```
Raid points: [1, 2, 0, 3, 1, 2, 0, 1]
total_points = 10
total_raids = 8

avg_points = 10 / 8 = 1.25 points/raid
```

---

### 6.3 Raids per Match

**Purpose**: Activity level indicator

**Formula**:
```
raids_per_match = total_raids / total_matches

where:
  total_raids: Total raids across all matches
  total_matches: Number of unique matches played
```

**Output**: Average raids per match

**Example**:
```
Total raids: 120
Total matches: 10

raids_per_match = 120 / 10 = 12 raids/match
```

---

## 7. Ranking Metrics

### 7.1 Composite Player Score

**Purpose**: Single score combining multiple performance dimensions

**Formula**:
```
score = w₁ × success_rate + 
        w₂ × normalized_penetration + 
        w₃ × normalized_points + 
        w₄ × duration_penalty

where:
  w₁ = 0.30  (Success rate weight)
  w₂ = 0.25  (Penetration weight)
  w₃ = 0.25  (Points weight)
  w₄ = 0.20  (Duration weight)
```

**Normalization Formulas**:

**Penetration Normalization**:
```
normalized_penetration = min(avg_penetration / 5.0, 1.0) × 100

Assumes 5.0 meters as elite penetration
```

**Points Normalization**:
```
normalized_points = min(avg_points / 3.0, 1.0) × 100

Assumes 3.0 points/raid as elite performance
```

**Duration Penalty**:
```
duration_penalty = -(avg_duration / 10) × 100

Penalizes longer raids (inefficiency)
Assumes 10 seconds as baseline
```

**Complete Example**:
```
Player Stats:
- success_rate = 65%
- avg_penetration = 3.8m
- avg_points = 1.8
- avg_duration = 7.2s

Calculations:
normalized_penetration = min(3.8 / 5.0, 1.0) × 100 = 76.0
normalized_points = min(1.8 / 3.0, 1.0) × 100 = 60.0
duration_penalty = -(7.2 / 10) × 100 = -72.0

score = 0.30 × 65 + 0.25 × 76.0 + 0.25 × 60.0 + 0.20 × (-72.0)
      = 19.5 + 19.0 + 15.0 - 14.4
      = 39.1
```

**Output**: Composite score (typically 0-100 range)

---

### 7.2 Rank Assignment

**Purpose**: Assign ordinal ranks based on scores

**Formula**:
```
1. Sort players by score (descending)
2. Assign ranks sequentially

ranks = []
current_rank = 1

for player, score in sorted_players:
    ranks.append({
        'player_id': player,
        'score': score,
        'rank': current_rank
    })
    current_rank += 1
```

**Output**: List of players with ranks

---

## 8. Performance Indicators (Radar Chart)

### 8.1 Efficiency

**Purpose**: Success rate indicator

**Formula**:
```
efficiency = min(success_rate, 100)
```

**Output**: Percentage [0, 100]

---

### 8.2 Aggression

**Purpose**: Penetration depth indicator

**Formula**:
```
aggression = min((avg_penetration / 5.0) × 100, 100)

where:
  5.0: Elite penetration threshold (meters)
```

**Output**: Percentage [0, 100]

---

### 8.3 Impact

**Purpose**: Scoring contribution indicator

**Formula**:
```
impact = min((avg_points / 3.0) × 100, 100)

where:
  3.0: Elite points/raid threshold
```

**Output**: Percentage [0, 100]

---

### 8.4 Control

**Purpose**: Efficiency with optimal duration

**Formula**:
```
# Duration score
if 5 ≤ avg_duration ≤ 20:
    duration_score = 100
elif avg_duration < 5:
    duration_score = (avg_duration / 5) × 100
else:
    duration_score = max(100 - ((avg_duration - 20) / 5) × 100, 0)

# Control combines success and duration
control = (success_rate / 100) × duration_score
control = min(max(control, 0), 100)
```

**Explanation**:
- Optimal duration: 5-20 seconds (full score)
- Too fast (<5s): Proportional penalty
- Too slow (>20s): Linear penalty

**Output**: Percentage [0, 100]

---

### 8.5 Consistency

**Purpose**: Activity level indicator

**Formula**:
```
consistency = min((raids_per_match / 15) × 100, 100)

where:
  15: Elite raids/match threshold
```

**Output**: Percentage [0, 100]

**Example**:
```
raids_per_match = 12

consistency = min((12 / 15) × 100, 100) = min(80, 100) = 80%
```

---

## 9. Position Smoothing

### 9.1 Exponential Moving Average (EMA)

**Purpose**: Reduce jitter in player position tracking

**Formula**:
```
smoothed_x = α × current_x + (1 - α) × previous_x
smoothed_y = α × current_y + (1 - α) × previous_y

where:
  α = 0.7 for normal players (more smoothing)
  α = 0.5 for far players (less smoothing, more responsive)
```

**Explanation**:
- Higher α: More weight to current position (less smoothing)
- Lower α: More weight to previous position (more smoothing)

**Example**:
```
previous_x = 100, current_x = 120, α = 0.7

smoothed_x = 0.7 × 120 + 0.3 × 100 = 84 + 30 = 114
```

---

## 10. Summary Table

| Metric | Formula | Unit | Range |
|--------|---------|------|-------|
| Penetration Depth | (d_pixel / D_total) × 6.5 | meters | [0, 6.5] |
| Raid Duration | (end_frame - start_frame) / fps | seconds | [0, ∞) |
| Success Rate | (successful / total) × 100 | % | [0, 100] |
| Avg Speed | total_distance / duration | px/s | [0, ∞) |
| Direction Changes | Count(angle > 45°) | count | [0, ∞) |
| Defenders Engaged | Count(distance < 80px) | count | [0, 7] |
| Composite Score | Σ(wᵢ × metricᵢ) | score | [0, 100] |
| Efficiency | success_rate | % | [0, 100] |
| Aggression | (penetration / 5.0) × 100 | % | [0, 100] |
| Impact | (points / 3.0) × 100 | % | [0, 100] |
| Control | (success_rate / 100) × duration_score | % | [0, 100] |
| Consistency | (raids_per_match / 15) × 100 | % | [0, 100] |

---

## 11. Constants and Thresholds

| Constant | Value | Description |
|----------|-------|-------------|
| END_DISTANCE | 6.5 m | Midline to end line distance |
| BAULK_DISTANCE | 3.75 m | Midline to baulk line distance |
| BONUS_DISTANCE | 4.75 m | Midline to bonus line distance |
| ENGAGEMENT_THRESHOLD | 80 px | Defender engagement distance |
| DIRECTION_CHANGE_ANGLE | 45° | Significant direction change |
| ELITE_PENETRATION | 5.0 m | Elite penetration threshold |
| ELITE_POINTS | 3.0 | Elite points/raid threshold |
| ELITE_RAIDS_PER_MATCH | 15 | Elite activity level |
| OPTIMAL_DURATION_MIN | 5 s | Minimum optimal raid duration |
| OPTIMAL_DURATION_MAX | 20 s | Maximum optimal raid duration |

---

**Document Version**: 1.0  
**Last Updated**: 2024  
**Project**: Vision-Based Kabaddi Analytics System
