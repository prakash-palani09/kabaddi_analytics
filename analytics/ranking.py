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
