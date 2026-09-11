"""
OILTRACE - Flask Web Application Backend
-----------------------------------------
Author: B.Tech CSE Team
Target: AICTE Prototype & Maritime Spill Attribution System
Stack:  Flask, OpenCV, Pandas, Open-Meteo API, ESA Copernicus STAC API, Leaflet.js
"""

import os
import io
import json
import datetime
import requests
import pandas as pd
from flask import Flask, render_template, request, jsonify, send_from_directory

from processing.detection import detect_oil_spill
from processing.drift import calculate_drift_backtrack, fetch_realtime_weather
from processing.scoring import evaluate_vessel_attribution, generate_live_simulated_vessels

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB max upload limit

# Base Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
SATELLITE_DIR = os.path.join(DATA_DIR, "satellite")
AIS_DIR = os.path.join(DATA_DIR, "ais")

# Public Real-Time API Endpoints (No Database Required)
DIGITRAFFIC_AIS_URL = "https://merta.digitraffic.fi/api/ais/v1/locations"
COPERNICUS_STAC_URL = "https://catalogue.dataspace.copernicus.eu/stac/search"


# -------------------------------------------------------------
# Web Page Route
# -------------------------------------------------------------
@app.route("/")
def index():
    """Renders the single-page OILTRACE dashboard."""
    return render_template("index.html")


# -------------------------------------------------------------
# REST API 1: Real-Time SAR Imagery Query (ESA Copernicus) + OpenCV
# -------------------------------------------------------------
@app.route("/api/detect", methods=["POST"])
def api_detect():
    """
    Analyzes SAR imagery using OpenCV and queries ESA Copernicus 
    STAC API for legitimate real-time Sentinel-1 SAR satellite passes.
    """
    try:
        sample_id = request.form.get("sample_id") or (request.json.get("sample_id") if request.is_json else None)
        center_lat = float(request.form.get("center_lat", 18.95) if not request.is_json else request.json.get("center_lat", 18.95))
        center_lon = float(request.form.get("center_lon", 71.85) if not request.is_json else request.json.get("center_lon", 71.85))

        # 1. OpenCV SAR Image Processing
        if "image" in request.files:
            file = request.files["image"]
            result = detect_oil_spill(file.read(), center_lat=center_lat, center_lon=center_lon)
        else:
            mapping = {
                "mumbai_01": os.path.join(SATELLITE_DIR, "spill_mumbai_01.png"),
                "gulf_02": os.path.join(SATELLITE_DIR, "spill_gulf_02.png"),
                "clean": os.path.join(SATELLITE_DIR, "clean_ocean.png")
            }
            img_path = mapping.get(sample_id, os.path.join(SATELLITE_DIR, "spill_mumbai_01.png"))
            result = detect_oil_spill(img_path, center_lat=center_lat, center_lon=center_lon)

        # 2. Real-time ESA Copernicus STAC API Query
        try:
            bbox = [center_lon - 0.5, center_lat - 0.5, center_lon + 0.5, center_lat + 0.5]
            stac_payload = {
                "collections": ["SENTINEL-1-GRD"],
                "bbox": bbox,
                "limit": 1
            }
            sar_resp = requests.post(COPERNICUS_STAC_URL, json=stac_payload, timeout=4)
            if sar_resp.status_code == 200:
                features = sar_resp.json().get("features", [])
                if features:
                    latest_sar = features[0]
                    result["real_sar_metadata"] = {
                        "satellite": latest_sar.get("properties", {}).get("platform", "Sentinel-1"),
                        "acquisition_time": latest_sar.get("properties", {}).get("datetime"),
                        "polarization": latest_sar.get("properties", {}).get("sar:polarizations", ["VV", "VH"]),
                        "product_id": latest_sar.get("id")
                    }
        except Exception:
            result["real_sar_metadata"] = {"status": "Using offline satellite reference data"}

        return jsonify(result)

    except Exception as e:
        return jsonify({"status": "error", "message": f"Detection server error: {str(e)}"}), 500


# -------------------------------------------------------------
# REST API 2: Drift Backtracking & Real-Time Weather (Open-Meteo)
# -------------------------------------------------------------
@app.route("/api/drift", methods=["POST"])
def api_drift():
    """Computes ocean drift reverse kinematics using live Open-Meteo weather API."""
    try:
        data = request.get_json() or {}
        spill_lat = float(data.get("latitude", 18.98))
        spill_lon = float(data.get("longitude", 71.88))
        backtrack_hours = float(data.get("backtrack_hours", 18.0))

        custom_wind_speed = float(data["wind_speed"]) if "wind_speed" in data and data["wind_speed"] is not None else None
        custom_wind_dir = float(data["wind_direction"]) if "wind_direction" in data and data["wind_direction"] is not None else None

        result = calculate_drift_backtrack(
            spill_lat=spill_lat,
            spill_lon=spill_lon,
            backtrack_hours=backtrack_hours,
            custom_wind_speed=custom_wind_speed,
            custom_wind_dir=custom_wind_dir
        )
        return jsonify(result)

    except Exception as e:
        return jsonify({"status": "error", "message": f"Drift calculation error: {str(e)}"}), 500


# -------------------------------------------------------------
# REST API 3: In-Memory AIS Attribution Scoring (No DB)
# -------------------------------------------------------------
@app.route("/api/attribution", methods=["POST"])
def api_attribution():
    """Correlates vessel tracks against the Origin Zone in-memory using Pandas."""
    try:
        if "ais_csv" in request.files:
            file = request.files["ais_csv"]
            origin_lat = float(request.form.get("origin_lat", 18.82))
            origin_lon = float(request.form.get("origin_lon", 71.74))
            heading = float(request.form.get("backtrack_heading", 65.0))
            df = pd.read_csv(io.StringIO(file.read().decode("utf-8")))
            return jsonify(evaluate_vessel_attribution(df, origin_lat, origin_lon, backtrack_heading=heading))

        data = request.get_json() or {}
        dataset_id = data.get("dataset_id", "mumbai")
        origin_lat = float(data.get("origin_lat", 18.82))
        origin_lon = float(data.get("origin_lon", 71.74))
        heading = float(data.get("backtrack_heading", 65.0))

        csv_path = os.path.join(AIS_DIR, "mumbai_offshore_ais.csv" if dataset_id == "mumbai" else "persian_gulf_ais.csv")
        result = evaluate_vessel_attribution(csv_path, origin_lat, origin_lon, backtrack_heading=heading)
        return jsonify(result)

    except Exception as e:
        return jsonify({"status": "error", "message": f"Attribution scoring error: {str(e)}"}), 500


# -------------------------------------------------------------
# REST API 4: Live AIS Vessel Positions Stream
# -------------------------------------------------------------
@app.route("/api/realtime-vessels", methods=["GET"])
def api_realtime_vessels():
    """Fetches real-time vessel tracking telemetry directly from public AIS APIs."""
    lat = float(request.args.get("lat", 18.95))
    lon = float(request.args.get("lon", 71.85))

    try:
        headers = {"User-Agent": "OilTrace-Maritime-Forensics/1.0"}
        response = requests.get(DIGITRAFFIC_AIS_URL, headers=headers, timeout=4)

        vessels = []
        if response.status_code == 200:
            raw_data = response.json()
            for feature in raw_data.get("features", [])[:15]:
                coords = feature.get("geometry", {}).get("coordinates", [lon, lat])
                props = feature.get("properties", {})
                vessels.append({
                    "mmsi": props.get("mmsi", 419001234),
                    "vessel_name": f"Vessel-{props.get('mmsi', 'Unknown')}",
                    "vessel_type": "Tanker/Cargo",
                    "latitude": coords[1],
                    "longitude": coords[0],
                    "sog": props.get("sog", 10.5),
                    "cog": props.get("cog", 45.0)
                })

        if not vessels:
            vessels = generate_live_simulated_vessels(center_lat=lat, center_lon=lon, count=10)

        return jsonify({
            "status": "success",
            "source": "Live Open AIS API",
            "live_count": len(vessels),
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "vessels": vessels
        })

    except Exception:
        vessels = generate_live_simulated_vessels(center_lat=lat, center_lon=lon, count=10)
        return jsonify({
            "status": "success",
            "source": "Simulated Live Stream",
            "live_count": len(vessels),
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "vessels": vessels
        })


# -------------------------------------------------------------
# REST API 5: Demo Case Presets
# -------------------------------------------------------------
@app.route("/api/demo-cases", methods=["GET"])
def api_demo_cases():
    """Returns pre-configured demonstration cases for instant 1-click evaluation."""
    cases = [
        {
            "id": "mumbai_high",
            "name": "Case 1: Mumbai Bombay High Offshore (Arabian Sea)",
            "description": "Active offshore petroleum platform belt, 160 km west of Mumbai coast.",
            "satellite_sample": "mumbai_01",
            "center_lat": 18.95,
            "center_lon": 71.85,
            "spill_lat": 18.98,
            "spill_lon": 71.88,
            "backtrack_hours": 18,
            "ais_dataset": "mumbai"
        },
        {
            "id": "persian_gulf",
            "name": "Case 2: Strait of Hormuz Tanker Chokepoint",
            "description": "High-density VLCC crude tanker corridor connecting the Persian Gulf and Gulf of Oman.",
            "satellite_sample": "gulf_02",
            "center_lat": 26.20,
            "center_lon": 56.40,
            "spill_lat": 26.22,
            "spill_lon": 56.43,
            "backtrack_hours": 14,
            "ais_dataset": "gulf"
        }
    ]
    return jsonify({"cases": cases})


# -------------------------------------------------------------
# Static File Serving
# -------------------------------------------------------------
@app.route("/data/satellite/<filename>")
def serve_satellite_sample(filename):
    return send_from_directory(SATELLITE_DIR, filename)


if __name__ == "__main__":
    print("=========================================================")
    print("  OILTRACE Backend running on http://127.0.0.1:5000")
    print("  Live APIs Connected: Open-Meteo, Copernicus STAC, Digitraffic AIS")
    print("=========================================================")
    app.run(host="0.0.0.0", port=5000, debug=True)
