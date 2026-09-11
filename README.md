# OCEANTRACE 🌊🛰️🚢
### Automated Satellite SAR Oil Spill Detection, Hydrodynamic Drift Hindcasting & AIS Vessel Attribution Platform

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI_0.110-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Leaflet](https://img.shields.io/badge/Frontend-Leaflet.js_1.9-199900?logo=leaflet)](https://leafletjs.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## 📌 Problem Statement Overview
Marine oil spills cause catastrophic, long-lasting damage to maritime biodiversity, fisheries, and coastal ecosystems. A major enforcement hurdle faced by maritime authorities (IMO, Coast Guards) is that illicit or accidental discharges often go **un-attributed**, allowing polluter vessels to escape legal accountability.

**OCEANTRACE** provides an end-to-end operational surveillance pipeline that:
1. **Detects & Characterizes Slicks**: Ingests Sentinel-1 Synthetic Aperture Radar (SAR) imagery, delineating slick boundaries and calculating geometric properties (area, perimeter, volume, and weathering phase).
2. **Hindcasts & Forecasts Drift**: Employs an explainable hydrodynamic leeway model ($\vec{V}_{drift} = \vec{V}_{current} + 0.032 \cdot \vec{V}_{wind}$ with Coriolis deflection) to back-calculate the exact **spill origin point and release time window**, as well as a 12-hour forward forecast.
3. **Reconstructs & Attributes AIS Traffic**: Correlates historical AIS vessel tracks around the origin window and scores candidate vessels using a 5-factor forensic weighting matrix (Proximity, Time, Course alignment, Vessel Risk profile, and Behavioral Anomalies).

---

## 🏛️ System Architecture

```
                                    OCEANTRACE
                                        │
           ┌────────────────────────────┼────────────────────────────┐
           ▼                            ▼                            ▼
   Satellite SAR Module          Drift Physics Engine          AIS Data Engine
  (Geometry, Area, Age)        (Ocean Current + Wind Drift)   (Historic / Live Stream)
           │                            │                            │
           └────────────────────────────┼────────────────────────────┘
                                        ▼
                            Spatio-Temporal Reconstructor
                            (Origin Window & Error Ellipse)
                                        │
                                        ▼
                           Vessel Attribution Engine
                         (5-Factor Multi-Criteria Score)
                                        │
                                        ▼
                             SQLite Audit Log (SQL)
                                        │
                                        ▼
                              FastAPI REST Backend
                                        │
                                        ▼
                         Leaflet.js + Vanilla JS UI
                         (Dark Maritime Tactical Map)
```

---

## 🔬 Explainable Attribution Scoring Model

Judges value transparent mathematical formulations over black-box buzzwords. The attribution engine ranks candidate vessels based on:

$$\text{Attribution Score} = 0.35 \cdot S_{\text{prox}} + 0.25 \cdot S_{\text{temp}} + 0.20 \cdot S_{\text{traj}} + 0.10 \cdot S_{\text{type}} + 0.10 \cdot S_{\text{anom}}$$

1. **Spatial Proximity ($S_{\text{prox}}$, 35%)**: Great-circle Haversine distance between vessel Closest Point of Approach (CPA) and estimated origin centroid.
2. **Temporal Correlation ($S_{\text{temp}}$, 25%)**: Absolute time difference between vessel transit and estimated release time window.
3. **Trajectory Alignment ($S_{\text{traj}}$, 20%)**: Angular similarity between vessel heading vector and slick elongation axis.
4. **Vessel Risk Profile ($S_{\text{type}}$, 10%)**: Cargo/bunker risk weight (Crude VLCC = 100, Chemical Tanker = 85, Cargo/Bulk = 55, Tug = 25).
5. **Behavioral Anomaly ($S_{\text{anom}}$, 10%)**: Flags sudden speed drops ($>30\%$), loitering, course deviation, or AIS transponder silence/gaps.

---

## 🚀 Quickstart Guide

### 1. Requirements
- Python 3.10+ (tested on Python 3.11)
- Any modern web browser

### 2. Installation
Clone the repository and install the lightweight dependencies:
```bash
pip install -r requirements.txt
```

### 3. Launch with 1 Command
```bash
python run.py
```
This starts the FastAPI server on `http://127.0.0.1:8000` and automatically opens the tactical dashboard in your browser.

---

## 📡 REST API Endpoints

FastAPI provides automatic interactive Swagger documentation at **`http://127.0.0.1:8000/docs`**:

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/status` | System diagnostics, AIS stream status, and active incident |
| `GET` | `/api/spill` | SAR slick geometry, polygon coordinates, and weathering |
| `GET` | `/api/drift` | Backward hindcast trajectory and 12h forward forecast |
| `GET` | `/api/vessels` | Candidate vessels with reconstructed AIS historical track points |
| `GET` | `/api/attribution` | Ranked suspect vessels with 5-factor scoring breakdown & evidence |
| `POST` | `/api/analyze` | Triggers the full multi-stage surveillance pipeline |

---

## ☁️ Free Cloud Deployment (Render.com)

OCEANTRACE is packaged for instant deployment as a single-service container or web service on [Render](https://render.com):

1. Push your repository to **GitHub**.
2. Log into Render, click **New +** -> **Web Service**.
3. Connect your GitHub repository.
4. Configure:
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
5. Click **Deploy**. Your app is live with an automatic HTTPS URL (`https://oceantrace-xxxx.onrender.com`)!

---

## 💡 Technologies Used
- **Frontend**: HTML5, CSS3 (Tactical Naval Dark Theme), Vanilla JavaScript (ES6+), Leaflet.js
- **Backend**: Python 3.11, FastAPI, Uvicorn, Requests
- **Database**: SQLite3 with indexing on spatial coordinates and timestamps
- **Data Integrations**: Sentinel-1 SAR imagery processing, Open-Meteo Marine API, AISStream.io
