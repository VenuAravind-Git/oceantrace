"""
backend/presets.py
Pre-calibrated global maritime incident scenarios for OCEANTRACE.
Enables 1-click scenario switching during hackathon presentations.
"""

from typing import Dict, Any, List

PRESETS: Dict[str, Dict[str, Any]] = {
    "singapore_strait": {
        "spill_incident": {
            "incident_id": "SPILL-2026-SG-0492",
            "region_name": "Singapore Strait / Eastern Approaches TSS",
            "sensor_source": "Sentinel-1B SAR C-Band (VV Polarization)",
            "satellite_pass_time": "2026-09-09T14:30:00Z",
            "slick_centroid": {"latitude": 1.2840, "longitude": 104.1250},
            "slick_polygon": [
                [1.2720, 104.0950],
                [1.2890, 104.1120],
                [1.3010, 104.1480],
                [1.2940, 104.1620],
                [1.2780, 104.1390],
                [1.2690, 104.1080],
                [1.2720, 104.0950]
            ],
            "geometric_properties": {
                "area_km2": 14.82,
                "perimeter_km": 26.40,
                "major_axis_length_km": 9.15,
                "minor_axis_length_km": 2.45,
                "orientation_deg": 68.5,
                "estimated_thickness_um": 12.5,
                "estimated_volume_m3": 185.25
            },
            "weathering_analysis": {
                "spreading_state": "Phase III (Weathered Emulsion)",
                "estimated_age_hours": 6.5,
                "evaporation_loss_pct": 32.4,
                "emulsification_pct": 18.0
            },
            "environmental_conditions": {
                "surface_current_speed_knots": 0.75,
                "surface_current_direction_deg": 245.0,
                "wind_speed_knots": 13.5,
                "wind_direction_deg": 55.0,
                "water_temperature_c": 28.5,
                "sea_state": "Slight (Douglas Scale 2)"
            },
            "estimated_origin": {
                "latitude": 1.3480,
                "longitude": 104.2620,
                "time_window_start": "2026-09-09T08:00:00Z",
                "time_window_end": "2026-09-09T08:45:00Z",
                "uncertainty_radius_nm": 1.85
            }
        },
        "candidate_vessels": [
            {
                "mmsi": 352001948,
                "name": "VALKYRIE STAR",
                "vessel_type": "Crude Oil Tanker (VLCC)",
                "imo": 9482011,
                "callsign": "3FXC9",
                "flag": "Panama",
                "length": 333,
                "width": 60,
                "deadweight_tonnage": 305000,
                "closest_point_of_approach": {
                    "distance_km": 0.57,
                    "timestamp": "2026-09-09T08:12:00Z",
                    "latitude": 1.3512,
                    "longitude": 104.2580,
                    "speed_knots": 6.8,
                    "course_deg": 242.0
                },
                "trajectory": [
                    {"timestamp": "2026-09-09T07:15:00Z", "latitude": 1.3980, "longitude": 104.3800, "speed_knots": 14.1, "course_deg": 238.0},
                    {"timestamp": "2026-09-09T07:45:00Z", "latitude": 1.3720, "longitude": 104.3120, "speed_knots": 13.8, "course_deg": 240.0},
                    {"timestamp": "2026-09-09T08:12:00Z", "latitude": 1.3512, "longitude": 104.2580, "speed_knots": 6.8, "course_deg": 242.0},
                    {"timestamp": "2026-09-09T08:48:00Z", "latitude": 1.3320, "longitude": 104.2150, "speed_knots": 7.1, "course_deg": 252.0},
                    {"timestamp": "2026-09-09T09:30:00Z", "latitude": 1.3110, "longitude": 104.1680, "speed_knots": 13.5, "course_deg": 246.0},
                    {"timestamp": "2026-09-09T14:30:00Z", "latitude": 1.1920, "longitude": 103.8850, "speed_knots": 12.8, "course_deg": 248.0}
                ],
                "anomalies": [
                    "Speed dropped 52% (from 14.1 kt to 6.8 kt) near estimated origin point",
                    "AIS transmission gap detected (36 minutes silent between 08:12Z and 08:48Z)",
                    "Sudden 14° course deviation during release window"
                ]
            },
            {
                "mmsi": 477123900,
                "name": "PACIFIC CARRIER",
                "vessel_type": "Chemical / Products Tanker",
                "imo": 9324410,
                "callsign": "VRLO8",
                "flag": "Hong Kong",
                "length": 182,
                "width": 32,
                "deadweight_tonnage": 46000,
                "closest_point_of_approach": {
                    "distance_km": 4.65,
                    "timestamp": "2026-09-09T08:40:00Z",
                    "latitude": 1.3320,
                    "longitude": 104.2980,
                    "speed_knots": 11.8,
                    "course_deg": 245.0
                },
                "trajectory": [
                    {"timestamp": "2026-09-09T07:30:00Z", "latitude": 1.3680, "longitude": 104.3850, "speed_knots": 12.0, "course_deg": 244.0},
                    {"timestamp": "2026-09-09T08:40:00Z", "latitude": 1.3320, "longitude": 104.2980, "speed_knots": 11.8, "course_deg": 245.0},
                    {"timestamp": "2026-09-09T09:50:00Z", "latitude": 1.2950, "longitude": 104.2050, "speed_knots": 11.9, "course_deg": 245.0},
                    {"timestamp": "2026-09-09T14:30:00Z", "latitude": 1.1550, "longitude": 103.8200, "speed_knots": 11.5, "course_deg": 245.0}
                ],
                "anomalies": ["Minor course adjustment for TSS compliance"]
            },
            {
                "mmsi": 371994000,
                "name": "EVER PROSPER",
                "vessel_type": "Container Ship (Ultra Large)",
                "imo": 9811002,
                "callsign": "3E229",
                "flag": "Panama",
                "length": 400,
                "width": 59,
                "deadweight_tonnage": 199000,
                "closest_point_of_approach": {
                    "distance_km": 8.75,
                    "timestamp": "2026-09-09T08:18:00Z",
                    "latitude": 1.3120,
                    "longitude": 104.3200,
                    "speed_knots": 16.4,
                    "course_deg": 240.0
                },
                "trajectory": [
                    {"timestamp": "2026-09-09T07:20:00Z", "latitude": 1.3520, "longitude": 104.4200, "speed_knots": 16.5, "course_deg": 240.0},
                    {"timestamp": "2026-09-09T08:18:00Z", "latitude": 1.3120, "longitude": 104.3200, "speed_knots": 16.4, "course_deg": 240.0},
                    {"timestamp": "2026-09-09T14:30:00Z", "latitude": 1.0500, "longitude": 103.6500, "speed_knots": 15.9, "course_deg": 240.0}
                ],
                "anomalies": []
            }
        ]
    },
    "strait_of_hormuz": {
        "spill_incident": {
            "incident_id": "SPILL-2026-HZ-0118",
            "region_name": "Strait of Hormuz / Persian Gulf Outbound Lane",
            "sensor_source": "Sentinel-1A SAR C-Band (VV Polarization)",
            "satellite_pass_time": "2026-09-08T18:00:00Z",
            "slick_centroid": {"latitude": 26.3150, "longitude": 56.4200},
            "slick_polygon": [
                [26.2980, 56.3950],
                [26.3220, 56.4150],
                [26.3380, 56.4480],
                [26.3290, 56.4620],
                [26.3050, 56.4380],
                [26.2980, 56.3950]
            ],
            "geometric_properties": {
                "area_km2": 21.40,
                "perimeter_km": 31.80,
                "major_axis_length_km": 11.4,
                "minor_axis_length_km": 3.1,
                "orientation_deg": 125.0,
                "estimated_thickness_um": 15.0,
                "estimated_volume_m3": 321.0
            },
            "weathering_analysis": {
                "spreading_state": "Phase III (Viscous Emulsion)",
                "estimated_age_hours": 8.0,
                "evaporation_loss_pct": 38.5,
                "emulsification_pct": 24.0
            },
            "environmental_conditions": {
                "surface_current_speed_knots": 0.90,
                "surface_current_direction_deg": 140.0,
                "wind_speed_knots": 16.0,
                "wind_direction_deg": 310.0,
                "water_temperature_c": 31.2,
                "sea_state": "Moderate"
            },
            "estimated_origin": {
                "latitude": 26.4320,
                "longitude": 56.2950,
                "time_window_start": "2026-09-08T10:00:00Z",
                "time_window_end": "2026-09-08T10:45:00Z",
                "uncertainty_radius_nm": 2.2
            }
        },
        "candidate_vessels": [
            {
                "mmsi": 636019882,
                "name": "AL-BARAKA PEARL",
                "vessel_type": "Crude Oil Tanker (Suezmax)",
                "imo": 9512390,
                "callsign": "A8X92",
                "flag": "Liberia",
                "length": 274,
                "width": 48,
                "deadweight_tonnage": 158000,
                "closest_point_of_approach": {
                    "distance_km": 0.85,
                    "timestamp": "2026-09-08T10:15:00Z",
                    "latitude": 26.4350,
                    "longitude": 56.2980,
                    "speed_knots": 7.2,
                    "course_deg": 138.0
                },
                "trajectory": [
                    {"timestamp": "2026-09-08T09:00:00Z", "latitude": 26.5100, "longitude": 56.1900, "speed_knots": 13.5, "course_deg": 135.0},
                    {"timestamp": "2026-09-08T10:15:00Z", "latitude": 26.4350, "longitude": 56.2980, "speed_knots": 7.2, "course_deg": 138.0},
                    {"timestamp": "2026-09-08T11:30:00Z", "latitude": 26.3500, "longitude": 56.3900, "speed_knots": 13.0, "course_deg": 135.0},
                    {"timestamp": "2026-09-08T18:00:00Z", "latitude": 25.8200, "longitude": 57.1200, "speed_knots": 13.8, "course_deg": 135.0}
                ],
                "anomalies": [
                    "Speed reduction 46% near estimated origin coordinates",
                    "Loitering behavior detected in outbound tanker fairway",
                    "Transponder power modulation flag"
                ]
            },
            {
                "mmsi": 212554000,
                "name": "CYPRUS NAVIGATOR",
                "vessel_type": "LPG Tanker",
                "imo": 9400211,
                "callsign": "5BTR4",
                "flag": "Cyprus",
                "length": 225,
                "width": 36,
                "deadweight_tonnage": 54000,
                "closest_point_of_approach": {
                    "distance_km": 5.9,
                    "timestamp": "2026-09-08T10:40:00Z",
                    "latitude": 26.4100,
                    "longitude": 56.3450,
                    "speed_knots": 14.5,
                    "course_deg": 136.0
                },
                "trajectory": [
                    {"timestamp": "2026-09-08T09:30:00Z", "latitude": 26.4900, "longitude": 56.2300, "speed_knots": 14.5, "course_deg": 136.0},
                    {"timestamp": "2026-09-08T10:40:00Z", "latitude": 26.4100, "longitude": 56.3450, "speed_knots": 14.5, "course_deg": 136.0}
                ],
                "anomalies": []
            }
        ]
    },
    "gulf_of_mexico": {
        "spill_incident": {
            "incident_id": "SPILL-2026-GOM-0831",
            "region_name": "Gulf of Mexico / Mississippi Canyon Sector",
            "sensor_source": "Sentinel-1B SAR C-Band",
            "satellite_pass_time": "2026-09-07T12:00:00Z",
            "slick_centroid": {"latitude": 28.6500, "longitude": -89.4200},
            "slick_polygon": [
                [28.6320, -89.4450],
                [28.6650, -89.4350],
                [28.6780, -89.3950],
                [28.6520, -89.3850],
                [28.6320, -89.4450]
            ],
            "geometric_properties": {
                "area_km2": 9.75,
                "perimeter_km": 18.20,
                "major_axis_length_km": 6.8,
                "minor_axis_length_km": 1.9,
                "orientation_deg": 45.0,
                "estimated_thickness_um": 10.0,
                "estimated_volume_m3": 97.5
            },
            "weathering_analysis": {
                "spreading_state": "Phase II (Viscous Spreading)",
                "estimated_age_hours": 5.0,
                "evaporation_loss_pct": 28.0,
                "emulsification_pct": 12.0
            },
            "environmental_conditions": {
                "surface_current_speed_knots": 0.65,
                "surface_current_direction_deg": 65.0,
                "wind_speed_knots": 11.0,
                "wind_direction_deg": 225.0,
                "water_temperature_c": 29.5,
                "sea_state": "Slight"
            },
            "estimated_origin": {
                "latitude": 28.5820,
                "longitude": -89.5180,
                "time_window_start": "2026-09-07T07:00:00Z",
                "time_window_end": "2026-09-07T07:45:00Z",
                "uncertainty_radius_nm": 1.5
            }
        },
        "candidate_vessels": [
            {
                "mmsi": 368021000,
                "name": "GULF TRADER",
                "vessel_type": "Chemical / Oil Products Tanker",
                "imo": 9618822,
                "callsign": "WDD41",
                "flag": "USA",
                "length": 183,
                "width": 32,
                "deadweight_tonnage": 50000,
                "closest_point_of_approach": {
                    "distance_km": 0.62,
                    "timestamp": "2026-09-07T07:18:00Z",
                    "latitude": 28.5850,
                    "longitude": -89.5140,
                    "speed_knots": 8.1,
                    "course_deg": 62.0
                },
                "trajectory": [
                    {"timestamp": "2026-09-07T06:00:00Z", "latitude": 28.5200, "longitude": -89.6200, "speed_knots": 13.2, "course_deg": 60.0},
                    {"timestamp": "2026-09-07T07:18:00Z", "latitude": 28.5850, "longitude": -89.5140, "speed_knots": 8.1, "course_deg": 62.0},
                    {"timestamp": "2026-09-07T08:30:00Z", "latitude": 28.6500, "longitude": -89.4100, "speed_knots": 13.0, "course_deg": 64.0}
                ],
                "anomalies": [
                    "Speed reduction 38% at origin window",
                    "Intermittent AIS transmission"
                ]
            }
        ]
    }
}
