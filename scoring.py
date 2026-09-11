"""
backend/scoring.py
Multi-Factor Maritime Vessel Attribution Engine.
Evaluates spatial, temporal, kinematic, vessel type, and behavioral factors
to rank potential source vessels with an explainable evidence breakdown.
"""

import math
from datetime import datetime
from typing import List, Dict, Any


def score_spatial_proximity(distance_km: float, max_radius_km: float = 15.0) -> float:
    """
    Evaluates spatial proximity (35% weight).
    Scores 100 if within 1.0 km of origin, decaying towards 0 at max_radius_km.
    """
    if distance_km <= 1.0:
        return 100.0
    if distance_km >= max_radius_km:
        return 0.0
    # Inverse quadratic decay
    decay = 1.0 - ((distance_km - 1.0) / (max_radius_km - 1.0))
    return round(max(0.0, min(100.0, (decay ** 1.5) * 100.0)), 1)


def score_temporal_correlation(time_diff_minutes: float, max_window_minutes: float = 120.0) -> float:
    """
    Evaluates temporal correlation (25% weight).
    Scores 100 if vessel was present within 15 minutes of estimated release time.
    """
    abs_diff = abs(time_diff_minutes)
    if abs_diff <= 15.0:
        return 100.0
    if abs_diff >= max_window_minutes:
        return 0.0
    decay = 1.0 - ((abs_diff - 15.0) / (max_window_minutes - 15.0))
    return round(max(0.0, min(100.0, decay * 100.0)), 1)


def score_trajectory_consistency(vessel_course_deg: float, slick_orientation_deg: float) -> float:
    """
    Evaluates trajectory consistency (20% weight).
    Compares vessel heading vector with the slick's major elongation axis.
    """
    angle_diff = abs((vessel_course_deg - slick_orientation_deg + 180) % 360 - 180)
    # If vessel aligns parallel or anti-parallel with slick axis (diff near 0 or 180)
    effective_diff = min(angle_diff, 180 - angle_diff)
    # Under 20 deg difference is high consistency
    if effective_diff <= 15.0:
        return 95.0
    elif effective_diff <= 35.0:
        return 80.0
    elif effective_diff <= 60.0:
        return 55.0
    return 30.0


def score_vessel_type(vessel_type: str) -> float:
    """
    Evaluates vessel risk profile based on cargo and bunker capacities (10% weight).
    """
    vtype = vessel_type.lower()
    if "crude" in vtype or "vlcc" in vtype or "oil tanker" in vtype:
        return 100.0
    elif "chemical" in vtype or "products tanker" in vtype:
        return 85.0
    elif "container" in vtype or "cargo" in vtype or "bulk" in vtype:
        return 55.0 # Large bunker fuel capacity
    elif "tug" in vtype or "offshore" in vtype or "supply" in vtype:
        return 25.0
    elif "fishing" in vtype:
        return 15.0
    return 30.0


def score_behavioral_anomaly(vessel: Dict[str, Any]) -> float:
    """
    Evaluates behavioral anomalies (10% weight):
    - Significant speed reductions (>30%) near the origin
    - Detected AIS transponder silence / position gaps
    - Erratic course deviations
    """
    score = 15.0 # baseline normal navigation
    anomalies = vessel.get("anomalies", [])

    if len(anomalies) >= 3:
        score = 95.0
    elif len(anomalies) == 2:
        score = 80.0
    elif len(anomalies) == 1:
        score = 50.0

    return score


def evaluate_vessel_attribution(
    vessel: Dict[str, Any],
    origin_point: Dict[str, float],
    origin_time_iso: str,
    slick_orientation_deg: float = 68.5
) -> Dict[str, Any]:
    """
    Runs the 5-factor scoring model on a single vessel and compiles the explainable evidence report.
    """
    cpa = vessel.get("closest_point_of_approach", {})
    dist_km = cpa.get("distance_km", 99.0)

    # Calculate time delta in minutes
    time_diff_min = 999.0
    cpa_time_str = cpa.get("timestamp", "")
    if cpa_time_str and origin_time_iso:
        try:
            t_cpa = datetime.fromisoformat(cpa_time_str.replace("Z", "+00:00"))
            t_orig = datetime.fromisoformat(origin_time_iso.replace("Z", "+00:00"))
            time_diff_min = round((t_cpa - t_orig).total_seconds() / 60.0, 1)
        except Exception:
            time_diff_min = 60.0

    course_deg = cpa.get("course_deg", 0.0)

    # 1. Proximity score (35%)
    s_prox = score_spatial_proximity(dist_km)

    # 2. Temporal score (25%)
    s_temp = score_temporal_correlation(time_diff_min)

    # 3. Trajectory score (20%)
    s_traj = score_trajectory_consistency(course_deg, slick_orientation_deg)

    # 4. Type score (10%)
    s_type = score_vessel_type(vessel.get("vessel_type", "Unknown"))

    # 5. Anomaly score (10%)
    s_anom = score_behavioral_anomaly(vessel)

    # Total Weighted Score
    total_score = round(
        (0.35 * s_prox) +
        (0.25 * s_temp) +
        (0.20 * s_traj) +
        (0.10 * s_type) +
        (0.10 * s_anom),
        1
    )

    # Classification Tier
    if total_score >= 80.0:
        tier = "HIGH POTENTIAL SOURCE"
        badge_class = "badge-danger"
    elif total_score >= 50.0:
        tier = "MODERATE RELEVANCE"
        badge_class = "badge-warning"
    else:
        tier = "FILTERED TRAFFIC (LOW)"
        badge_class = "badge-info"

    # Compile Explainable Evidence Items
    evidence = []
    if dist_km <= 2.0:
        evidence.append(f"Crucial Proximity: Intercepted within {dist_km} km of estimated origin")
    else:
        evidence.append(f"Proximity: Passed at distance of {dist_km} km")

    if abs(time_diff_min) <= 20.0:
        evidence.append(f"Tight Time Window: Passed within {int(abs(time_diff_min))} mins of estimated release")
    else:
        evidence.append(f"Temporal Window: Passed {int(abs(time_diff_min))} mins away from estimated release")

    if s_type >= 80.0:
        evidence.append(f"High-Risk Vessel Category: {vessel.get('vessel_type')}")

    for a in vessel.get("anomalies", []):
        evidence.append(f"Observed Anomaly: {a}")

    return {
        "mmsi": vessel["mmsi"],
        "name": vessel.get("name", "Unknown Vessel"),
        "vessel_type": vessel.get("vessel_type"),
        "flag": vessel.get("flag"),
        "total_score": total_score,
        "classification": tier,
        "badge_class": badge_class,
        "score_breakdown": {
            "spatial_proximity": {"score": s_prox, "weight_pct": 35, "weighted_val": round(0.35 * s_prox, 1)},
            "temporal_correlation": {"score": s_temp, "weight_pct": 25, "weighted_val": round(0.25 * s_temp, 1)},
            "trajectory_consistency": {"score": s_traj, "weight_pct": 20, "weighted_val": round(0.20 * s_traj, 1)},
            "vessel_type_risk": {"score": s_type, "weight_pct": 10, "weighted_val": round(0.10 * s_type, 1)},
            "behavioral_anomaly": {"score": s_anom, "weight_pct": 10, "weighted_val": round(0.10 * s_anom, 1)}
        },
        "closest_approach": {
            "distance_km": dist_km,
            "time_diff_minutes": time_diff_min,
            "speed_knots": cpa.get("speed_knots"),
            "course_deg": course_deg
        },
        "evidence_log": evidence
    }


def rank_vessels(
    vessels: List[Dict[str, Any]],
    origin_point: Dict[str, float],
    origin_time_iso: str,
    slick_orientation_deg: float = 68.5
) -> List[Dict[str, Any]]:
    """Evaluates all candidate vessels and sorts them by attribution score descending."""
    results = [
        evaluate_vessel_attribution(v, origin_point, origin_time_iso, slick_orientation_deg)
        for v in vessels
    ]
    results.sort(key=lambda x: x["total_score"], reverse=True)
    for idx, r in enumerate(results, start=1):
        r["rank"] = idx
    return results
