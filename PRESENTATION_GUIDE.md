# 🎓 OILTRACE: AICTE & B.Tech CSE Viva Presentation Defense Guide

> **Created for:** 1st Semester B.Tech Computer Science & Engineering Students  
> **Target Audience:** AICTE Evaluators, Senior University Professors, and Hackathon Judges  
> **Project Title:** OILTRACE – Real-Time Satellite Oil Spill Detection & Forensic Vessel Attribution System

---

## ⚡ 1. The 60-Second Elevator Pitch

> *"Good morning, respected judges. We are presenting **OILTRACE**, an explainable maritime forensic intelligence prototype. 
> 
> When an illegal oil discharge or tanker leak occurs in the ocean, maritime authorities typically spot it hours or days later. By then, the discharging vessel is already dozens of nautical miles away. 
> 
> OILTRACE solves this by connecting two worlds:
> 1. **Spaceborne Earth Observation:** We process Synthetic Aperture Radar (SAR) satellite imagery using OpenCV to extract low-backscatter oil slick geometries and calculate exact spill areas in km².
> 2. **Physical Kinematic Backtracking:** Using real-time meteorological wind data from the open-source Open-Meteo API, we reverse-simulate the ocean drift vector back in time to establish a **Probable Origin Zone**.
> 3. **AIS Spatial-Temporal Correlation:** We ingest maritime Automatic Identification System (AIS) trajectories using Pandas, compute great-circle Haversine distances, and generate an explainable, weighted attribution score to rank suspect vessels by **Investigation Priority**.
> 
> Our system does not make reckless legal accusations; instead, it delivers a transparent, mathematically grounded audit trail for Coast Guard and Port State Control authorities."*

---

## 🧠 2. Mathematical & Algorithmic Concepts (Explained Simply)

### A. Satellite Radar Image Processing (OpenCV)
- **The Physics:** Synthetic Aperture Radar (SAR) satellites (e.g., ESA Sentinel-1) pulse radar beams down to the ocean.
  - Normal sea has capillary waves, scattering radar back in all directions $\rightarrow$ appears **bright / textured**.
  - Oil dampens these surface ripples, acting like a mirror (specular reflection) $\rightarrow$ radar bounces away $\rightarrow$ appears as a **dark patch**.
- **The Pipeline:**
  1. `cv2.cvtColor()` $\rightarrow$ Grayscale single-channel radar intensity.
  2. `cv2.GaussianBlur(k=7)` $\rightarrow$ Attenuates high-frequency SAR speckle noise.
  3. `cv2.threshold(THRESH_BINARY_INV + THRESH_OTSU)` $\rightarrow$ Otsu’s algorithm automatically calculates the optimal intensity threshold separating dark oil from background water by maximizing inter-class variance.
  4. `cv2.morphologyEx()` $\rightarrow$ Morphological opening (erosion + dilation) removes isolated wave noise; morphological closing bridges interior gaps.
  5. `cv2.findContours()` $\rightarrow$ Extracts vector boundary contours and computes pixel surface area, converted to $\text{km}^2$ via Ground Sampling Distance (GSD).

### B. Reverse Kinematic Drift Backtracking (Physics & Meteorology)
- **Leeway Law:** Surface oil moves downwind at approximately $3.0\% \text{ to } 3.5\%$ of the $10\text{m}$ wind velocity ($V_{\text{wind}}$), superimposed on local ocean surface currents ($V_{\text{current}}$):
  $$V_{\text{drift}} = (0.031 \cdot V_{\text{wind}}) + V_{\text{current}}$$
- **Reverse Kinematics:** To locate where the oil was released $T$ hours ago:
  $$\vec{X}_{\text{origin}}(t - \Delta t) = \vec{X}_{\text{spill}}(t) - \vec{V}_{\text{drift}} \cdot \Delta t$$
- **Uncertainty Cone:** Due to oceanic turbulent eddy diffusion, the spatial uncertainty expands over time:
  $$R_{\text{error}}(t) = R_0 + 0.12 \sqrt{t + 1} \cdot D_{\text{drift}}$$

### C. Great-Circle Distance (Haversine Formula)
To compute precise distances between coordinates on the spherical Earth:
$$a = \sin^2\left(\frac{\Delta \phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta \lambda}{2}\right)$$
$$d = 2 R \cdot \text{atan2}\left(\sqrt{a}, \sqrt{1-a}\right)$$
*(where $R = 6371\text{ km}$, $\phi$ is latitude in radians, $\lambda$ is longitude in radians)*.

### D. Explainable Multi-Factor Attribution Matrix
$$\text{Score} = (0.40 \times S_{\text{spatial}}) + (0.30 \times S_{\text{temporal}}) + (0.20 \times S_{\text{trajectory}}) + (0.10 \times S_{\text{maneuver}})$$

| Factor | Weight | Evaluation Criteria |
| :--- | :---: | :--- |
| **Spatial Proximity ($S_{\text{spatial}}$)** | **40%** | Minimum Haversine distance from vessel trajectory to Origin Zone centroid. $d \le 1\text{ km} \rightarrow 100\%$, decaying exponentially. |
| **Temporal Overlap ($S_{\text{temporal}}$)** | **30%** | Time difference $|\Delta t|$ between vessel transit and estimated discharge hour. $|\Delta t| \le 1\text{h} \rightarrow 100\%$. |
| **Trajectory Alignment ($S_{\text{trajectory}}$)** | **20%** | Angular deviation between vessel Course Over Ground (COG) and backtrack axis. |
| **Speed & Maneuver ($S_{\text{maneuver}}$)** | **10%** | Anomaly detection for loitering (speed dropping to 2–6 knots in open water during transit). |

---

## 🛡️ 3. How to Answer Tough Judge Questions

### Q1: "Why didn't you use a Deep Learning model like YOLOv8 or CNN?"
> **Your Answer:**  
> *"In maritime pollution forensics and legal tribunals (such as the UNCLOS International Tribunal for the Law of the Sea), black-box neural networks face strict admissibility scrutiny because weights are unexplainable. 
> 
> OpenCV’s deterministic radiometric segmentation, combined with Otsu's thresholding and physical leeway vectors, provides a 100% mathematically transparent, repeatable, and verifiable audit trail. Furthermore, this approach runs smoothly in real-time on standard servers without requiring heavy GPU infrastructure."*

### Q2: "Why do you label vessels as 'Investigation Priority' instead of 'Guilty'?"
> **Your Answer:**  
> *"Under the International Convention for the Prevention of Pollution from Ships (MARPOL Annex I), an automated software system cannot make a judicial verdict of guilt. 
> 
> Our system produces **forensic correlative evidence** to prioritize boarding and port inspections. Labeling vessels as 'Priority 1 (Critical Investigation)' adheres to proper maritime law protocol and prevents legal liability."*

### Q3: "What makes your project real-time?"
> **Your Answer:**  
> *"We integrated the open-source Open-Meteo Marine API, which queries live 10-meter wind speed and direction vectors at the spill coordinates in real time with zero API key dependencies. This live meteorological vector directly drives our kinematic drift backtracking algorithm on the Leaflet map."*

### Q4: "How will you scale this if deployed by AICTE or the Indian Coast Guard?"
> **Your Answer:**  
> *"Our architecture is strictly modular into 4 compartments (`detection.py`, `drift.py`, `scoring.py`, and `app.py`). 
> - The backend can be containerized on cloud servers (e.g. Render, Railway, AWS).
> - Satellite imagery can be ingested automatically via ESA Copernicus Open Access API.
> - AIS data can transition from CSV ingestion to streaming Kafka/WebSocket feeds directly from DG Shipping or Indian Navy Information Fusion Centre (IFC-IOR)."*

---

## 🎯 4. Demo Flow for the Presentation

1. **Start on Dark Mode:** Highlight the interactive Leaflet map and live Open-Meteo wind reading in the top banner.
2. **Click "Run End-to-End Pipeline":**
   - Show the step-by-step progression:
     1. OpenCV highlights the oil slick in red ($49.7\text{ km}^2$).
     2. Open-Meteo live wind is fetched.
     3. Amber Probable Origin Zone and cyan drift trajectory appear.
     4. Vessel tracks are rendered on the map.
     5. Top candidate (`MT ARYAVART`) is highlighted in red with an $87\%$ correlation score.
3. **Switch to Attribution Tab:** Point to the **Chart.js Radar Chart** to explain the 4-factor breakdown (Spatial, Temporal, Trajectory, Maneuver).
4. **Click the Light Mode Toggle:** Show how the entire UI and Leaflet map seamlessly switch to a clean, high-contrast light theme suitable for formal reports.
5. **Show the "AICTE Guide" tab:** Show that all formulas and answers are built right into the app!
