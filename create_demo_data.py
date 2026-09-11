"""
Script to generate realistic synthetic SAR satellite images and AIS sample CSV files.
These provide immediate, deterministic, and impressive data for the AICTE live demo.
"""

import os
import cv2
import numpy as np
import pandas as pd
import datetime

# Create directories
os.makedirs("data/satellite", exist_ok=True)
os.makedirs("data/ais", exist_ok=True)

# -------------------------------------------------------------
# 1. Generate Synthetic SAR Images
# -------------------------------------------------------------

def create_sar_speckle_background(width=512, height=512, mean_intensity=140):
    """Simulates SAR Rayleigh/Gamma distributed sea surface radar backscatter speckle."""
    # Base sea texture with speckle
    base = np.random.gamma(shape=9.0, scale=mean_intensity / 9.0, size=(height, width)).astype(np.float32)
    # Gentle undulating waves
    x = np.linspace(0, 8 * np.pi, width)
    y = np.linspace(0, 8 * np.pi, height)
    X, Y = np.meshgrid(x, y)
    wave = 15.0 * np.sin(X * 0.5 + Y * 0.3)
    sea = np.clip(base + wave, 20, 245).astype(np.uint8)
    return sea

# Image 1: Mumbai Offshore Spill (Classic irregular dark oil slick)
img1 = create_sar_speckle_background()
# Draw irregular dark slick (oil dampens waves -> values drop to 20-50)
mask1 = np.zeros_like(img1)
# Create realistic amoeba/slick shape
pts1 = np.array([
    [210, 180], [250, 160], [310, 175], [360, 220], [390, 280],
    [370, 330], [310, 350], [250, 340], [200, 300], [180, 240]
], np.int32)
cv2.fillPoly(mask1, [pts1], 255)
# Add a secondary smaller trailing patch
pts1_tail = np.array([[380, 290], [420, 310], [440, 350], [410, 370], [375, 340]], np.int32)
cv2.fillPoly(mask1, [pts1_tail], 255)

# Smooth mask edges
mask1 = cv2.GaussianBlur(mask1, (15, 15), 0)
dark_slick1 = np.random.normal(38, 8, img1.shape).clip(15, 65).astype(np.uint8)
# Composite: where mask is white, place dark oil
alpha1 = (mask1.astype(np.float32) / 255.0)
img1_final = ((1.0 - alpha1) * img1 + alpha1 * dark_slick1).astype(np.uint8)
# Add subtle coordinate grid & annotation
cv2.imwrite("data/satellite/spill_mumbai_01.png", img1_final)
print("Saved data/satellite/spill_mumbai_01.png")

# Image 2: Persian Gulf Elongated Slick (Narrow discharge plume)
img2 = create_sar_speckle_background(mean_intensity=155)
mask2 = np.zeros_like(img2)
pts2 = np.array([
    [140, 290], [190, 270], [260, 240], [340, 200], [420, 160],
    [450, 150], [440, 175], [360, 225], [280, 265], [200, 300], [150, 315]
], np.int32)
cv2.fillPoly(mask2, [pts2], 255)
mask2 = cv2.GaussianBlur(mask2, (19, 19), 0)
dark_slick2 = np.random.normal(32, 6, img2.shape).clip(12, 55).astype(np.uint8)
alpha2 = (mask2.astype(np.float32) / 255.0)
img2_final = ((1.0 - alpha2) * img2 + alpha2 * dark_slick2).astype(np.uint8)
cv2.imwrite("data/satellite/spill_gulf_02.png", img2_final)
print("Saved data/satellite/spill_gulf_02.png")

# Image 3: Clean Ocean (No slicks - used to demonstrate zero false positive)
img3 = create_sar_speckle_background(mean_intensity=145)
cv2.imwrite("data/satellite/clean_ocean.png", img3)
print("Saved data/satellite/clean_ocean.png")

# -------------------------------------------------------------
# 2. Generate Realistic AIS Datasets
# -------------------------------------------------------------

# Dataset 1: Mumbai Bombay High Offshore (Center ~ 18.95°N, 71.85°E)
# Slick observed at: 18.98°N, 71.88°E
# Probable Origin backtracked 18h ago to: 18.82°N, 71.74°E (WSW wind drift)
# We design 4 realistic vessels:
# Vessel 1 (MT ARYAVART - MMSI 419001234): Crude Oil Tanker passing directly through origin zone at T-18h! SOG slows to 4.2 kn.
# Vessel 2 (MV PACIFIC TRADER - MMSI 419005678): Container Ship passing 7.5 km away at T-15h. SOG 14.5 kn steady.
# Vessel 3 (MT OCEAN PEARL - MMSI 419008912): Chemical Tanker passing 16.8 km away.
# Vessel 4 (FV SAGARIKA - MMSI 419003456): Small Fishing Vessel far off (26 km).

now = datetime.datetime.utcnow()
t_origin = now - datetime.timedelta(hours=18)

ais_records_mumbai = []

# Vessel 1: MT ARYAVART (High Priority Suspect - 87% Score)
v1_mmsi = 419001234
v1_name = "MT ARYAVART"
v1_type = "Crude Oil Tanker"
for i, dt_hours in enumerate([-22, -20, -18, -16, -14]):
    t = now + datetime.timedelta(hours=dt_hours)
    # Origin at 18.82, 71.74. At dt_hours = -18, lat=18.822, lon=71.743 (distance ~ 0.3 km!)
    lat = 18.72 + (i * 0.05)
    lon = 71.64 + (i * 0.05)
    sog = 4.2 if i == 2 else 12.8  # Anomalous slow down exactly in zone!
    cog = 45.0
    ais_records_mumbai.append({
        "mmsi": v1_mmsi,
        "vessel_name": v1_name,
        "vessel_type": v1_type,
        "latitude": round(lat, 4),
        "longitude": round(lon, 4),
        "timestamp": t.strftime("%Y-%m-%d %H:%M:%S"),
        "sog": sog,
        "cog": cog
    })

# Vessel 2: MV PACIFIC TRADER (Moderate Suspicion - 64% Score)
v2_mmsi = 419005678
v2_name = "MV PACIFIC TRADER"
v2_type = "Container Ship"
for i, dt_hours in enumerate([-21, -19, -17, -15, -13]):
    t = now + datetime.timedelta(hours=dt_hours)
    lat = 18.70 + (i * 0.06)
    lon = 71.80 + (i * 0.03)  # Misses origin by ~7 km
    sog = 15.2
    cog = 25.0
    ais_records_mumbai.append({
        "mmsi": v2_mmsi,
        "vessel_name": v2_name,
        "vessel_type": v2_type,
        "latitude": round(lat, 4),
        "longitude": round(lon, 4),
        "timestamp": t.strftime("%Y-%m-%d %H:%M:%S"),
        "sog": sog,
        "cog": cog
    })

# Vessel 3: MT OCEAN PEARL (Low Suspicion - 42% Score)
v3_mmsi = 419008912
v3_name = "MT OCEAN PEARL"
v3_type = "Chemical Tanker"
for i, dt_hours in enumerate([-24, -20, -16, -12, -8]):
    t = now + datetime.timedelta(hours=dt_hours)
    lat = 18.90 + (i * 0.04)
    lon = 71.95 + (i * 0.02)  # East of Mumbai corridor
    sog = 11.5
    cog = 18.0
    ais_records_mumbai.append({
        "mmsi": v3_mmsi,
        "vessel_name": v3_name,
        "vessel_type": v3_type,
        "latitude": round(lat, 4),
        "longitude": round(lon, 4),
        "timestamp": t.strftime("%Y-%m-%d %H:%M:%S"),
        "sog": sog,
        "cog": cog
    })

# Vessel 4: FV SAGARIKA (Unlikely - 25% Score)
v4_mmsi = 419003456
v4_name = "FV SAGARIKA"
v4_type = "Fishing Vessel"
for i, dt_hours in enumerate([-23, -19, -15, -11]):
    t = now + datetime.timedelta(hours=dt_hours)
    lat = 18.60 + (i * 0.02)
    lon = 71.50 + (i * 0.02)  # Far Southwest
    sog = 6.0
    cog = 45.0
    ais_records_mumbai.append({
        "mmsi": v4_mmsi,
        "vessel_name": v4_name,
        "vessel_type": v4_type,
        "latitude": round(lat, 4),
        "longitude": round(lon, 4),
        "timestamp": t.strftime("%Y-%m-%d %H:%M:%S"),
        "sog": sog,
        "cog": cog
    })

df_mumbai = pd.DataFrame(ais_records_mumbai)
df_mumbai.to_csv("data/ais/mumbai_offshore_ais.csv", index=False)
print("Saved data/ais/mumbai_offshore_ais.csv")

# Dataset 2: Persian Gulf / Strait of Hormuz (Center ~ 26.2°N, 56.4°E)
ais_records_gulf = []
v_gulf_names = [
    (538002100, "MT ARABIAN HORIZON", "VLCC Crude Tanker", 26.15, 56.35, 12.5, 310.0),
    (636014500, "MT PERSIAN GLORY", "Product Tanker", 26.05, 56.50, 11.0, 305.0),
    (477003200, "MV EMIRATES EXPRESS", "Container Ship", 26.30, 56.20, 17.5, 315.0),
]
for mmsi, name, vtype, base_lat, base_lon, sog, cog in v_gulf_names:
    for step in range(5):
        t = now - datetime.timedelta(hours=20 - (step * 4))
        p_lat = base_lat + (step * 0.04)
        p_lon = base_lon - (step * 0.04)
        ais_records_gulf.append({
            "mmsi": mmsi,
            "vessel_name": name,
            "vessel_type": vtype,
            "latitude": round(p_lat, 4),
            "longitude": round(p_lon, 4),
            "timestamp": t.strftime("%Y-%m-%d %H:%M:%S"),
            "sog": sog,
            "cog": cog
        })

df_gulf = pd.DataFrame(ais_records_gulf)
df_gulf.to_csv("data/ais/persian_gulf_ais.csv", index=False)
print("Saved data/ais/persian_gulf_ais.csv")
print("All realistic demo assets generated successfully!")
