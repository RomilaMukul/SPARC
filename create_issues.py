import json
import os
import time
import urllib.request

# =====================================================================
# CONFIGURATION
# =====================================================================
# Replace the raw token with an environment variable fetch
TOKEN = os.getenv("GITHUB_TOKEN", "YOUR_GITHUB_TOKEN_HERE")
REPO_OWNER = "RomilaMukul"               
REPO_NAME = "SPARC"                      

# =====================================================================
# 25 USER STORIES (MoSCoW PRIORITIZED)
# =====================================================================
USER_STORIES = [
    # 🔴 MUST HAVE (10 Stories)
    {
        "title": "[MUST HAVE] Ingest Aditya-L1 Solar Telemetry Streams",
        "body": "As a **Fleet Lead**, I want to ingest real-time proton and electron flux data from Aditya-L1 payloads (PAPA, ASPEX) so that mission control receives low-latency space weather feeds.\n\n**Acceptance Criteria:**\n- Stream updates at least once every 60s.\n- Handle missing telemetry packets gracefully without crashing.",
        "labels": ["Must Have", "Telemetry"]
    },
    {
        "title": "[MUST HAVE] Cumulative Radiation Absorbed Dose Engine",
        "body": "As a **Gaganyaan Flight Surgeon**, I want Simpson's composite integration computed over flux curves so that I can monitor crew cumulative absorbed radiation dose in real time.\n\n**Acceptance Criteria:**\n- Calculates absorbed dose $D$ in milliSieverts (mSv).\n- Displays accumulated dose against 1.0 mSv and 10.0 mSv safety thresholds.",
        "labels": ["Must Have", "Dosimetry"]
    },
    {
        "title": "[MUST HAVE] LSTM Time-Series Proton Flux Forecasting",
        "body": "As a **Gaganyaan Flight Surgeon**, I want a 2-layer LSTM model forecasting 6-hour future proton flux so that Solar Proton Event (SPE) warnings are triggered before radiation peaks.\n\n**Acceptance Criteria:**\n- Generates 6-hour prediction window from 24-hour historical flux.\n- Re-evaluates forecast curve every telemetry tick.",
        "labels": ["Must Have", "AI/ML"]
    },
    {
        "title": "[MUST HAVE] Finite State Machine (FSM) Triage Classification",
        "body": "As a **Gaganyaan Flight Surgeon**, I want an automated FSM triage system (GREEN, YELLOW, RED) so that crew safety protocols are instantly flagged.\n\n**Acceptance Criteria:**\n- GREEN: $D < 1.0$ mSv (Nominal)\n- YELLOW: $1.0 \le D < 10.0$ mSv (Suspend EVAs)\n- RED: $D \ge 10.0$ mSv (Order crew to storm shelter)",
        "labels": ["Must Have", "Safety"]
    },
    {
        "title": "[MUST HAVE] 3D Satellite Fleet Hazard Profiler",
        "body": "As a **Fleet Lead**, I want 3D Euclidean spatial proximity mapping using SGP4 TLE orbital propagation so that I can identify satellites crossing radiation storm corridors.\n\n**Acceptance Criteria:**\n- Propagates satellite orbits in 3D Earth space.\n- Highlights high-risk satellites crossing hazard zones in red.",
        "labels": ["Must Have", "3D Visualization"]
    },
    {
        "title": "[MUST HAVE] CNN-LSTM Telemetry Anomaly Detection",
        "body": "As a **Subsystem Reliability Specialist**, I want deep learning anomaly detection on telemetry parameters (voltage, gyro drift, temp) so that hardware degradation is flagged early.\n\n**Acceptance Criteria:**\n- Computes normalized reconstruction error score (0-100%).\n- Triggers warning badge when score exceeds 80%.",
        "labels": ["Must Have", "Predictive Maintenance"]
    },
    {
        "title": "[MUST HAVE] Closed-Loop CCSDS Telecommand Packet Generation", "body": "As a **Fleet Lead**, I want automated command packet synthesis for satellite safe-mode transition so that critical response workflows execute in sub-100ms.\n\n**Acceptance Criteria:**\n- Generates CCSDS-compliant JSON command payloads.\n- Includes target satellite ID and action code.",
        "labels": ["Must Have", "Automation"]
    },
    {
        "title": "[MUST HAVE] SHA-256 Command Integrity Hashing",
        "body": "As a **Mission Operations Engineer**, I want all generated telecommands signed with SHA-256 cryptographic checksums so that corrupted commands are rejected by ground controllers.\n\n**Acceptance Criteria:**\n- Generates 64-character hex hash appended to command payload.\n- Validates checksum prior to uplink.",
        "labels": ["Must Have", "Security"]
    },
    {
        "title": "[MUST HAVE] Naive Bayes Failure Mode Classifier",
        "body": "As a **Subsystem Reliability Specialist**, I want probabilistic classification of telemetry anomalies so that repair protocols are context-specific.\n\n**Acceptance Criteria:**\n- Classifies anomalies into CMOS noise, gyro drift, or battery decay.\n- Outputs percentage probability breakdown.",
        "labels": ["Must Have", "AI/ML"]
    },
    {
        "title": "[MUST HAVE] Streamlit Mission Control GUI Dashboard",
        "body": "As a **Mission Operator**, I want an integrated multi-tab dashboard displaying fleet health, space weather, and command logs in one screen.\n\n**Acceptance Criteria:**\n- Renders interactive 3D globes and Plotly flux curves.\n- Latency under 100ms for pipeline updates.",
        "labels": ["Must Have", "UI/UX"]
    },

    # 🟡 SHOULD HAVE (8 Stories)
    {
        "title": "[SHOULD HAVE] Multi-Constellation Satellite Orbit Filter",
        "body": "As a **Fleet Lead**, I want to filter fleet assets by orbit regime (LEO, GEO, Molniya) so that localized atmospheric drag impacts can be analyzed.",
        "labels": ["Should Have", "Fleet Ops"]
    },
    {
        "title": "[SHOULD HAVE] Telemetry Drift Rate Computation Engine",
        "body": "As a **Subsystem Specialist**, I want parameter rate-of-change calculation over 24-hour windows so that battery capacity degradation is spotted early.",
        "labels": ["Should Have", "Analytics"]
    },
    {
        "title": "[SHOULD HAVE] Solar Flare Radio Blackout (R-Scale) Monitor",
        "body": "As a **Communications Lead**, I want real-time monitoring of solar X-ray flux to track high-frequency radio blackout risks (R1-R5 scale).",
        "labels": ["Should Have", "Space Weather"]
    },
    {
        "title": "[SHOULD HAVE] Automated PDF Mission Incident Report Generator",
        "body": "As a **Mission Director**, I want one-click generation of PDF post-event reports summarizing solar particle peak times and executed commands.",
        "labels": ["Should Have", "Reporting"]
    },
    {
        "title": "[SHOULD HAVE] Manual Override Interlock Safety Window",
        "body": "As a **Mission Director**, I want a 10-second countdown delay on automated telecommands so that ground operators can abort accidental triggers.",
        "labels": ["Should Have", "Safety"]
    },
    {
        "title": "[SHOULD HAVE] Ground Station Visibility Horizon Calculator",
        "body": "As a **Fleet Lead**, I want calculation of ground station line-of-sight passes so that emergency telecommand windows can be prioritized.",
        "labels": ["Should Have", "Orbital Mechanics"]
    },
    {
        "title": "[SHOULD HAVE] Subsystem Power & Torque Constraint Solver",
        "body": "As a **Fleet Lead**, I want integer optimization ensuring auto-generated commands do not exceed satellite maximum power or wheel torque limits.",
        "labels": ["Should Have", "Optimization"]
    },
    {
        "title": "[SHOULD HAVE] Interactive Historical Space Weather Event Replay",
        "body": "As an **Analyst**, I want to replay historical solar storm datasets (e.g., 2003 Halloween Storm) to benchmark model accuracy.",
        "labels": ["Should Have", "Testing"]
    },

    # 🔵 COULD HAVE (5 Stories)
    {
        "title": "[COULD HAVE] Custom High-Contrast Mission Control Dark Mode UI",
        "body": "As an **Operator**, I want customizable UI themes optimized for low-light control room environments.",
        "labels": ["Could Have", "UI/UX"]
    },
    {
        "title": "[COULD HAVE] Automated Email / SMS Webhook Alerts",
        "body": "As an **On-Call Flight Surgeon**, I want emergency alerts pushed via Twilio/SendGrid when severe radiation storms trigger after hours.",
        "labels": ["Could Have", "Notifications"]
    },
    {
        "title": "[COULD HAVE] Voice-Command Search Bar for Satellite Telemetry",
        "body": "As an **Operator**, I want voice input to quickly search satellite status parameters.",
        "labels": ["Could Have", "UI/UX"]
    },
    {
        "title": "[COULD HAVE] Augmented Reality (AR) 3D Fleet Orbit Viewer",
        "body": "As a **Visitor**, I want an interactive AR viewer for satellite constellations during public mission showcases.",
        "labels": ["Could Have", "Visualization"]
    },
    {
        "title": "[COULD HAVE] Multi-Language Localization for ISRO Engineers",
        "body": "As an **Engineer**, I want UI labels toggleable between English and Hindi.",
        "labels": ["Could Have", "Localization"]
    },

    # ⚪ WON'T HAVE (2 Stories)
    {
        "title": "[WON'T HAVE] Physical Hardware-in-the-Loop Thruster Actuation",
        "body": "As a **System Architect**, I acknowledge physical thruster hardware firing will not be implemented in this software platform.",
        "labels": ["Won't Have", "Out of Scope"]
    },
    {
        "title": "[WON'T HAVE] Deep Space Interplanetary Relay Beyond L1",
        "body": "As a **System Architect**, I acknowledge telemetry routing for probes beyond Earth-Sun Lagrange Point 1 is out of scope.",
        "labels": ["Won't Have", "Out of Scope"]
    }
]


def upload_user_stories():
    """Uploads 25 MoSCoW User Stories to GitHub Issues via REST API."""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json"
    }

    print("=" * 70)
    print("🚀 SPARC-PM: Uploading 25 MoSCoW User Stories to GitHub Issues")
    print("=" * 70)

    success_count = 0
    for idx, story in enumerate(USER_STORIES, 1):
        data = json.dumps({
            "title": story["title"],
            "body": story["body"],
            "labels": story["labels"]
        }).encode("utf-8")

        req = urllib.request.Request(url, data=data, headers=headers)
        
        try:
            with urllib.request.urlopen(req) as response:
                res = json.loads(response.read().decode())
                print(f"[{idx}/25] ✅ Issue #{res['number']} Created: {story['title']}")
                success_count += 1
        except Exception as e:
            print(f"[{idx}/25] ❌ Error creating '{story['title']}': {e}")
            
        time.sleep(0.5)  # Rate limit protection

    print("=" * 70)
    print(f"🎉 Completed! Successfully published {success_count}/25 User Stories.")
    print(f"🔗 View your issues at: https://github.com/{REPO_OWNER}/{REPO_NAME}/issues")
    print("=" * 70)


if __name__ == "__main__":
    upload_user_stories()