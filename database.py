"""
backend/database.py
SQLite Database Layer for OCEANTRACE.
Handles incidents, vessel historical AIS data, and attribution logs using clean SQL.
"""

import sqlite3
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

DB_FILE = Path(__file__).resolve().parent.parent / "oceantrace.db"
DEMO_JSON = Path(__file__).resolve().parent.parent / "data" / "demo.json"


def get_connection() -> sqlite3.Connection:
    """Returns a connection to the SQLite database with row factory enabled."""
    conn = sqlite3.connect(str(DB_FILE))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Creates the relational database schema if it doesn't already exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # Table 1: Oil Spill Incidents
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS incidents (
        incident_id TEXT PRIMARY KEY,
        region_name TEXT NOT NULL,
        sensor_source TEXT NOT NULL,
        detection_timestamp TEXT NOT NULL,
        centroid_lat REAL NOT NULL,
        centroid_lon REAL NOT NULL,
        area_km2 REAL NOT NULL,
        perimeter_km REAL NOT NULL,
        estimated_age_hours REAL NOT NULL,
        estimated_origin_lat REAL,
        estimated_origin_lon REAL,
        estimated_origin_time TEXT,
        raw_polygon_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Table 2: Vessels Registry
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vessels (
        mmsi INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        vessel_type TEXT NOT NULL,
        imo INTEGER,
        callsign TEXT,
        flag TEXT,
        length_m REAL,
        width_m REAL,
        dwt REAL,
        anomalies_json TEXT
    );
    """)

    # Table 3: Historic AIS Trajectory Points
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ais_tracks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mmsi INTEGER NOT NULL,
        timestamp TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        speed_knots REAL NOT NULL,
        course_deg REAL NOT NULL,
        FOREIGN KEY (mmsi) REFERENCES vessels(mmsi)
    );
    """)

    # Create indexes for fast spatial-temporal searching
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ais_mmsi ON ais_tracks(mmsi);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ais_time ON ais_tracks(timestamp);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ais_lat_lon ON ais_tracks(latitude, longitude);")

    # Table 4: Attribution Results & Evidence Log
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attribution_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        incident_id TEXT NOT NULL,
        mmsi INTEGER NOT NULL,
        rank INTEGER NOT NULL,
        total_score REAL NOT NULL,
        proximity_score REAL NOT NULL,
        temporal_score REAL NOT NULL,
        trajectory_score REAL NOT NULL,
        type_score REAL NOT NULL,
        anomaly_score REAL NOT NULL,
        evidence_summary TEXT NOT NULL,
        evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (incident_id) REFERENCES incidents(incident_id),
        FOREIGN KEY (mmsi) REFERENCES vessels(mmsi)
    );
    """)

    conn.commit()
    conn.close()


def seed_demo_data_if_empty():
    """Seeds the SQLite database from data/demo.json if tables are empty."""
    if not DEMO_JSON.exists():
        return

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM incidents;")
    count = cursor.fetchone()[0]

    if count == 0:
        with open(DEMO_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)

        spill = data["spill_incident"]
        cursor.execute("""
        INSERT INTO incidents (
            incident_id, region_name, sensor_source, detection_timestamp,
            centroid_lat, centroid_lon, area_km2, perimeter_km,
            estimated_age_hours, estimated_origin_lat, estimated_origin_lon, estimated_origin_time, raw_polygon_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            spill["incident_id"],
            spill["region_name"],
            spill["sensor_source"],
            spill["satellite_pass_time"],
            spill["slick_centroid"]["latitude"],
            spill["slick_centroid"]["longitude"],
            spill["geometric_properties"]["area_km2"],
            spill["geometric_properties"]["perimeter_km"],
            spill["weathering_analysis"]["estimated_age_hours"],
            spill["estimated_origin"]["latitude"],
            spill["estimated_origin"]["longitude"],
            spill["estimated_origin"].get("time_window_start", "2026-09-09T08:00:00Z"),
            json.dumps(spill["slick_polygon"])
        ))

        # Insert vessels and trajectory points
        for v in data.get("candidate_vessels", []):
            cursor.execute("""
            INSERT OR REPLACE INTO vessels (
                mmsi, name, vessel_type, imo, callsign, flag, length_m, width_m, dwt, anomalies_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                v["mmsi"], v["name"], v["vessel_type"], v.get("imo"),
                v.get("callsign"), v.get("flag"), v.get("length"),
                v.get("width"), v.get("deadweight_tonnage"),
                json.dumps(v.get("anomalies", []))
            ))

            for pt in v.get("trajectory", []):
                cursor.execute("""
                INSERT INTO ais_tracks (mmsi, timestamp, latitude, longitude, speed_knots, course_deg)
                VALUES (?, ?, ?, ?, ?, ?);
                """, (
                    v["mmsi"], pt["timestamp"], pt["latitude"],
                    pt["longitude"], pt["speed_knots"], pt["course_deg"]
                ))

        conn.commit()

    conn.close()


def get_active_incident() -> Optional[Dict[str, Any]]:
    """Fetches the latest active spill incident from SQL."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM incidents ORDER BY created_at DESC LIMIT 1;")
    row = cursor.fetchone()
    conn.close()
    if row:
        res = dict(row)
        if res.get("raw_polygon_json"):
            res["raw_polygon_json"] = json.loads(res["raw_polygon_json"])
        return res
    return None


def get_all_vessels_with_tracks() -> List[Dict[str, Any]]:
    """Retrieves all registered vessels with their historical track points via SQL join."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM vessels;")
    vessel_rows = cursor.fetchall()

    vessels = []
    for vr in vessel_rows:
        v_dict = dict(vr)
        if v_dict.get("anomalies_json"):
            try:
                v_dict["anomalies"] = json.loads(v_dict["anomalies_json"])
            except Exception:
                v_dict["anomalies"] = []
        else:
            v_dict["anomalies"] = []

        cursor.execute("""
        SELECT timestamp, latitude, longitude, speed_knots, course_deg 
        FROM ais_tracks 
        WHERE mmsi = ? 
        ORDER BY timestamp ASC;
        """, (v_dict["mmsi"],))
        tracks = [dict(tr) for tr in cursor.fetchall()]
        v_dict["trajectory"] = tracks
        vessels.append(v_dict)

    conn.close()
    return vessels


def load_incident_scenario(scenario: Dict[str, Any]):
    """Loads a full scenario (spill incident + candidate vessels) into the database."""
    conn = get_connection()
    cursor = conn.cursor()

    # Clear old active session data
    cursor.execute("DELETE FROM ais_tracks;")
    cursor.execute("DELETE FROM vessels;")
    cursor.execute("DELETE FROM incidents;")

    spill = scenario["spill_incident"]
    cursor.execute("""
    INSERT OR REPLACE INTO incidents (
        incident_id, region_name, sensor_source, detection_timestamp,
        centroid_lat, centroid_lon, area_km2, perimeter_km,
        estimated_age_hours, estimated_origin_lat, estimated_origin_lon, estimated_origin_time, raw_polygon_json
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        spill["incident_id"],
        spill["region_name"],
        spill["sensor_source"],
        spill["satellite_pass_time"],
        spill["slick_centroid"]["latitude"],
        spill["slick_centroid"]["longitude"],
        spill["geometric_properties"]["area_km2"],
        spill["geometric_properties"]["perimeter_km"],
        spill["weathering_analysis"]["estimated_age_hours"],
        spill["estimated_origin"]["latitude"],
        spill["estimated_origin"]["longitude"],
        spill["estimated_origin"].get("time_window_start", "2026-09-09T08:00:00Z"),
        json.dumps(spill.get("slick_polygon", []))
    ))

    for v in scenario.get("candidate_vessels", []):
        cursor.execute("""
        INSERT OR REPLACE INTO vessels (
            mmsi, name, vessel_type, imo, callsign, flag, length_m, width_m, dwt, anomalies_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            v["mmsi"], v["name"], v["vessel_type"], v.get("imo"),
            v.get("callsign"), v.get("flag"), v.get("length"),
            v.get("width"), v.get("deadweight_tonnage"),
            json.dumps(v.get("anomalies", []))
        ))

        for pt in v.get("trajectory", []):
            cursor.execute("""
            INSERT INTO ais_tracks (mmsi, timestamp, latitude, longitude, speed_knots, course_deg)
            VALUES (?, ?, ?, ?, ?, ?);
            """, (
                v["mmsi"], pt["timestamp"], pt["latitude"],
                pt["longitude"], pt["speed_knots"], pt["course_deg"]
            ))

    conn.commit()
    conn.close()

