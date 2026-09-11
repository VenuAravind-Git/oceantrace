/**
 * OCEANTRACE Tactical Maritime Surveillance & Vessel Attribution System
 * Vanilla JavaScript Frontend Controller (Real-Time Enterprise Edition)
 */

document.addEventListener("DOMContentLoaded", () => {
  // Global State
  let map = null;
  let currentTileLayer = null;
  let currentTheme = localStorage.getItem("oceantrace_theme") || "dark";
  let isSatelliteMode = false;

  let layers = {
    spillPolygon: null,
    originCircle: null,
    originMarker: null,
    hindcastLine: null,
    forecastLine: null,
    vesselLayers: []
  };

  let globalData = {
    spill: null,
    drift: null,
    vessels: [],
    attribution: [],
    ports: []
  };

  // DOM Elements
  const btnRunAnalysis = document.getElementById("btn-run-analysis");
  const analysisModal = document.getElementById("analysis-modal");
  const pipelineBarFill = document.getElementById("pipeline-bar-fill");
  const evidenceModal = document.getElementById("evidence-modal");
  const btnCloseModal = document.getElementById("btn-close-modal");
  const btnCloseModal2 = document.getElementById("btn-close-modal-2");
  const btnThemeToggle = document.getElementById("btn-theme-toggle");
  const themeIconMoon = document.getElementById("theme-icon-moon");
  const themeIconSun = document.getElementById("theme-icon-sun");
  const themeBtnText = document.getElementById("theme-btn-text");
  
  // Real-Time Location Search & NASA Satellite
  const navLocationSearch = document.getElementById("nav-location-search");
  const btnNavSearch = document.getElementById("btn-nav-search");
  const btnSatelliteToggle = document.getElementById("btn-satellite-toggle");
  const satBtnText = document.getElementById("sat-btn-text");

  // Tab Elements
  const tabButtons = document.querySelectorAll(".tab-btn");
  const viewContents = document.querySelectorAll(".view-content");

  // View 2: Vessel Table Elements
  const vesselSearchInput = document.getElementById("vessel-search-input");
  const vesselFilterSelect = document.getElementById("vessel-filter-select");
  const vesselsTableBody = document.getElementById("vessels-table-body");
  const tabVesselsCount = document.getElementById("tab-vessels-count");

  // View 3: Simulator Elements
  const customIncidentForm = document.getElementById("custom-incident-form");
  const simulatorPortsGrid = document.getElementById("simulator-ports-grid");
  const btnRefreshPorts = document.getElementById("btn-refresh-ports");

  // View 4: Report Print
  const btnPrintReport = document.getElementById("btn-print-report");

  // View 5: Settings
  const btnSaveSettings = document.getElementById("btn-save-settings");
  const inpAisKey = document.getElementById("inp-ais-key");
  const chkLiveOcean = document.getElementById("chk-live-ocean");

  // ================= 1. Theme & Satellite Tile Management =================
  function applyTheme(theme) {
    currentTheme = theme;
    localStorage.setItem("oceantrace_theme", theme);

    if (theme === "light") {
      document.body.classList.remove("dark-theme");
      document.body.classList.add("light-theme");
      if (themeIconMoon) themeIconMoon.style.display = "none";
      if (themeIconSun) themeIconSun.style.display = "inline-block";
      if (themeBtnText) themeBtnText.textContent = "Light";

      if (map && !isSatelliteMode) {
        if (currentTileLayer) map.removeLayer(currentTileLayer);
        currentTileLayer = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
          maxZoom: 19,
          attribution: "&copy; OpenStreetMap contributors"
        }).addTo(map);
      }
    } else {
      document.body.classList.remove("light-theme");
      document.body.classList.add("dark-theme");
      if (themeIconMoon) themeIconMoon.style.display = "inline-block";
      if (themeIconSun) themeIconSun.style.display = "none";
      if (themeBtnText) themeBtnText.textContent = "Dark";

      if (map && !isSatelliteMode) {
        if (currentTileLayer) map.removeLayer(currentTileLayer);
        currentTileLayer = L.tileLayer("https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}{r}.png", {
          maxZoom: 20,
          attribution: "&copy; Stadia Maps &copy; OpenMapTiles &copy; OpenStreetMap contributors"
        }).addTo(map);
      }
    }
  }

  if (btnThemeToggle) {
    btnThemeToggle.addEventListener("click", () => {
      const nextTheme = currentTheme === "dark" ? "light" : "dark";
      applyTheme(nextTheme);
    });
  }

  // NASA GIBS Satellite Toggle
  if (btnSatelliteToggle) {
    btnSatelliteToggle.addEventListener("click", () => {
      if (!map) return;
      isSatelliteMode = !isSatelliteMode;
      btnSatelliteToggle.classList.toggle("active-sat", isSatelliteMode);

      if (isSatelliteMode) {
        if (currentTileLayer) map.removeLayer(currentTileLayer);
        satBtnText.textContent = "OSM Maps";
        
        // Use NASA GIBS imagery layer
        const dateStr = "2024-05-01"; // Guaranteed global imagery pass
        currentTileLayer = L.tileLayer(`https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_CorrectedReflectance_TrueColor/default/${dateStr}/GoogleMapsCompatible_Level9/{z}/{y}/{x}.jpg`, {
          maxZoom: 9,
          attribution: "Imagery &copy; NASA EOSDIS GIBS"
        }).addTo(map);
      } else {
        satBtnText.textContent = "NASA GIBS";
        applyTheme(currentTheme);
      }
    });
  }

  // ================= 2. Sub-Tab Navigation =================
  function switchTab(targetViewId) {
    tabButtons.forEach(btn => {
      btn.classList.toggle("active", btn.dataset.view === targetViewId);
    });
    viewContents.forEach(view => {
      view.classList.toggle("active", view.id === targetViewId);
    });

    if (targetViewId === "view-map" && map) {
      setTimeout(() => map.invalidateSize(), 150);
    }
    if (targetViewId === "view-report") {
      renderReportData();
    }
    if (targetViewId === "view-simulate") {
      loadSimulatorPorts();
    }
  }

  tabButtons.forEach(btn => {
    btn.addEventListener("click", () => switchTab(btn.dataset.view));
  });

  // ================= 3. Initialize Map =================
  function initMap() {
    map = L.map("tactical-map", {
      zoomControl: true,
      attributionControl: false
    }).setView([1.31, 104.22], 11);

    applyTheme(currentTheme);
    L.control.scale({ position: "bottomright", imperial: false }).addTo(map);
  }

  // ================= 4. Fetch All Dashboard Data =================
  async function refreshAllData() {
    await Promise.all([
      loadSpillData(),
      loadDriftData(),
      loadAttributionData(),
      loadSimulatorPorts()
    ]);
    renderVesselTable();
    renderReportData();
  }

  // 4a. Load Spill Incident
  async function loadSpillData() {
    try {
      const res = await fetch("/api/spill");
      const data = await res.json();
      globalData.spill = data;

      document.getElementById("incident-id").textContent = data.incident_id;
      document.getElementById("spill-region").textContent = data.region_name;
      
      const coordEl = document.getElementById("spill-coords");
      if (coordEl && data.centroid) {
        coordEl.textContent = `${data.centroid.latitude.toFixed(4)}° N, ${data.centroid.longitude.toFixed(4)}° E`;
      }

      const portEl = document.getElementById("spill-nearest-port");
      if (portEl && data.nearest_ports && data.nearest_ports.length > 0) {
        const p0 = data.nearest_ports[0];
        portEl.textContent = `${p0.name} (${p0.distance_km} km)`;
      }

      document.getElementById("spill-time").textContent = data.detection_timestamp.replace("T", " ").replace("Z", " UTC");
      document.getElementById("val-area").textContent = data.geometric_properties.area_km2;
      document.getElementById("val-perimeter").textContent = data.geometric_properties.perimeter_km;
      document.getElementById("val-age").textContent = data.weathering.estimated_age_hours;
      document.getElementById("val-vol").textContent = data.geometric_properties.estimated_volume_m3;

      const env = data.environmental_conditions;
      document.getElementById("val-current-spd").textContent = env.surface_current_speed_knots;
      document.getElementById("val-current-dir").textContent = env.surface_current_direction_deg + "°";
      document.getElementById("val-wind-spd").textContent = env.wind_speed_knots;
      document.getElementById("val-wind-dir").textContent = env.wind_direction_deg + "°";

      const diag = document.getElementById("diag-incident");
      if (diag) diag.textContent = data.incident_id;

      // Draw Slick Polygon
      if (data.slick_polygon && data.slick_polygon.length > 0) {
        if (layers.spillPolygon) map.removeLayer(layers.spillPolygon);

        layers.spillPolygon = L.polygon(data.slick_polygon, {
          color: "#ef4444",
          weight: 2,
          fillColor: "#ef4444",
          fillOpacity: 0.45,
          dashArray: "3, 6"
        }).addTo(map);

        layers.spillPolygon.bindPopup(`
          <div style="color:#0f172a; font-family:sans-serif; font-size:12px;">
            <strong style="color:#b91c1c;">AUTHENTIC SATELLITE SAR OIL SLICK</strong><br>
            <strong>Region:</strong> ${data.region_name}<br>
            <strong>Area:</strong> ${data.geometric_properties.area_km2} km²<br>
            <strong>Est. Volume:</strong> ${data.geometric_properties.estimated_volume_m3} m³<br>
            <strong>Weathering State:</strong> ${data.weathering.spreading_stage}
          </div>
        `);

        // Center map to spill
        if (data.centroid) {
          map.setView([data.centroid.latitude, data.centroid.longitude], 11);
        }
      }
    } catch (err) {
      console.error("Failed to load spill data:", err);
    }
  }

  // 4b. Load Drift Hindcast & Forecast
  async function loadDriftData() {
    try {
      const res = await fetch("/api/drift");
      const data = await res.json();
      globalData.drift = data;

      const hindcast = data.hindcast;
      const originPt = hindcast.origin_point;

      document.getElementById("origin-coord").textContent = `${originPt.latitude.toFixed(4)}° N, ${originPt.longitude.toFixed(4)}° E`;
      const timeStart = hindcast.release_window_hours[0].slice(11, 16);
      const timeEnd = hindcast.release_window_hours[1].slice(11, 16);
      document.getElementById("origin-time").textContent = `${timeStart} - ${timeEnd} UTC`;
      document.getElementById("origin-radius").textContent = `${hindcast.uncertainty_radius_km} km`;

      // Hindcast Polyline
      const hindcastCoords = hindcast.trajectory.map(p => [p.latitude, p.longitude]);
      if (layers.hindcastLine) map.removeLayer(layers.hindcastLine);
      layers.hindcastLine = L.polyline(hindcastCoords, {
        color: "#f59e0b",
        weight: 3,
        dashArray: "6, 8",
        opacity: 0.9
      }).addTo(map);

      // Origin Circle & Marker
      if (layers.originMarker) map.removeLayer(layers.originMarker);
      if (layers.originCircle) map.removeLayer(layers.originCircle);

      layers.originCircle = L.circle([originPt.latitude, originPt.longitude], {
        radius: hindcast.uncertainty_radius_km * 1000,
        color: "#f59e0b",
        weight: 2,
        dashArray: "4, 6",
        fillColor: "#f59e0b",
        fillOpacity: 0.12
      }).addTo(map);

      const originIcon = L.divIcon({
        className: "custom-origin-icon",
        html: `<div style="width:16px; height:16px; background:#f59e0b; border:2px solid #fff; border-radius:50%; box-shadow:0 0 10px #f59e0b;"></div>`,
        iconSize: [16, 16],
        iconAnchor: [8, 8]
      });

      layers.originMarker = L.marker([originPt.latitude, originPt.longitude], { icon: originIcon })
        .addTo(map)
        .bindPopup(`
          <div style="color:#0f172a; font-family:sans-serif; font-size:12px;">
            <strong style="color:#d97706;">ESTIMATED ORIGIN POINT</strong><br>
            <strong>Coordinates:</strong> ${originPt.latitude.toFixed(4)}°N, ${originPt.longitude.toFixed(4)}°E<br>
            <strong>Window:</strong> ${timeStart} - ${timeEnd} UTC<br>
            <strong>Uncertainty:</strong> ${hindcast.uncertainty_radius_km} km
          </div>
        `);

      // 12h Forward Forecast Line
      if (data.forecast && data.forecast.length > 0) {
        const forecastCoords = data.forecast.map(p => [p.latitude, p.longitude]);
        if (layers.forecastLine) map.removeLayer(layers.forecastLine);
        layers.forecastLine = L.polyline(forecastCoords, {
          color: "#38bdf8",
          weight: 2.5,
          dashArray: "2, 6",
          opacity: 0.8
        }).addTo(map);
      }
    } catch (err) {
      console.error("Failed to load drift data:", err);
    }
  }

  // 4c. Load Candidate Vessels & Attribution
  async function loadAttributionData() {
    try {
      const resAttrib = await fetch("/api/attribution");
      const attribData = await resAttrib.json();
      globalData.attribution = attribData.suspect_rankings || [];

      const resVessels = await fetch("/api/vessels");
      const vesselsData = await resVessels.json();
      globalData.vessels = vesselsData.vessels || [];

      if (tabVesselsCount) tabVesselsCount.textContent = globalData.vessels.length;

      renderVesselsList();
      renderVesselsOnMap();
    } catch (err) {
      console.error("Failed to load attribution data:", err);
    }
  }

  // 4d. Load Ports Explorer for Simulator
  async function loadSimulatorPorts() {
    if (!simulatorPortsGrid) return;
    try {
      const res = await fetch("/api/ports");
      const data = await res.json();
      globalData.ports = data.ports || [];
      renderSimulatorPorts(globalData.ports);
    } catch (err) {
      console.error("Failed to load ports:", err);
    }
  }

  function renderSimulatorPorts(ports) {
    if (!simulatorPortsGrid) return;
    simulatorPortsGrid.innerHTML = "";

    if (!ports || ports.length === 0) {
      simulatorPortsGrid.innerHTML = `<div class="loading-placeholder">No commercial ports detected in immediate radius.</div>`;
      return;
    }

    ports.forEach(p => {
      const card = document.createElement("div");
      card.className = "port-card";
      card.innerHTML = `
        <div class="port-card-top">
          <div class="port-name">${p.name}</div>
          <span class="port-dist-badge">${p.distance_nm} NM (${p.distance_km} km)</span>
        </div>
        <div class="port-meta">
          <strong>UN/LOCODE:</strong> ${p.un_locode} &bull; <strong>Country:</strong> ${p.country}<br>
          <strong>Category:</strong> ${p.category}<br>
          <strong>Max Draft:</strong> ${p.max_draft_m}m &bull; <strong>Calls:</strong> ${p.annual_vessel_calls.toLocaleString()}/yr
        </div>
        <div class="port-explanation">
          ${p.sector_explanation}
        </div>
      `;
      simulatorPortsGrid.appendChild(card);
    });
  }

  if (btnRefreshPorts) {
    btnRefreshPorts.addEventListener("click", loadSimulatorPorts);
  }

  // ================= 5. Location Search + Autocomplete =================

  const suggList = document.getElementById("location-suggestions");
  let suggItems = [];      // current suggestion objects from Nominatim
  let activeSuggIdx = -1; // keyboard nav index
  let debounceTimer = null;

  /** Fetch suggestions from Nominatim (OpenStreetMap, free, no key) */
  async function fetchSuggestions(query) {
    try {
      const url = `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&format=json&limit=7&addressdetails=1`;
      const res = await fetch(url, { headers: { "Accept-Language": "en" } });
      if (!res.ok) return [];
      return await res.json();
    } catch { return []; }
  }

  /** Render suggestions list */
  function renderSuggestions(results) {
    if (!suggList) return;
    suggList.innerHTML = "";
    activeSuggIdx = -1;

    if (!results.length) {
      suggList.hidden = true;
      return;
    }

    results.forEach((r, i) => {
      const label = r.display_name || r.name || "Unknown";
      const typeTag = r.type || r.class || "place";
      const country = r.address?.country || "";
      const badgeText = country || typeTag;

      const li = document.createElement("li");
      li.innerHTML = `
        <svg class="sugg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/>
          <circle cx="12" cy="9" r="2.5"/>
        </svg>
        <span class="sugg-name">${label}</span>
        <span class="sugg-type">${badgeText}</span>
      `;
      li.addEventListener("mousedown", (e) => {
        // Use mousedown (fires before blur) so we can catch it before input loses focus
        e.preventDefault();
        selectSuggestion(i);
      });
      suggList.appendChild(li);
    });

    suggItems = results;
    suggList.hidden = false;
  }

  /** Highlight keyboard-active item */
  function updateActiveHighlight() {
    const lis = suggList.querySelectorAll("li");
    lis.forEach((li, i) => li.classList.toggle("sugg-active", i === activeSuggIdx));
  }

  /** User picked a suggestion */
  function selectSuggestion(idx) {
    const item = suggItems[idx];
    if (!item) return;
    navLocationSearch.value = item.display_name || item.name;
    closeSuggestions();
    // Pass precise coordinates from the selected geocoded suggestion
    const coordParam = (item.lat && item.lon) ? `&lat=${item.lat}&lon=${item.lon}` : "";
    handleLocationSearch(coordParam);
  }

  function closeSuggestions() {
    if (suggList) suggList.hidden = true;
    activeSuggIdx = -1;
  }

  async function handleLocationSearch(extraParams = "") {
    const query = navLocationSearch.value.trim();
    if (!query) return;
    closeSuggestions();

    btnNavSearch.textContent = "...";
    btnNavSearch.disabled = true;

    try {
      const url = `/api/search-location?query=${encodeURIComponent(query)}${extraParams}`;
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        await refreshAllData();
        switchTab("view-map");

        if (data.coordinates) {
          map.flyTo([data.coordinates.latitude, data.coordinates.longitude], 11, { duration: 1.5 });
        }
      } else {
        alert("Location search failed. Please verify the ocean region or coordinates.");
      }
    } catch (err) {
      alert("Error searching location: " + err);
    } finally {
      btnNavSearch.textContent = "SEARCH";
      btnNavSearch.disabled = false;
    }
  }

  // ---- Wire up events ----
  if (btnNavSearch) {
    btnNavSearch.addEventListener("click", handleLocationSearch);
  }

  if (navLocationSearch) {
    // Debounced input → fetch suggestions
    navLocationSearch.addEventListener("input", () => {
      clearTimeout(debounceTimer);
      const q = navLocationSearch.value.trim();
      if (q.length < 2) { closeSuggestions(); return; }
      debounceTimer = setTimeout(async () => {
        const results = await fetchSuggestions(q);
        renderSuggestions(results);
      }, 280);
    });

    // Keyboard navigation inside input
    navLocationSearch.addEventListener("keydown", (e) => {
      const lis = suggList ? suggList.querySelectorAll("li") : [];

      if (e.key === "ArrowDown") {
        e.preventDefault();
        if (!suggList || suggList.hidden) return;
        activeSuggIdx = Math.min(activeSuggIdx + 1, lis.length - 1);
        updateActiveHighlight();
        lis[activeSuggIdx]?.scrollIntoView({ block: "nearest" });
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        if (!suggList || suggList.hidden) return;
        activeSuggIdx = Math.max(activeSuggIdx - 1, 0);
        updateActiveHighlight();
        lis[activeSuggIdx]?.scrollIntoView({ block: "nearest" });
      } else if (e.key === "Enter") {
        if (activeSuggIdx >= 0 && !suggList.hidden) {
          e.preventDefault();
          selectSuggestion(activeSuggIdx);
        } else {
          handleLocationSearch();
        }
      } else if (e.key === "Escape") {
        closeSuggestions();
      }
    });

    // Close when focus leaves the entire search area
    navLocationSearch.addEventListener("blur", () => {
      setTimeout(closeSuggestions, 150); // small delay so mousedown on li fires first
    });
  }

  // Close suggestions if user clicks anywhere else on the page
  document.addEventListener("click", (e) => {
    if (!e.target.closest(".search-autocomplete-wrap")) {
      closeSuggestions();
    }
  });

  // ================= 6. Render Map View Right Sidebar =================
  function renderVesselsList() {
    const container = document.getElementById("vessels-container");
    container.innerHTML = "";

    if (!globalData.attribution.length) {
      container.innerHTML = `<div class="loading-placeholder">No vessels detected in active origin sector.</div>`;
      return;
    }

    globalData.attribution.forEach((v, idx) => {
      const isTop = idx === 0;
      const card = document.createElement("div");
      card.className = `vessel-card ${isTop ? 'suspect-top' : ''}`;
      card.dataset.mmsi = v.mmsi;

      const hasAnomalies = v.evidence_log && v.evidence_log.some(e => e.includes("Anomaly") || e.includes("Crucial") || e.includes("reduction"));

      card.innerHTML = `
        <div class="card-top">
          <div>
            <div class="vessel-title">${v.name}</div>
            <div class="vessel-type-tag">${v.vessel_type} &bull; ${v.flag}</div>
          </div>
          <span class="score-badge ${v.badge_class}">${v.total_score}%</span>
        </div>

        <div class="card-metrics-grid">
          <span class="cm-label">CPA to Origin:</span>
          <span class="cm-val ${v.closest_approach.distance_km <= 1.0 ? 'text-amber' : ''}">${v.closest_approach.distance_km} km</span>
          <span class="cm-label">Time Offset:</span>
          <span class="cm-val">${Math.abs(v.closest_approach.time_diff_minutes)} mins</span>
          <span class="cm-label">Speed at CPA:</span>
          <span class="cm-val">${v.closest_approach.speed_knots} kt</span>
          <span class="cm-label">MMSI:</span>
          <span class="cm-val font-mono">${v.mmsi}</span>
        </div>

        ${hasAnomalies && isTop ? `
          <div class="mini-anomaly-alert">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
            <span>Speed drop & course anomaly detected</span>
          </div>
        ` : ''}
      `;

      card.addEventListener("click", () => openEvidenceModal(v));
      container.appendChild(card);
    });
  }

  // ================= 7. Render Map Trajectories =================
  function renderVesselsOnMap() {
    layers.vesselLayers.forEach(l => map.removeLayer(l));
    layers.vesselLayers = [];

    globalData.vessels.forEach((v) => {
      const attrib = globalData.attribution.find(a => a.mmsi === v.mmsi);
      const isTopSuspect = attrib && attrib.rank === 1;

      const coords = v.trajectory.map(pt => [pt.latitude, pt.longitude]);
      if (coords.length > 1) {
        const poly = L.polyline(coords, {
          color: isTopSuspect ? "#ef4444" : "#06b6d4",
          weight: isTopSuspect ? 3 : 1.5,
          opacity: isTopSuspect ? 0.9 : 0.4,
          dashArray: isTopSuspect ? null : "4, 4"
        }).addTo(map);
        layers.vesselLayers.push(poly);
      }

      const cpa = v.closest_point_of_approach;
      if (cpa && cpa.latitude) {
        const markerColor = isTopSuspect ? "#ef4444" : "#06b6d4";
        const shipIcon = L.divIcon({
          className: "tactical-ship-icon",
          html: `<div style="transform: rotate(${cpa.course_deg || 0}deg); color: ${markerColor}; font-size: 16px; text-shadow: 0 0 8px ${markerColor};">▲</div>`,
          iconSize: [16, 16],
          iconAnchor: [8, 8]
        });

        const marker = L.marker([cpa.latitude, cpa.longitude], { icon: shipIcon }).addTo(map);
        marker.bindPopup(`
          <div style="color:#0f172a; font-family:sans-serif; font-size:12px;">
            <strong style="color:${markerColor}; font-size:13px;">${v.name}</strong><br>
            <strong>Type:</strong> ${v.vessel_type}<br>
            <strong>MMSI:</strong> ${v.mmsi}<br>
            <strong>Speed:</strong> ${cpa.speed_knots} kt &bull; <strong>Course:</strong> ${cpa.course_deg}°<br>
            <strong>Dist to Origin:</strong> ${cpa.distance_km} km<br>
            <button style="margin-top:6px; background:#0284c7; color:#fff; border:none; padding:4px 8px; border-radius:4px; cursor:pointer;" onclick="window.triggerDossier(${v.mmsi})">Inspect Dossier</button>
          </div>
        `);
        layers.vesselLayers.push(marker);
      }
    });
  }

  window.triggerDossier = (mmsi) => {
    const vessel = globalData.attribution.find(a => a.mmsi === mmsi);
    if (vessel) openEvidenceModal(vessel);
  };

  // ================= 8. Evidence Dossier Modal =================
  function openEvidenceModal(vessel) {
    const rawVessel = globalData.vessels.find(v => v.mmsi === vessel.mmsi) || {};

    document.getElementById("modal-vessel-name").textContent = vessel.name;
    const tierBadge = document.getElementById("modal-suspect-tier");
    tierBadge.textContent = vessel.classification;
    tierBadge.className = `badge ${vessel.badge_class}`;

    document.getElementById("dossier-mmsi").textContent = vessel.mmsi;
    document.getElementById("dossier-type").textContent = vessel.vessel_type;
    document.getElementById("dossier-flag").textContent = vessel.flag || rawVessel.flag || "International";
    document.getElementById("dossier-dim").innerHTML = `${rawVessel.length || 200}m &times; ${rawVessel.width || 32}m`;
    document.getElementById("dossier-dwt").textContent = `${(rawVessel.deadweight_tonnage || 50000).toLocaleString()} DWT`;

    document.getElementById("dossier-cpa-dist").textContent = `${vessel.closest_approach.distance_km} km`;
    document.getElementById("dossier-time-offset").textContent = `${vessel.closest_approach.time_diff_minutes > 0 ? '+' : ''}${vessel.closest_approach.time_diff_minutes} mins from release window`;
    document.getElementById("dossier-speed").textContent = `${vessel.closest_approach.speed_knots} knots`;
    document.getElementById("dossier-course").textContent = `${vessel.closest_approach.course_deg}°`;

    document.getElementById("dossier-total-score").textContent = `${vessel.total_score} / 100`;

    const barsContainer = document.getElementById("dossier-breakdown-bars");
    barsContainer.innerHTML = "";
    const factors = [
      { name: "Spatial Proximity", key: "spatial_proximity" },
      { name: "Temporal Correlation", key: "temporal_correlation" },
      { name: "Trajectory Consistency", key: "trajectory_consistency" },
      { name: "Vessel Type Profile", key: "vessel_type_risk" },
      { name: "Behavioral Anomalies", key: "behavioral_anomaly" }
    ];

    factors.forEach(f => {
      const item = vessel.score_breakdown[f.key];
      const barRow = document.createElement("div");
      barRow.className = "bar-row";
      barRow.innerHTML = `
        <div class="bar-row-labels">
          <span>${f.name} (${item.weight_pct}%)</span>
          <span class="font-mono">${item.score}%</span>
        </div>
        <div class="bar-track">
          <div class="bar-prog" style="width: ${item.score}%;"></div>
        </div>
      `;
      barsContainer.appendChild(barRow);
    });

    const evContainer = document.getElementById("dossier-evidence-list");
    evContainer.innerHTML = "";
    (vessel.evidence_log || []).forEach(e => {
      const li = document.createElement("li");
      li.textContent = e;
      evContainer.appendChild(li);
    });

    evidenceModal.classList.add("open");
  }

  btnCloseModal.addEventListener("click", () => evidenceModal.classList.remove("open"));
  btnCloseModal2.addEventListener("click", () => evidenceModal.classList.remove("open"));

  // ================= 9. View 2: Vessel Registry Table =================
  function renderVesselTable() {
    if (!vesselsTableBody) return;
    vesselsTableBody.innerHTML = "";

    const query = (vesselSearchInput ? vesselSearchInput.value.toLowerCase().trim() : "");
    const filter = (vesselFilterSelect ? vesselFilterSelect.value : "ALL");

    const filtered = globalData.attribution.filter(v => {
      const matchesQuery = v.name.toLowerCase().includes(query) ||
                           String(v.mmsi).includes(query) ||
                           v.vessel_type.toLowerCase().includes(query);

      let matchesFilter = true;
      if (filter === "HIGH") matchesFilter = v.total_score >= 80;
      else if (filter === "MODERATE") matchesFilter = v.total_score >= 50 && v.total_score < 80;
      else if (filter === "LOW") matchesFilter = v.total_score < 50;

      return matchesQuery && matchesFilter;
    });

    if (!filtered.length) {
      vesselsTableBody.innerHTML = `<tr><td colspan="10" style="text-align:center; padding:24px; color:var(--text-dim);">No vessels match your search/filter criteria in this sector.</td></tr>`;
      return;
    }

    filtered.forEach(v => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td class="font-mono bold">${v.rank}</td>
        <td class="bold">${v.name}</td>
        <td class="font-mono">${v.mmsi} &bull; ${v.flag}</td>
        <td>${v.vessel_type}</td>
        <td class="font-mono ${v.closest_approach.distance_km <= 1.0 ? 'text-amber' : ''}">${v.closest_approach.distance_km} km</td>
        <td class="font-mono">${Math.abs(v.closest_approach.time_diff_minutes)} mins</td>
        <td class="font-mono">${v.closest_approach.speed_knots} kt</td>
        <td><span class="score-badge ${v.badge_class}">${v.total_score}%</span></td>
        <td><span class="badge ${v.badge_class}">${v.classification}</span></td>
        <td>
          <button class="btn btn-secondary" style="padding:4px 8px; font-size:0.75rem;" onclick="window.triggerDossier(${v.mmsi})">Inspect</button>
        </td>
      `;
      vesselsTableBody.appendChild(tr);
    });
  }

  if (vesselSearchInput) vesselSearchInput.addEventListener("input", renderVesselTable);
  if (vesselFilterSelect) vesselFilterSelect.addEventListener("change", renderVesselTable);

  // ================= 10. View 3: Custom Incident Ingestion =================
  if (customIncidentForm) {
    customIncidentForm.addEventListener("submit", async (e) => {
      e.preventDefault();

      const payload = {
        region_name: document.getElementById("inp-region").value,
        area_km2: parseFloat(document.getElementById("inp-area").value),
        latitude: parseFloat(document.getElementById("inp-lat").value),
        longitude: parseFloat(document.getElementById("inp-lon").value),
        current_speed_knots: parseFloat(document.getElementById("inp-current-spd").value),
        current_direction_deg: parseFloat(document.getElementById("inp-current-dir").value),
        wind_speed_knots: parseFloat(document.getElementById("inp-wind-spd").value),
        wind_direction_deg: parseFloat(document.getElementById("inp-wind-dir").value),
        estimated_age_hours: parseFloat(document.getElementById("inp-age").value)
      };

      try {
        const res = await fetch("/api/incident/custom", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const resData = await res.json();
        alert(`Custom Incident Created: ${resData.incident_id}\nActivating tactical surveillance map!`);
        await refreshAllData();
        switchTab("view-map");
      } catch (err) {
        alert("Failed to submit custom incident: " + err);
      }
    });
  }

  // ================= 11. View 4: Official Case Report =================
  async function renderReportData() {
    try {
      const res = await fetch("/api/report");
      const report = await res.json();

      const spill = report.incident_summary;
      const hindcast = report.hydrodynamic_hindcast;
      const suspect = report.primary_suspect_vessel;
      const bio = report.biological_impact;
      const econ = report.economic_impact;

      document.getElementById("rep-case-id").textContent = report.report_title || `CASE REPORT: ${spill.incident_id}`;
      document.getElementById("rep-region").textContent = spill.region_name;
      document.getElementById("rep-sensor").textContent = spill.sensor_source;
      document.getElementById("rep-time").textContent = spill.detection_timestamp.replace("T", " ").replace("Z", " UTC");
      document.getElementById("rep-centroid").textContent = `${spill.centroid.latitude.toFixed(4)}° N, ${spill.centroid.longitude.toFixed(4)}° E`;
      document.getElementById("rep-area").textContent = `${spill.geometric_properties.area_km2} km²`;
      document.getElementById("rep-vol").textContent = `${spill.geometric_properties.estimated_volume_m3} m³`;

      const tStart = hindcast.release_window_hours[0].slice(11, 16);
      const tEnd = hindcast.release_window_hours[1].slice(11, 16);
      document.getElementById("rep-origin-time").textContent = `${tStart} - ${tEnd} UTC`;
      document.getElementById("rep-origin-coord").textContent = `${hindcast.origin_point.latitude.toFixed(4)}° N, ${hindcast.origin_point.longitude.toFixed(4)}° E`;
      document.getElementById("rep-origin-radius").textContent = `${hindcast.uncertainty_radius_km} km`;

      if (suspect) {
        document.getElementById("rep-suspect-name").textContent = suspect.name;
        document.getElementById("rep-suspect-mmsi").textContent = `${suspect.mmsi} (${suspect.flag || 'Panama'})`;
        document.getElementById("rep-suspect-type").textContent = suspect.vessel_type;
        document.getElementById("rep-suspect-cpa").textContent = `${suspect.closest_approach.distance_km} km from origin centroid`;
        document.getElementById("rep-suspect-time").textContent = `${suspect.closest_approach.time_diff_minutes} mins from estimated release`;
        document.getElementById("rep-suspect-score").textContent = `${suspect.total_score} / 100 (${suspect.classification})`;

        const repEv = document.getElementById("rep-evidence-list");
        repEv.innerHTML = "";
        (suspect.evidence_log || []).forEach(e => {
          const li = document.createElement("li");
          li.textContent = e;
          repEv.appendChild(li);
        });
      }

      // Render Biological Impact
      if (bio) {
        const sevEl = document.getElementById("rep-bio-severity");
        if (sevEl) sevEl.textContent = bio.severity_level;
        const recEl = document.getElementById("rep-bio-recovery");
        if (recEl) recEl.textContent = bio.estimated_recovery_time;

        const fEl = document.getElementById("rep-bio-fauna");
        if (fEl && bio.pelagic_fauna) fEl.textContent = bio.pelagic_fauna.impact;
        const bEl = document.getElementById("rep-bio-benthic");
        if (bEl && bio.benthic_and_coastal) bEl.textContent = bio.benthic_and_coastal.impact;
        const cEl = document.getElementById("rep-bio-chem");
        if (cEl && bio.chemical_toxicity) cEl.textContent = bio.chemical_toxicity.impact;
        const fishEl = document.getElementById("rep-bio-fisheries");
        if (fishEl && bio.fisheries_and_breeding) fishEl.textContent = bio.fisheries_and_breeding.impact;
      }

      // Render Economic Impact
      if (econ && econ.breakdown) {
        const econBody = document.getElementById("rep-econ-table-body");
        if (econBody) {
          econBody.innerHTML = "";
          Object.values(econ.breakdown).forEach(item => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
              <td>${item.label}</td>
              <td style="text-align:right; font-family:var(--font-mono); font-weight:600;">$${item.amount_usd.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
            `;
            econBody.appendChild(tr);
          });
        }
        const totalEl = document.getElementById("rep-econ-total");
        if (totalEl) {
          totalEl.textContent = `$${econ.total_estimated_loss_usd.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        }
      }

    } catch (err) {
      console.error("Failed to render report data:", err);
    }
  }

  if (btnPrintReport) {
    btnPrintReport.addEventListener("click", () => window.print());
  }

  // ================= 12. View 5: Settings Handler =================
  if (btnSaveSettings) {
    btnSaveSettings.addEventListener("click", async () => {
      const payload = {
        aisstream_api_key: inpAisKey.value,
        use_live_ocean_api: chkLiveOcean.checked
      };
      try {
        const res = await fetch("/api/settings", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        alert("Settings updated successfully!\nAIS Status: " + data.ais_ingest.status);
      } catch (err) {
        alert("Error saving settings: " + err);
      }
    });
  }

  // ================= 13. Pipeline Runner Simulation =================
  if (btnRunAnalysis) {
    btnRunAnalysis.addEventListener("click", async () => {
      analysisModal.classList.add("open");
      const steps = document.querySelectorAll(".pipeline-stepper .step-item");
      pipelineBarFill.style.width = "0%";

      const totalSteps = steps.length;
      for (let i = 0; i < totalSteps; i++) {
        steps.forEach((s, idx) => {
          s.classList.remove("active");
          if (idx < i) s.classList.add("completed");
        });
        steps[i].classList.add("active");
        pipelineBarFill.style.width = `${Math.round(((i + 1) / totalSteps) * 100)}%`;
        await new Promise(r => setTimeout(r, 450));
      }

      steps.forEach(s => s.classList.add("completed"));
      await new Promise(r => setTimeout(r, 400));
      analysisModal.classList.remove("open");

      switchTab("view-map");
      if (globalData.attribution.length > 0) {
        const top = globalData.attribution[0];
        const topVessel = globalData.vessels.find(v => v.mmsi === top.mmsi);
        if (topVessel && topVessel.closest_point_of_approach) {
          map.flyTo([topVessel.closest_point_of_approach.latitude, topVessel.closest_point_of_approach.longitude], 13, { duration: 1.5 });
        }
      }
    });
  }

  // Initial startup
  initMap();
  refreshAllData();
});
