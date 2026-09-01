import os

# Ensure output directory exists
output_dir = os.path.join("docs", "wireframes")
os.makedirs(output_dir, exist_ok=True)

# Common SVGs components
def get_header(title, active_tab_index):
    tabs = ["1. Executive", "2. Dosimetry", "3. 3D Fleet", "4. Maintenance", "5. Commands", "6. Reports"]
    tab_xml = ""
    for i, tab in enumerate(tabs):
        color = "#38BDF8" if i == active_tab_index else "#94A3B8"
        weight = "bold" if i == active_tab_index else "normal"
        tab_xml += f'<text x="{380 + i*130}" y="42" fill="{color}" font-family="sans-serif" font-size="14" font-weight="{weight}">{tab}</text>'
    
    return f'''
    <!-- Top Header Navigation -->
    <rect x="0" y="0" width="1440" height="70" fill="#0F172A"/>
    <text x="30" y="42" fill="#F8FAFC" font-family="sans-serif" font-size="18" font-weight="bold">SPARC-PM | ISRO Mission Control</text>
    {tab_xml}
    <rect x="1100" y="20" width="310" height="32" rx="6" fill="#1E293B" stroke="#334155"/>
    <circle cx="1115" cy="36" r="5" fill="#10B981"/>
    <text x="1130" y="41" fill="#F8FAFC" font-family="sans-serif" font-size="12">UTC: 2026-07-29 | ADITYA-L1: LIVE</text>
    '''

def save_svg(filename, content):
    filepath = os.path.join(output_dir, filename)
    svg_wrapper = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 900" width="1440" height="900" style="background:#0B0F19;">
    {content}
    </svg>'''
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(svg_wrapper)
    print(f"[INFO] Generated: {filepath}")

# ==========================================
# SCREEN 1: EXECUTIVE MISSION OVERVIEW
# ==========================================
s1 = get_header("Overview", 0) + '''
<!-- Metric Card 1 -->
<rect x="40" y="100" width="420" height="110" rx="10" fill="#1E293B" stroke="#10B981" stroke-width="2"/>
<text x="60" y="130" fill="#94A3B8" font-family="sans-serif" font-size="13">GLOBAL FLEET ALERT LEVEL</text>
<text x="60" y="170" fill="#10B981" font-family="sans-serif" font-size="28" font-weight="bold">NOMINAL (GREEN)</text>

<!-- Metric Card 2 -->
<rect x="510" y="100" width="420" height="110" rx="10" fill="#1E293B" stroke="#334155"/>
<text x="530" y="130" fill="#94A3B8" font-family="sans-serif" font-size="13">ACTIVE SATELLITES TRACKED</text>
<text x="530" y="170" fill="#38BDF8" font-family="sans-serif" font-size="28" font-weight="bold">24 / 24 Operational</text>

<!-- Metric Card 3 -->
<rect x="980" y="100" width="420" height="110" rx="10" fill="#1E293B" stroke="#334155"/>
<text x="1000" y="130" fill="#94A3B8" font-family="sans-serif" font-size="13">PEAK SOLAR PROTON FLUX</text>
<text x="1000" y="170" fill="#F59E0B" font-family="sans-serif" font-size="28" font-weight="bold">12.4 pfu (Normal)</text>

<!-- Main Telemetry Chart -->
<rect x="40" y="240" width="890" height="480" rx="10" fill="#1E293B" stroke="#334155"/>
<text x="70" y="280" fill="#F8FAFC" font-family="sans-serif" font-size="16" font-weight="bold">Real-Time Solar Proton Flux Stream (Aditya-L1 Telemetry)</text>
<path d="M 80 650 Q 250 630 400 550 T 700 450 T 900 350" fill="none" stroke="#38BDF8" stroke-width="3"/>
<line x1="80" y1="670" x2="900" y2="670" stroke="#475569" stroke-width="1"/>

<!-- Satellite Status List -->
<rect x="960" y="240" width="440" height="480" rx="10" fill="#1E293B" stroke="#334155"/>
<text x="990" y="280" fill="#F8FAFC" font-family="sans-serif" font-size="16" font-weight="bold">Spacecraft Fleet Telemetry</text>
<text x="990" y="330" fill="#F8FAFC" font-family="sans-serif" font-size="14">INSAT-3DR — Health: 98% [NOMINAL]</text>
<text x="990" y="380" fill="#F8FAFC" font-family="sans-serif" font-size="14">EOS-06 — Health: 95% [NOMINAL]</text>
<text x="990" y="430" fill="#F8FAFC" font-family="sans-serif" font-size="14">Gaganyaan-1 — Health: 100% [NOMINAL]</text>

<!-- Console Log -->
<rect x="40" y="740" width="1360" height="120" rx="10" fill="#020617" stroke="#334155"/>
<text x="60" y="775" fill="#38BDF8" font-family="monospace" font-size="13">> [21:45:00 UTC] Aditya-L1 PAPA/ASPEX packet ingested successfully (200 OK)</text>
<text x="60" y="805" fill="#10B981" font-family="monospace" font-size="13">> [21:45:10 UTC] LSTM Dose engine initialized. Hazard score: LOW</text>
'''
save_svg("01_executive_overview.svg", s1)

# ==========================================
# SCREEN 2: GAGANYAAN CREW DOSIMETRY
# ==========================================
s2 = get_header("Dosimetry", 1) + '''
<!-- Banner -->
<rect x="40" y="90" width="1360" height="70" rx="10" fill="#065F46" stroke="#10B981"/>
<text x="70" y="132" fill="#F8FAFC" font-family="sans-serif" font-size="20" font-weight="bold">FSM TRIAGE STATUS: GREEN (NOMINAL) — CREW CLEAR FOR EVA</text>

<!-- Left Chart: LSTM Forecast -->
<rect x="40" y="180" width="660" height="520" rx="10" fill="#1E293B" stroke="#334155"/>
<text x="70" y="220" fill="#F8FAFC" font-family="sans-serif" font-size="16" font-weight="bold">6-Hour LSTM Proton Flux Forecast Curve</text>
<path d="M 70 600 Q 200 580 350 480 T 650 350" fill="none" stroke="#38BDF8" stroke-width="3"/>
<path d="M 350 480 Q 500 400 650 250" fill="none" stroke="#F59E0B" stroke-dasharray="6,6" stroke-width="3"/>

<!-- Right Chart: Absorbed Dose Curve -->
<rect x="740" y="180" width="660" height="520" rx="10" fill="#1E293B" stroke="#334155"/>
<text x="770" y="220" fill="#F8FAFC" font-family="sans-serif" font-size="16" font-weight="bold">Crew Cumulative Dose (mSv) — Simpson Integration</text>
<line x1="770" y1="350" x2="1360" y2="350" stroke="#EF4444" stroke-dasharray="4,4" stroke-width="2"/>
<text x="1220" y="340" fill="#EF4444" font-family="sans-serif" font-size="12">Red Limit: 10.0 mSv</text>
<path d="M 770 620 C 950 610, 1100 580, 1360 520" fill="none" stroke="#10B981" stroke-width="3"/>

<!-- Control Panel -->
<rect x="40" y="720" width="1360" height="140" rx="10" fill="#1E293B" stroke="#334155"/>
<rect x="70" y="755" width="380" height="70" rx="8" fill="#DC2626"/>
<text x="110" y="797" fill="#FFFFFF" font-family="sans-serif" font-size="16" font-weight="bold">TRIGGER CREW STORM SHELTER ALARM</text>
'''
save_svg("02_gaganyaan_dosimetry.svg", s2)

# ==========================================
# SCREEN 3: 3D FLEET HAZARD PROFILER
# ==========================================
s3 = get_header("3D Fleet", 2) + '''
<!-- Left Sidebar -->
<rect x="40" y="90" width="260" height="770" rx="10" fill="#1E293B" stroke="#334155"/>
<text x="60" y="130" fill="#F8FAFC" font-family="sans-serif" font-size="16" font-weight="bold">Orbit Filters</text>
<text x="60" y="180" fill="#38BDF8" font-family="sans-serif" font-size="14">[X] LEO Satellites</text>
<text x="60" y="220" fill="#38BDF8" font-family="sans-serif" font-size="14">[X] GEO Satellites</text>
<text x="60" y="260" fill="#94A3B8" font-family="sans-serif" font-size="14">[ ] Molniya Orbits</text>

<!-- 3D Earth Globe Viewport -->
<rect x="320" y="90" width="800" height="770" rx="10" fill="#020617" stroke="#334155"/>
<circle cx="720" cy="475" r="180" fill="#1E3A8A" stroke="#38BDF8" stroke-width="2"/>
<ellipse cx="720" cy="475" rx="320" ry="80" fill="none" stroke="#10B981" stroke-dasharray="5,5" stroke-width="2"/>
<polygon points="720,475 1050,200 1100,350" fill="#EF4444" opacity="0.3"/>
<text x="720" y="480" fill="#FFFFFF" font-family="sans-serif" font-size="18" text-anchor="middle" font-weight="bold">EARTH (SGP4 Model)</text>

<!-- Right Sidebar -->
<rect x="1140" y="90" width="260" height="770" rx="10" fill="#1E293B" stroke="#334155"/>
<text x="1160" y="130" fill="#F8FAFC" font-family="sans-serif" font-size="16" font-weight="bold">Selected Satellite</text>
<text x="1160" y="180" fill="#38BDF8" font-family="sans-serif" font-size="14">INSAT-3DR</text>
<text x="1160" y="220" fill="#94A3B8" font-family="sans-serif" font-size="12">Lat: 12.9° N | Lon: 77.5° E</text>
<text x="1160" y="250" fill="#F59E0B" font-family="sans-serif" font-size="12">Hazard Proximity: 1,420 km</text>
'''
save_svg("03_3d_fleet_hazard.svg", s3)

# ==========================================
# SCREEN 4: PREDICTIVE MAINTENANCE
# ==========================================
s4 = get_header("Maintenance", 3) + '''
<!-- Subsystem Health Row -->
<rect x="40" y="90" width="320" height="90" rx="8" fill="#1E293B" stroke="#10B981"/>
<text x="60" y="125" fill="#94A3B8" font-family="sans-serif" font-size="12">POWER SUBSYSTEM</text>
<text x="60" y="155" fill="#10B981" font-family="sans-serif" font-size="20" font-weight="bold">99% Healthy</text>

<rect x="386" y="90" width="320" height="90" rx="8" fill="#1E293B" stroke="#F59E0B"/>
<text x="406" y="125" fill="#94A3B8" font-family="sans-serif" font-size="12">ATTITUDE (ADCS)</text>
<text x="406" y="155" fill="#F59E0B" font-family="sans-serif" font-size="20" font-weight="bold">87% Degraded</text>

<rect x="733" y="90" width="320" height="90" rx="8" fill="#1E293B" stroke="#10B981"/>
<text x="753" y="125" fill="#94A3B8" font-family="sans-serif" font-size="12">THERMAL CONTROL</text>
<text x="753" y="155" fill="#10B981" font-family="sans-serif" font-size="20" font-weight="bold">98% Healthy</text>

<rect x="1080" y="90" width="320" height="90" rx="8" fill="#1E293B" stroke="#10B981"/>
<text x="1100" y="125" fill="#94A3B8" font-family="sans-serif" font-size="12">PAYLOAD</text>
<text x="1100" y="155" fill="#10B981" font-family="sans-serif" font-size="20" font-weight="bold">100% Healthy</text>

<!-- CNN-LSTM Anomaly Reconstruction -->
<rect x="40" y="200" width="850" height="660" rx="10" fill="#1E293B" stroke="#334155"/>
<text x="70" y="240" fill="#F8FAFC" font-family="sans-serif" font-size="16" font-weight="bold">CNN-LSTM Anomaly Reconstruction Error</text>
<path d="M 80 650 Q 300 640 450 350 T 700 630 T 850 640" fill="none" stroke="#EF4444" stroke-width="3"/>
<line x1="80" y1="500" x2="850" y2="500" stroke="#F59E0B" stroke-dasharray="5,5" stroke-width="2"/>

<!-- Naive Bayes Failure Classifier -->
<rect x="910" y="200" width="490" height="660" rx="10" fill="#1E293B" stroke="#334155"/>
<text x="940" y="240" fill="#F8FAFC" font-family="sans-serif" font-size="16" font-weight="bold">Naive Bayes Failure Classification</text>
<text x="940" y="300" fill="#F8FAFC" font-family="sans-serif" font-size="14">Gyroscope Drift Noise: 78% (HIGH)</text>
<rect x="940" y="320" width="350" height="15" rx="4" fill="#EF4444"/>
<text x="940" y="380" fill="#F8FAFC" font-family="sans-serif" font-size="14">CMOS Sensor Degradation: 15%</text>
<rect x="940" y="400" width="75" height="15" rx="4" fill="#38BDF8"/>
'''
save_svg("04_predictive_maintenance.svg", s4)

# ==========================================
# SCREEN 5: COMMAND SYNTHESIZER
# ==========================================
s5 = get_header("Commands", 4) + '''
<!-- Left Panel: Payload JSON -->
<rect x="40" y="90" width="440" height="770" rx="10" fill="#020617" stroke="#334155"/>
<text x="70" y="130" fill="#F8FAFC" font-family="sans-serif" font-size="16" font-weight="bold">CCSDS Telecommand Payload (JSON)</text>
<text x="70" y="180" fill="#38BDF8" font-family="monospace" font-size="13">&#123;</text>
<text x="90" y="210" fill="#38BDF8" font-family="monospace" font-size="13">"target": "ISRO_EOS_06",</text>
<text x="90" y="240" fill="#38BDF8" font-family="monospace" font-size="13">"action": "SAFE_MODE_ORIENT",</text>
<text x="90" y="270" fill="#38BDF8" font-family="monospace" font-size="13">"panel_angle": 180,</text>
<text x="90" y="300" fill="#38BDF8" font-family="monospace" font-size="13">"sha256": "8f4e2a9b3c..."</text>
<text x="70" y="330" fill="#38BDF8" font-family="monospace" font-size="13">&#125;</text>

<!-- Center Panel: Verification & Interlock -->
<rect x="500" y="90" width="440" height="770" rx="10" fill="#1E293B" stroke="#334155"/>
<text x="530" y="130" fill="#F8FAFC" font-family="sans-serif" font-size="16" font-weight="bold">Security Verification & Override</text>
<rect x="530" y="160" width="380" height="60" rx="8" fill="#065F46"/>
<text x="550" y="195" fill="#FFFFFF" font-family="sans-serif" font-size="14">SHA-256 Checksum Verified [VALID]</text>

<circle cx="720" cy="450" r="100" fill="#7F1D1D" stroke="#EF4444" stroke-width="4"/>
<text x="720" y="445" fill="#FFFFFF" font-family="sans-serif" font-size="28" font-weight="bold" text-anchor="middle">00:08</text>
<text x="720" y="475" fill="#F8FAFC" font-family="sans-serif" font-size="12" text-anchor="middle">COUNTDOWN</text>

<rect x="550" y="620" width="340" height="60" rx="8" fill="#DC2626"/>
<text x="610" y="656" fill="#FFFFFF" font-family="sans-serif" font-size="16" font-weight="bold">ABORT COMMAND</text>

<!-- Right Panel: Audit Trail -->
<rect x="960" y="90" width="440" height="770" rx="10" fill="#1E293B" stroke="#334155"/>
<text x="990" y="130" fill="#F8FAFC" font-family="sans-serif" font-size="16" font-weight="bold">Telecommand Audit Log</text>
<text x="990" y="180" fill="#94A3B8" font-family="sans-serif" font-size="13">[21:40] CMD_0102: EXECUTED (ACK)</text>
<text x="990" y="220" fill="#F59E0B" font-family="sans-serif" font-size="13">[21:45] CMD_0103: STAGED (COUNTDOWN)</text>
'''
save_svg("05_command_synthesizer.svg", s5)

# ==========================================
# SCREEN 6: INCIDENT ANALYTICS
# ==========================================
s6 = get_header("Reports", 5) + '''
<!-- Top Selector -->
<rect x="40" y="90" width="1360" height="80" rx="10" fill="#1E293B" stroke="#334155"/>
<text x="70" y="138" fill="#F8FAFC" font-family="sans-serif" font-size="16" font-weight="bold">Select Historical Incident:</text>
<rect x="300" y="110" width="450" height="40" rx="6" fill="#0F172A" stroke="#334155"/>
<text x="320" y="135" fill="#38BDF8" font-family="sans-serif" font-size="14">October 2003 Halloween Solar Storm ▼</text>

<!-- Replay Chart -->
<rect x="40" y="190" width="1360" height="500" rx="10" fill="#1E293B" stroke="#334155"/>
<text x="70" y="230" fill="#F8FAFC" font-family="sans-serif" font-size="16" font-weight="bold">Historical Telemetry vs SPARC Predictive Model Performance</text>
<path d="M 80 600 Q 400 580 700 280 T 1300 550" fill="none" stroke="#38BDF8" stroke-width="3"/>
<path d="M 80 600 Q 400 590 700 300 T 1300 540" fill="none" stroke="#F59E0B" stroke-dasharray="5,5" stroke-width="2"/>

<!-- PDF Export Studio -->
<rect x="40" y="710" width="1360" height="150" rx="10" fill="#1E293B" stroke="#334155"/>
<text x="70" y="750" fill="#F8FAFC" font-family="sans-serif" font-size="16" font-weight="bold">Generate Official Mission Incident Report</text>
<text x="70" y="790" fill="#94A3B8" font-family="sans-serif" font-size="13">[X] Include Dosimetry Logs   [X] Include Anomaly Error Charts   [X] Include Cryptographic Hash</text>

<rect x="1000" y="740" width="350" height="60" rx="8" fill="#2563EB"/>
<text x="1050" y="777" fill="#FFFFFF" font-family="sans-serif" font-size="16" font-weight="bold">Export Official PDF Report (.pdf)</text>
'''
save_svg("06_incident_analytics.svg", s6)

print("\nAll 6 Wireframe SVG files generated inside docs/wireframes/")