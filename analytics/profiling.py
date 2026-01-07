def build_raider_profile(raids):
    """
    raids: list of dicts with raid metrics
    """
    total_raids = len(raids)
    successful = sum(1 for r in raids if r["success"])
    avg_duration = sum(r["duration"] for r in raids) / total_raids
    avg_penetration = sum(r["penetration"] for r in raids) / total_raids

    return {
        "raids": total_raids,
        "success_rate": successful / total_raids,
        "avg_duration": avg_duration,
        "avg_penetration": avg_penetration
    }


def build_defender_profile(defensive_events):
    total_engagements = len(defensive_events)
    successful_stops = sum(1 for e in defensive_events if e["stop"])

    return {
        "engagements": total_engagements,
        "stop_success_rate": successful_stops / total_engagements
    }

def build_raider_profile(raids):
    total_raids = len(raids)
    
    successful_raids = sum(1 for r in raids if r["success"])
    total_penetration = sum(r["penetration"] for r in raids)
    total_duration = sum(r["duration"] for r in raids)
    
    return {
        "raids": total_raids,
        "success_rate": successful_raids/total_raids if total_raids else 0,
        "avg_penetration": total_penetration/total_raids if total_raids else 0,
        "avg_duration": total_duration/total_raids if total_raids else 0
    }