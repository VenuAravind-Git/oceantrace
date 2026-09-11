"""
backend/drift.py
Hydrodynamic Marine Drift Physics Engine.
Computes backward trajectory (Hindcasting to origin) and forward trajectory (Forecasting)
using ocean currents and wind leeway vector addition with Coriolis deflection.
"""

import math
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple


def calculate_drift_vector(
    current_speed_knots: float,
    current_direction_deg: float,
    wind_speed_knots: float,
    wind_direction_deg: float,
    latitude: float
) -> Tuple[float, float, float]:
    """
    Computes net drift velocity (speed in knots and direction towards which oil moves in degrees).
    Uses the internationally accepted 3% wind leeway rule (NOAA GNOME / IMO guidelines).
    Applies Coriolis deflection: ~15 deg right in Northern Hemisphere, ~15 deg left in Southern.
    """
    # 1. Current vector (direction represents "flowing towards")
    # Speed in knots, angle in radians (mathematical angle from East)
    # Oceanographic heading: 0=North, 90=East
    rad_curr = math.radians((90 - current_direction_deg) % 360)
    u_curr = current_speed_knots * math.cos(rad_curr)
    v_curr = current_speed_knots * math.sin(rad_curr)

    # 2. Wind leeway: Oil drifts at approx 3.2% of 10m wind speed
    # Meteorological wind direction is "coming from", so drift is opposite: (wind_direction + 180)
    wind_towards_deg = (wind_direction_deg + 180) % 360

    # Coriolis deflection angle (approx +12 deg right in North, -12 deg left in South)
    coriolis_deflection = 12.0 if latitude >= 0 else -12.0
    wind_drift_deg = (wind_towards_deg + coriolis_deflection) % 360

    rad_wind = math.radians((90 - wind_drift_deg) % 360)
    wind_leeway_speed = 0.032 * wind_speed_knots
    u_wind = wind_leeway_speed * math.cos(rad_wind)
    v_wind = wind_leeway_speed * math.sin(rad_wind)

    # 3. Superposition: Net drift vector
    u_net = u_curr + u_wind
    v_net = v_curr + v_wind

    net_speed_knots = math.sqrt(u_net ** 2 + v_net ** 2)
    # Convert math angle back to navigational compass heading
    nav_angle = (90 - math.degrees(math.atan2(v_net, u_net))) % 360

    return net_speed_knots, nav_angle, coriolis_deflection


def step_geographic_position(
    lat: float,
    lon: float,
    speed_knots: float,
    course_deg: float,
    duration_hours: float
) -> Tuple[float, float]:
    """Projects geographic position forward or backward given speed, heading and hours."""
    distance_nm = speed_knots * duration_hours
    distance_km = distance_nm * 1.852

    km_per_deg_lat = 111.132
    km_per_deg_lon = 111.320 * math.cos(math.radians(lat))

    rad = math.radians((90 - course_deg) % 360)
    dx_km = distance_km * math.cos(rad)
    dy_km = distance_km * math.sin(rad)

    new_lat = lat + (dy_km / km_per_deg_lat)
    new_lon = lon + (dx_km / km_per_deg_lon)

    return round(new_lat, 5), round(new_lon, 5)


def run_hindcast(
    observed_centroid: Tuple[float, float],
    observation_time_iso: str,
    estimated_age_hours: float,
    current_speed_knots: float,
    current_direction_deg: float,
    wind_speed_knots: float,
    wind_direction_deg: float
) -> Dict[str, Any]:
    """
    Traces the slick backward from satellite observation time to find origin window.
    Hindcast inverts the drift vector: Heading_backward = (Heading_forward + 180) % 360.
    """
    obs_time = datetime.fromisoformat(observation_time_iso.replace("Z", "+00:00"))
    c_lat, c_lon = observed_centroid

    net_speed, forward_heading, coriolis = calculate_drift_vector(
        current_speed_knots, current_direction_deg,
        wind_speed_knots, wind_direction_deg, c_lat
    )
    backward_heading = (forward_heading + 180.0) % 360.0

    # Hourly simulation steps backward
    steps = []
    current_lat, current_lon = c_lat, c_lon
    total_hours = max(1.0, estimated_age_hours)
    num_steps = max(3, int(total_hours))
    step_duration = total_hours / num_steps

    steps.append({
        "step": 0,
        "hours_offset": 0.0,
        "timestamp": obs_time.isoformat(),
        "latitude": current_lat,
        "longitude": current_lon
    })

    for i in range(1, num_steps + 1):
        elapsed_hours = i * step_duration
        current_lat, current_lon = step_geographic_position(
            current_lat, current_lon, net_speed, backward_heading, step_duration
        )
        t_step = obs_time - timedelta(hours=elapsed_hours)
        steps.append({
            "step": i,
            "hours_offset": -round(elapsed_hours, 1),
            "timestamp": t_step.isoformat(),
            "latitude": current_lat,
            "longitude": current_lon
        })

    origin_point = (current_lat, current_lon)
    origin_time = obs_time - timedelta(hours=total_hours)

    # Uncertainty radius expands with drift time (~0.35 km per hour of drift)
    uncertainty_radius_km = round(1.5 + (0.35 * total_hours), 2)

    return {
        "origin_point": {
            "latitude": origin_point[0],
            "longitude": origin_point[1]
        },
        "estimated_release_time": origin_time.isoformat(),
        "release_window_hours": [
            (origin_time - timedelta(minutes=45)).isoformat(),
            (origin_time + timedelta(minutes=45)).isoformat()
        ],
        "uncertainty_radius_km": uncertainty_radius_km,
        "net_drift_speed_knots": round(net_speed, 2),
        "forward_drift_course_deg": round(forward_heading, 1),
        "coriolis_deflection_deg": coriolis,
        "trajectory": steps
    }


def run_forecast(
    observed_centroid: Tuple[float, float],
    observation_time_iso: str,
    forecast_hours: float,
    current_speed_knots: float,
    current_direction_deg: float,
    wind_speed_knots: float,
    wind_direction_deg: float
) -> List[Dict[str, Any]]:
    """Simulates forward trajectory over the specified forecast hours (e.g. 12h or 24h)."""
    obs_time = datetime.fromisoformat(observation_time_iso.replace("Z", "+00:00"))
    c_lat, c_lon = observed_centroid

    net_speed, forward_heading, _ = calculate_drift_vector(
        current_speed_knots, current_direction_deg,
        wind_speed_knots, wind_direction_deg, c_lat
    )

    steps = []
    current_lat, current_lon = c_lat, c_lon
    num_steps = 6 # 6 intervals
    step_duration = forecast_hours / num_steps

    steps.append({
        "step": 0,
        "hours_ahead": 0.0,
        "timestamp": obs_time.isoformat(),
        "latitude": current_lat,
        "longitude": current_lon
    })

    for i in range(1, num_steps + 1):
        elapsed_hours = i * step_duration
        current_lat, current_lon = step_geographic_position(
            current_lat, current_lon, net_speed, forward_heading, step_duration
        )
        t_step = obs_time + timedelta(hours=elapsed_hours)
        steps.append({
            "step": i,
            "hours_ahead": round(elapsed_hours, 1),
            "timestamp": t_step.isoformat(),
            "latitude": current_lat,
            "longitude": current_lon
        })

    return steps
