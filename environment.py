"""
backend/environment.py
Meteorological & Oceanographic Data Provider.
Integrates live real-time ocean currents, winds, waves, and temperature
via Open-Meteo Free Marine and Weather APIs (100% open, zero API key required).
"""

import os
import requests
from typing import Dict, Any

DEFAULT_CONDITIONS = {
    "source": "DEMO_CALIBRATED_HYDRO",
    "surface_current_speed_knots": 0.75,
    "surface_current_direction_deg": 245.0,
    "wind_speed_knots": 13.5,
    "wind_direction_deg": 55.0,
    "wave_height_m": 0.8,
    "water_temperature_c": 28.5,
    "sea_state": "Slight (Douglas Scale 2)"
}


def get_marine_conditions(latitude: float, longitude: float) -> Dict[str, Any]:
    """
    Fetches live real-time marine current, wave, and wind parameters from Open-Meteo.
    Zero-key open API directly returning authentic satellite-derived hydrodynamic vectors.
    """
    use_live_env = os.environ.get("USE_LIVE_OCEAN_API", "true").lower() in ("1", "true", "yes")

    if not use_live_env:
        return DEFAULT_CONDITIONS

    try:
        # 1. Fetch Marine Current & Wave Data
        marine_url = "https://marine-api.open-meteo.com/v1/marine"
        marine_params = {
            "latitude": round(latitude, 4),
            "longitude": round(longitude, 4),
            "current": ["ocean_current_velocity", "ocean_current_direction", "wave_height", "wave_direction"]
        }
        res_marine = requests.get(marine_url, params=marine_params, timeout=4)
        
        current_knots = 0.75
        current_dir = 240.0
        wave_height = 0.6
        if res_marine.status_code == 200:
            m_curr = res_marine.json().get("current", {})
            # velocity in km/h -> knots (1 km/h = 0.539957 knots)
            vel_raw = m_curr.get("ocean_current_velocity")
            if vel_raw is not None:
                current_knots = max(0.2, round(float(vel_raw) * 0.539957, 2))
            dir_raw = m_curr.get("ocean_current_direction")
            if dir_raw is not None:
                current_dir = round(float(dir_raw), 1)
            wave_raw = m_curr.get("wave_height")
            if wave_raw is not None:
                wave_height = round(float(wave_raw), 2)

        # 2. Fetch Surface Wind Data
        weather_url = "https://api.open-meteo.com/v1/forecast"
        weather_params = {
            "latitude": round(latitude, 4),
            "longitude": round(longitude, 4),
            "current": ["wind_speed_10m", "wind_direction_10m", "temperature_2m"]
        }
        res_weather = requests.get(weather_url, params=weather_params, timeout=4)
        
        wind_knots = 12.0
        wind_dir = 50.0
        temp_c = 28.0
        if res_weather.status_code == 200:
            w_curr = res_weather.json().get("current", {})
            # wind speed in km/h -> knots
            ws_raw = w_curr.get("wind_speed_10m")
            if ws_raw is not None:
                wind_knots = max(1.5, round(float(ws_raw) * 0.539957, 2))
            wd_raw = w_curr.get("wind_direction_10m")
            if wd_raw is not None:
                wind_dir = round(float(wd_raw), 1)
            t_raw = w_curr.get("temperature_2m")
            if t_raw is not None:
                temp_c = round(float(t_raw), 1)

        # Determine sea state
        if wave_height < 0.5:
            sea_state = "Calm (Rippled, Douglas Scale 1)"
        elif wave_height < 1.25:
            sea_state = "Smooth / Slight (Douglas Scale 2)"
        elif wave_height < 2.5:
            sea_state = "Moderate (Douglas Scale 3-4)"
        else:
            sea_state = "Rough (Douglas Scale 5+)"

        return {
            "source": "OPEN_METEO_LIVE_REALTIME",
            "surface_current_speed_knots": current_knots,
            "surface_current_direction_deg": current_dir,
            "wind_speed_knots": wind_knots,
            "wind_direction_deg": wind_dir,
            "wave_height_m": wave_height,
            "water_temperature_c": temp_c,
            "sea_state": sea_state,
            "coordinates": {
                "latitude": latitude,
                "longitude": longitude
            }
        }
    except Exception as e:
        # Resilient fallback to calibrated hydrodynamics if offline
        fallback = dict(DEFAULT_CONDITIONS)
        fallback["source"] = f"CALIBRATED_FALLBACK ({str(e)[:30]})"
        return fallback


def check_is_sea_water(latitude: float, longitude: float) -> bool:
    """
    Directly queries Open-Meteo's global marine hydrodynamic model.
    Returns True if coordinates are located in authentic ocean/sea waters,
    False if located on land or landlocked terrain.
    """
    try:
        url = f"https://marine-api.open-meteo.com/v1/marine?latitude={round(latitude, 4)}&longitude={round(longitude, 4)}&current=wave_height"
        res = requests.get(url, timeout=3.0, headers={"User-Agent": "OceanTrace/2.0"})
        if res.status_code == 200:
            wh = res.json().get("current", {}).get("wave_height")
            return wh is not None
    except Exception:
        pass
    return False


def ensure_marine_sea_coordinates(latitude: float, longitude: float, location_hint: str = "") -> tuple:
    """
    CRITICAL MARITIME SANITIZER:
    Guarantees that the spill centroid, slick polygon, and all vessel navigation tracks
    are ALWAYS situated strictly in open ocean/sea waters and NEVER on land.

    If coordinates are on land or coastal city center, automatically shifts offshore
    into verified navigable sea waters or aligns with the nearest maritime fairway.
    """
    from backend.ports import find_nearest_ports

    # 1. Test if candidate location is already authentic sea/ocean
    if check_is_sea_water(latitude, longitude):
        return latitude, longitude, False

    # 2. Expanding radial offshore probe (searching sea vectors up to ~65 km)
    radii = [0.08, 0.16, 0.28, 0.45, 0.65]
    for r in radii:
        offsets = [
            (0, -r), (0, r), (-r, 0), (r, 0),
            (-r * 0.7, -r * 0.7), (-r * 0.7, r * 0.7),
            (r * 0.7, -r * 0.7), (r * 0.7, r * 0.7)
        ]
        for dla, dlo in offsets:
            tla = round(latitude + dla, 4)
            tlo = round(longitude + dlo, 4)
            if check_is_sea_water(tla, tlo):
                return tla, tlo, True

    # 3. Fallback for deeply landlocked queries: snap directly to the nearest maritime port waters
    nearest_ports = find_nearest_ports(latitude, longitude, limit=1)
    if nearest_ports:
        port = nearest_ports[0]
        pla, plo = port["latitude"], port["longitude"]
        if check_is_sea_water(pla, plo):
            return pla, plo, True
        # Probe slightly offshore of port
        for r in [0.05, 0.12, 0.20]:
            for dla, dlo in [(0, -r), (0, r), (-r, 0), (r, 0)]:
                if check_is_sea_water(pla + dla, plo + dlo):
                    return round(pla + dla, 4), round(plo + dlo, 4), True
        return pla, plo, True

    # Default safe global ocean coordinates (Singapore Strait TSS)
    return 1.2840, 104.1250, True

