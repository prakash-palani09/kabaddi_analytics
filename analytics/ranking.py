def raider_score(profile):
    return (
        0.4 * profile["success_rate"] +
        0.3 * profile["avg_penetration"] +
        0.3 * (1 / profile["avg_duration"])
    )


def rank_players(player_profiles):
    scored = []
    for player_id, profile in player_profiles.items():
        score = raider_score(profile)
        scored.append((player_id, score))

    return sorted(scored, key=lambda x: x[1], reverse=True)

def raider_score(profile, weights=None):
    if weights is None:
        weights = {
            "success_rate": 0.30,
            "avg_points": 0.25,
            "avg_penetration": 0.25,
            "avg_duration": 0.20
        }
    
    # Normalize penetration (assuming max ~250px)
    norm_penetration = min(profile["avg_penetration"] / 250, 1.0)
    
    # Normalize points (assuming max average ~3 points)
    norm_points = min(profile["avg_points"] / 3.0, 1.0)
    
    return (
        weights["success_rate"] * profile["success_rate"]
        + weights["avg_penetration"] * norm_penetration
        + weights["avg_points"] * norm_points
        - weights["avg_duration"] * (profile["avg_duration"] / 10)  # Penalty for long duration
    )
    
def rank_players(player_profiles):
    ranked = []
    for player_id, profile in player_profiles.items():
        score = raider_score(profile)
        ranked.append((player_id,score))
        
    return sorted(ranked, key=lambda x:x[1], reverse=True)

def assign_ranks(sorted_scores):
    """
    sorted_scores: list of (player_id, score) sorted DESC
    """
    ranked = []
    current_rank = 1

    for player_id, score in sorted_scores:
        ranked.append({
            "player_id": player_id,
            "score": score,
            "rank": current_rank
        })
        current_rank += 1

    return ranked