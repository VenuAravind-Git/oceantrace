"""
backend/ports.py
Global Maritime Ports, Harbors, and Shipping Fairways Database.
Provides geographic proximity search, harbor specifications, vessel density,
and sector explanations for the OCEANTRACE simulator.
"""

import math
from typing import List, Dict, Any
from backend.satellite import haversine_distance_km

# Rich global registry of major maritime ports and oil terminals
GLOBAL_PORTS_DATABASE = [
    {
        "name": "Port of Singapore / Jurong Island Oil Terminal",
        "country": "Singapore",
        "un_locode": "SG SIN",
        "latitude": 1.2644,
        "longitude": 103.7150,
        "category": "Mega Petrochemical & Bunkering Hub",
        "max_draft_m": 22.0,
        "annual_vessel_calls": 130000,
        "oil_storage_capacity_m3": 12600000,
        "fairway": "Singapore Strait TSS (Traffic Separation Scheme)",
        "risk_profile": "Ultra-High Traffic Density / Crucial East-West Choke Point"
    },
    {
        "name": "Port of Fujairah Oil Terminal",
        "country": "United Arab Emirates",
        "un_locode": "AE FJR",
        "latitude": 25.1783,
        "longitude": 56.3622,
        "category": "Global Crude Oil Bunkering & Export Hub",
        "max_draft_m": 26.0,
        "annual_vessel_calls": 15000,
        "oil_storage_capacity_m3": 10000000,
        "fairway": "Gulf of Oman / Strait of Hormuz Approaches",
        "risk_profile": "Heavy VLCC/Suezmax crude tanker transit corridor"
    },
    {
        "name": "Louisiana Offshore Oil Port (LOOP) / Port of South Louisiana",
        "country": "United States",
        "un_locode": "US LOOP",
        "latitude": 28.8850,
        "longitude": -90.0250,
        "category": "Deepwater Offshore Crude Port",
        "max_draft_m": 28.0,
        "annual_vessel_calls": 4500,
        "oil_storage_capacity_m3": 9500000,
        "fairway": "Mississippi River Delta / Gulf of Mexico Fairway",
        "risk_profile": "Subsea pipelines, offshore production platforms, hurricane exposure"
    },
    {
        "name": "Jawaharlal Nehru Port (JNPT) & Mumbai Port",
        "country": "India",
        "un_locode": "IN NSA",
        "latitude": 18.9490,
        "longitude": 72.9510,
        "category": "Major Container & Petroleum Harbor",
        "max_draft_m": 15.5,
        "annual_vessel_calls": 32000,
        "oil_storage_capacity_m3": 4200000,
        "fairway": "Arabian Sea Coastal Fairway / Mumbai Approach Channel",
        "risk_profile": "Monsoon high currents, heavy coastal traffic, sensitive fishing grounds"
    },
    {
        "name": "Port of Rotterdam (Europoort & Maasvlakte)",
        "country": "Netherlands",
        "un_locode": "NL RTM",
        "latitude": 51.9560,
        "longitude": 4.1450,
        "category": "European Petrochemical Gateway",
        "max_draft_m": 24.0,
        "annual_vessel_calls": 29000,
        "oil_storage_capacity_m3": 8500000,
        "fairway": "North Sea English Channel TSS",
        "risk_profile": "Extremely dense multi-directional commercial fairway"
    },
    {
        "name": "Ras Tanura Terminal",
        "country": "Saudi Arabia",
        "un_locode": "SA RTA",
        "latitude": 26.6433,
        "longitude": 50.1650,
        "category": "World's Largest Offshore Crude Loading Terminal",
        "max_draft_m": 25.0,
        "annual_vessel_calls": 3800,
        "oil_storage_capacity_m3": 33000000,
        "fairway": "Persian Gulf Central Channel",
        "risk_profile": "High volume supertanker loading berths and offshore SPM buoys"
    },
    {
        "name": "Port of Houston Oil & Chemical Terminal",
        "country": "United States",
        "un_locode": "US HOU",
        "latitude": 29.7280,
        "longitude": -95.0340,
        "category": "Petrochemical Refining Complex & Channel",
        "max_draft_m": 14.0,
        "annual_vessel_calls": 8200,
        "oil_storage_capacity_m3": 15000000,
        "fairway": "Houston Ship Channel / Galveston Bay",
        "risk_profile": "Confined waterway transit, high collision risk, extensive estuaries"
    },
    {
        "name": "Port of Malacca / Tanjung Pelepas",
        "country": "Malaysia",
        "un_locode": "MY TPP",
        "latitude": 1.3650,
        "longitude": 103.5500,
        "category": "Transshipment & Bunkering Terminal",
        "max_draft_m": 19.0,
        "annual_vessel_calls": 11000,
        "oil_storage_capacity_m3": 2800000,
        "fairway": "Strait of Malacca South Channel",
        "risk_profile": "High cross-strait ferry traffic, narrow navigational channel"
    },
    {
        "name": "Port of Santos",
        "country": "Brazil",
        "un_locode": "BR SSZ",
        "latitude": -23.9670,
        "longitude": -46.3000,
        "category": "South American Atlantic Gateway",
        "max_draft_m": 14.5,
        "annual_vessel_calls": 5200,
        "oil_storage_capacity_m3": 3100000,
        "fairway": "Santos Bay Navigation Channel",
        "risk_profile": "Offshore pre-salt oil transit corridor"
    },
    {
        "name": "Port of Gibraltar / Algeciras",
        "country": "Spain / Gibraltar",
        "un_locode": "ES ALG",
        "latitude": 36.1300,
        "longitude": -5.4400,
        "category": "Mediterranean Western Bunkering Strait",
        "max_draft_m": 22.0,
        "annual_vessel_calls": 28000,
        "oil_storage_capacity_m3": 3900000,
        "fairway": "Strait of Gibraltar TSS",
        "risk_profile": "Strong Atlantic-Mediterranean surface currents, massive density"
    },
    {
        "name": "Port of Chennai & Ennore (Kamarajar)",
        "country": "India",
        "un_locode": "IN MAA",
        "latitude": 13.0850,
        "longitude": 80.2980,
        "category": "Coromandel Coast Crude & Coal Port",
        "max_draft_m": 16.0,
        "annual_vessel_calls": 4200,
        "oil_storage_capacity_m3": 1900000,
        "fairway": "Bay of Bengal Coastal Corridor",
        "risk_profile": "Tropical cyclones, coastal olive ridley turtle conservation zones"
    },
    {
        "name": "Port of New York and New Jersey",
        "country": "United States",
        "un_locode": "US NYC",
        "latitude": 40.5200,
        "longitude": -73.8500,
        "category": "East Coast Mega Gateway & Refined Petroleum Hub",
        "max_draft_m": 15.2,
        "annual_vessel_calls": 4800,
        "oil_storage_capacity_m3": 7500000,
        "fairway": "New York Bight / Ambrose Channel TSS",
        "risk_profile": "Heavy container and product tanker traffic in busy Atlantic coastal approach"
    },
    {
        "name": "Port of Busan & Ulsan Petrochemical Port",
        "country": "South Korea",
        "un_locode": "KR USN",
        "latitude": 35.5000,
        "longitude": 129.3800,
        "category": "Pacific Industrial & Refined Products Hub",
        "max_draft_m": 20.0,
        "annual_vessel_calls": 24000,
        "oil_storage_capacity_m3": 6200000,
        "fairway": "Korea Strait / East Sea Shipping Lanes",
        "risk_profile": "Heavy seasonal typhoons, fishing fleet congestion"
    }
]


def find_nearest_ports(target_lat: float, target_lon: float, limit: int = 3) -> List[Dict[str, Any]]:
    """
    Finds and ranks the closest major ports to given coordinates,
    computing exact Haversine distance in kilometers and nautical miles.
    """
    ranked = []
    for port in GLOBAL_PORTS_DATABASE:
        dist_km = haversine_distance_km(target_lat, target_lon, port["latitude"], port["longitude"])
        dist_nm = round(dist_km / 1.852, 2)
        ranked.append({
            **port,
            "distance_km": round(dist_km, 2),
            "distance_nm": dist_nm
        })

    ranked.sort(key=lambda x: x["distance_km"])
    top_ports = ranked[:limit]

    # Add forensic sector explanation
    for idx, p in enumerate(top_ports):
        if p["distance_km"] < 60:
            proximity_desc = "Immediate Harbor Sector / Bunkering Outer Anchorage zone"
            corr = "Vessels originating or terminating in this port are subject to primary AIS track correlation."
        elif p["distance_km"] < 250:
            proximity_desc = "Regional Coastal Approach Channel"
            corr = "Vessels transiting through this regional fairway exhibit direct navigational vectors passing the observed coordinates."
        else:
            proximity_desc = "Open Sea Transit Corridor"
            corr = "Major long-distance commercial shipping lane connecting this terminal to global trade routes."

        p["sector_explanation"] = f"{proximity_desc}: Located {p['distance_nm']} NM ({p['distance_km']} km) from coordinates. {corr}"

    return top_ports
