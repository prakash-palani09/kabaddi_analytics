"""
Generate synthetic kabaddi data: 28 players (7 per team, 4 teams), each played 3 matches
Duration: 10-25 sec with varied control per player
"""
import csv
import random
import os

def generate_data():
    data = []
    
    # 4 teams, 7 players each = 28 players
    teams = ['TeamA', 'TeamB', 'TeamC', 'TeamD']
    players = [f"{team}_P{i}" for team in teams for i in range(1, 8)]
    
    # 12 matches (each team plays 3 matches)
    matches = [f'M{i}' for i in range(1, 13)]
    
    # Assign matches to teams
    team_matches = {team: matches[i*3:(i+1)*3] for i, team in enumerate(teams)}
    
    # Assign duration profile to each player (for varied control)
    player_duration_profile = {}
    for player in players:
        # Random duration center point between 10-25
        center = random.uniform(12, 23)
        variance = random.uniform(1.5, 3.5)
        player_duration_profile[player] = (center, variance)
    
    for player in players:
        team = player.split('_')[0]
        player_matches = team_matches[team]
        center, variance = player_duration_profile[player]
        
        for match in player_matches:
            raids_in_match = random.randint(8, 20)
            
            for _ in range(raids_in_match):
                # Duration varies per player (10-25 sec range)
                duration = round(random.gauss(center, variance), 1)
                duration = max(10.0, min(25.0, duration))  # Clamp to 10-25
                
                penetration = random.randint(80, 220)
                success = random.choices([0, 1], weights=[40, 60])[0]
                raid_points = random.choices([1, 2, 3], weights=[60, 30, 10])[0] if success else 0
                
                data.append({
                    'match_id': match,
                    'player_id': player,
                    'raid_duration_sec': duration,
                    'penetration_px': penetration,
                    'success': success,
                    'raid_points': raid_points
                })
    
    # Save to CSV
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = os.path.join(root_dir, "data", "synthetic", "synthetic_data.csv")
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['match_id', 'player_id', 'raid_duration_sec', 'penetration_px', 'success', 'raid_points'])
        writer.writeheader()
        writer.writerows(data)
    
    print(f"Generated {len(data)} raids for {len(players)} players")
    print(f"Duration range: 10-25 seconds (varied per player)")
    print(f"Saved to: {csv_path}")

if __name__ == "__main__":
    generate_data()
