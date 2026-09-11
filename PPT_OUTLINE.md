# OCEANTRACE: Presentation Deck Outline (10 Slides)

Use this complete slide-by-slide structure for PowerPoint / Google Slides. Each slide includes the exact on-screen bullet points and the word-for-word speaker script.

---

### Slide 1: Title & Hook
- **Slide Title**: OCEANTRACE
- **Subtitle**: Automated Satellite SAR Marine Oil Spill Detection, Hydrodynamic Drift Hindcasting & AIS Vessel Attribution Platform
- **Team**: [Your Team Name] | [Hackathon Track]
- **Speaker Script**:
  > "Good morning, respected judges. Every year, over 1.3 million tonnes of petroleum enter the oceans, much of it from illicit bilge-dumping and tank washing by merchant ships operating in international waters. Because these discharges occur offshore under cover of night or cloud cover, they remain un-attributable. Today, we present OCEANTRACE—an intelligent surveillance platform that bridges satellite radar remote sensing with historical AIS vessel tracking to identify and attribute the polluting vessels with explainable evidence."

---

### Slide 2: The Problem: Maritime Attribution Blindspot
- **Bullet Points**:
  - **Offshore Invisibility**: Optical satellites are blocked by clouds and darkness; conventional patrols cover less than 5% of economic zones.
  - **Dynamic Ocean Drift**: By the time a slick is spotted, ocean currents and winds have displaced it tens of kilometers from where it was released.
  - **Dense Marine Traffic**: In congested straits (like Singapore, Malacca, or Hormuz), hundreds of vessels pass daily, creating a needle-in-a-haystack attribution problem.
- **Speaker Script**:
  > "The fundamental hurdle isn't just seeing the spill—it's that oil moves. A slick observed today was dumped 6 to 12 hours ago miles away. Without backtracking drift physics and reconstructing past vessel traffic, authorities cannot legally hold polluters accountable."

---

### Slide 3: Our Solution: The OCEANTRACE Pipeline
- **Bullet Points**:
  - **1. SAR Dark Patch Extraction**: Ingests Sentinel-1 all-weather Synthetic Aperture Radar imagery to segment slicks and compute geometry.
  - **2. Hydrodynamic Drift Engine**: Reverse-simulates ocean currents and wind leeway to pinpoint the exact origin coordinates and time window.
  - **3. AIS Traffic Reconstruction**: Queries historical AIS transponder tracks to extract all transiting vessels within the origin window.
  - **4. 5-Factor Attribution Scoring**: Ranks suspect vessels using explainable kinematics, proximity, ship profiles, and behavioral anomalies.
- **Speaker Script**:
  > "We developed an end-to-end automated pipeline that connects the observation back to the offender in four deterministic, mathematically validated stages."

---

### Slide 4: Satellite SAR Slick Characterization
- **Bullet Points**:
  - **Radar Physics**: Oil dampens capillary and gravity ocean waves, reducing radar backscatter and appearing as characteristic dark patches on C-band SAR.
  - **Geometric Metrics**:
    - Surface Area ($14.82 \text{ km}^2$) using spherical Shoelace formulation
    - Perimeter ($26.4 \text{ km}$) and elongation orientation ($68.5^\circ$)
  - **Weathering Model**: Estimates slick age based on Fay's spreading phases, evaporation rates, and emulsification state.
- **Speaker Script**:
  > "By measuring the geometry and spreading phase of the slick, our engine accurately estimates the age of the slick—in our demo case, approximately 6.5 hours old. This age estimate is what unlocks the reverse drift calculation."

---

### Slide 5: Hydrodynamic Drift Physics (Hindcasting & Forecasting)
- **Bullet Points**:
  - **Vector Leeway Equation**:
    $$\vec{V}_{\text{drift}} = \vec{V}_{\text{current}} + 0.032 \cdot \vec{V}_{\text{wind}}$$
  - **Coriolis Deflection**: $+12^\circ$ rightward angular deflection in Northern Hemisphere.
  - **Lagrangian Backward Hindcast**: Integrates environmental vectors in reverse:
    $$(x_{\text{origin}}, y_{\text{origin}}) = (x_{\text{slick}}, y_{\text{slick}}) - \int_{0}^{T_{\text{age}}} \vec{V}_{\text{drift}} dt$$
  - **Forward Forecast**: Projects 12-hour future drift to protect coastal habitats.
- **Speaker Script**:
  > "Rather than using a black-box model, we implemented the internationally standardized 3% wind leeway rule with Coriolis deflection used by NOAA and the IMO. Tracing backward 6.5 hours from the slick reveals the true origin: 1.348° N, 104.262° E between 07:30 and 08:30 UTC."

---

### Slide 6: AIS Spatio-Temporal Traffic Filtering
- **Bullet Points**:
  - **Bounding Box Query**: Filters global AIS traffic down to vessels present in the origin search zone.
  - **Closest Point of Approach (CPA)**: Computes the precise minute and distance at which each vessel passed the estimated origin.
  - **Relational SQL Architecture**: SQLite database indexed on MMSI, timestamp, and latitude/longitude coordinates.
- **Speaker Script**:
  > "Next, our database engine reconstructs all vessel tracks that passed within 15 km of that origin during the 2-hour release window. Out of hundreds of ships in the region, only 5 crossed this spatio-temporal boundary."

---

### Slide 7: Explainable 5-Factor Attribution Algorithm
- **Formula**:
  $$\text{Score} = 35\%(\text{Proximity}) + 25\%(\text{Time}) + 20\%(\text{Course Alignment}) + 10\%(\text{Ship Risk}) + 10\%(\text{Anomalies})$$
- **Breakdown**:
  - **Proximity (35%)**: CPA distance to origin centroid.
  - **Temporal (25%)**: Alignment with release time window.
  - **Trajectory (20%)**: Vessel heading vs. slick elongation axis.
  - **Vessel Type (10%)**: Crude VLCC vs. Container vs. Tug.
  - **Behavioral Anomaly (10%)**: Speed drops, loitering, AIS transponder gaps.
- **Speaker Script**:
  > "Judges, this is our core innovation. We evaluate 5 distinct dimensions. In a court of law or maritime tribunal, a black box neural net is inadmissible. Our system produces an itemized forensic evidence dossier that officers can immediately verify."

---

### Slide 8: Live Demonstration & Results
- **Bullet Points**:
  - **Tactical Maritime Interface**: Dark naval surveillance dashboard built with Leaflet.js and Vanilla JS.
  - **Top Suspect Identified**: *VALKYRIE STAR* (MMSI: 352001948, Crude Oil Tanker VLCC).
    - Passed within **0.57 km** of origin.
    - Passed within **42 mins** of estimated release.
    - **Anomalous 52% speed drop** (from 14.1 to 6.8 kt) and **36-minute AIS gap**.
    - Final Attribution Score: **92.1% (High Potential Source)**.
- **Speaker Script**:
  > *[Switch to browser / live app]* 'Here on our live tactical map, you see the red SAR slick, the orange dashed hindcast line, and the origin circle. Notice how the track of VALKYRIE STAR directly intersects the origin point, right when its speed dropped abnormally. Clicking on the ship opens the forensic dossier showing the complete score breakdown.'"

---

### Slide 9: Tech Stack & Production Scalability
- **Bullet Points**:
  - **Decoupled, Lightweight Architecture**: Python 3.11 FastAPI backend + Vanilla JS/HTML5/CSS3 frontend.
  - **Zero Black-Box Overhead**: Pure mathematical modeling that runs in sub-second response times without requiring GPU clusters.
  - **Real-World API Ready**: Plug-in hooks for live `AISStream.io` WebSocket stream and `Open-Meteo` marine currents.
  - **Instant Cloud Deployment**: Live on Render / GitHub Pages.
- **Speaker Script**:
  > "By choosing FastAPI and vanilla web technologies over bloated frameworks, our system boots in 1.2 seconds, requires zero GPU infrastructure, and can be deployed onto a patrol boat's onboard laptop or a national coast guard server."

---

### Slide 10: Conclusion & Next Steps
- **Bullet Points**:
  - **Summary**: An operational, explainable tool that closes the loop between satellite remote sensing and maritime law enforcement.
  - **Future Roadmap**:
    - Integration with Copernicus Sentinel Hub API for automated scheduled orbits.
    - Ingestion of Global Fishing Watch historical dark vessel data.
    - Automated generation of IMO MARPOL Annex I violation PDF reports.
  - **Thank You**: We are now open for your questions!
- **Speaker Script**:
  > "OCEANTRACE transforms raw satellite pixels and raw AIS coordinates into actionable maritime legal evidence. Thank you, and we welcome your questions!"
