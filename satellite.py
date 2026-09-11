"""
backend/satellite.py
Synthetic Aperture Radar (SAR) and Earth Observation (EO) Satellite Slick Processing.
Calculates geometry, area, perimeter, elongation, weathering state, and estimated release age.
"""

import math
from typing import List, Tuple, Dict, Any


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates the great-circle distance between two points on the Earth in kilometers."""
    R = 6371.0 # Earth's mean radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def calculate_polygon_centroid(polygon: List[List[float]]) -> Tuple[float, float]:
    """Calculates the centroid (mean latitude, mean longitude) of a polygon."""
    if not polygon:
        return (0.0, 0.0)
    # Exclude closing coordinate if identical to first
    coords = polygon[:-1] if (len(polygon) > 1 and polygon[0] == polygon[-1]) else polygon
    avg_lat = sum(p[0] for p in coords) / len(coords)
    avg_lon = sum(p[1] for p in coords) / len(coords)
    return round(avg_lat, 5), round(avg_lon, 5)


def calculate_polygon_perimeter_km(polygon: List[List[float]]) -> float:
    """Calculates the total perimeter of a geographic polygon in kilometers."""
    if len(polygon) < 2:
        return 0.0
    perimeter = 0.0
    for i in range(len(polygon) - 1):
        perimeter += haversine_distance_km(
            polygon[i][0], polygon[i][1],
            polygon[i + 1][0], polygon[i + 1][1]
        )
    return round(perimeter, 2)


def calculate_polygon_area_km2(polygon: List[List[float]]) -> float:
    """
    Approximates geographic polygon area in km² using planar projection
    centered at the polygon centroid (accurate for slicks up to thousands of km²).
    """
    if len(polygon) < 3:
        return 0.0

    c_lat, c_lon = calculate_polygon_centroid(polygon)
    # Conversion factors at centroid latitude
    km_per_deg_lat = 111.132
    km_per_deg_lon = 111.320 * math.cos(math.radians(c_lat))

    # Convert coordinates to local Cartesian (x: East km, y: North km)
    xy_points = [
        ((p[1] - c_lon) * km_per_deg_lon, (p[0] - c_lat) * km_per_deg_lat)
        for p in polygon
    ]

    # Shoelace formula
    n = len(xy_points)
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += xy_points[i][0] * xy_points[j][1]
        area -= xy_points[j][0] * xy_points[i][1]

    return round(abs(area) / 2.0, 2)


def estimate_slick_age_and_weathering(area_km2: float, wind_speed_knots: float) -> Dict[str, Any]:
    """
    Estimates slick age using Fay's spreading formulation and wind-induced weathering.
    Heavy crude spreads rapidly in gravity-inertial phase then slows in surface tension phase.
    """
    # Empirical spreading relation: t ~ (Area / constant) ^ (1 / spreading_exponent)
    # Typical slick spreading rate in moderate seas (~10-15 kt wind)
    spreading_rate_factor = 2.2 + (wind_speed_knots * 0.05)
    estimated_age_hours = round(math.sqrt(max(1.0, area_km2)) * (spreading_rate_factor / 1.5), 1)

    # Weathering metrics
    evaporation_pct = round(min(55.0, 15.0 + (estimated_age_hours * 2.8) + (wind_speed_knots * 0.5)), 1)
    emulsification_pct = round(min(70.0, max(5.0, (estimated_age_hours - 2.0) * 3.5)), 1)

    if estimated_age_hours < 3.0:
        stage = "Phase I (Fresh Slick / Gravity-Inertial Spreading)"
    elif estimated_age_hours < 8.0:
        stage = "Phase II (Viscous-Surface Tension Spreading)"
    else:
        stage = "Phase III (Weathered Chocolate-Mousse Emulsion)"

    return {
        "estimated_age_hours": estimated_age_hours,
        "spreading_stage": stage,
        "evaporation_loss_pct": evaporation_pct,
        "emulsification_pct": emulsification_pct
    }
