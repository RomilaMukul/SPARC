# 🚀 SPARC-PM: Space Weather Risk Classification & Predictive Maintenance Engine

> **Target Operations Center:** ISRO Mission Control Center Simulation (ISTRAC / MCF)  
> **Core Focus:** Real-time space weather defense, crew dosimetry, and sub-100ms autonomous command synthesis.

---

## 📑 1. Vision Document

### Project Name & Overview
**SPARC-PM** (*Space Priority Alert & Response Command Engine with Predictive Maintenance*) is an autonomous space operations decision-support platform designed to protect orbital assets and crewed space missions from severe space weather threats.

### Problem it Solves
Space weather events such as Coronal Mass Ejections (CMEs) and Solar Proton Events (SPEs) pose severe threats to orbital hardware and human spaceflight:
1. **Dosimetry Blind Spots:** Raw proton counts from sensors are not automatically integrated into cumulative absorbed dose curves for flight surgeons.
2. **Lack of 3D Spatial Awareness:** Generic alerts fail to pinpoint which specific satellites cross high-drag or radiation storm corridors.
3. **Emergency Response Latency:** Manual ground station workflows take 30+ minutes, while high-energy solar proton flares reach peak intensity in minutes.

### Target Users (Personas)
| Persona Name | Role & Domain | Primary Operational Goal |
| :--- | :--- | :--- |
| **Dr. Vikram Sharma** | Gaganyaan Flight Surgeon | Protect crew members from acute radiation sickness during solar proton events. |
| **Ananya Roy** | Fleet Operations Lead | Monitor orbital fleet health, atmospheric drag, and 3D storm proximity. |
| **Rajesh Kumar** | Subsystem Reliability Specialist | Detect early component degradation (CMOS noise, gyro drift, battery decay). |

### Vision Statement
> *"To pioneer an autonomous, zero-latency space weather defense and asset survivability system that empowers space agencies to protect human lives and multi-billion-dollar satellite constellations through predictive AI, 3D spatial mechanics, and closed-loop command automation."*

### Key Features / Goals
* **Gaganyaan Crew Dosimetry Engine:** Time-series solar flux forecasting and composite integration for cumulative radiation dose calculation.
* **3D Satellite Fleet Hazard Profiler:** SGP4 orbital propagation and 3D Euclidean spatial proximity mapping.
* **Predictive Maintenance Subsystem:** Anomaly detection and failure probability classification for satellite subsystems.
* **Closed-Loop Command Synthesizer:** Resource-constrained optimization generating telecommand packets signed with SHA-256 hashes.

### Success Metrics
* **Forecast Accuracy:** $\ge 90\%$ accuracy in predicting 6-hour solar proton flux trends.
* **Execution Latency:** Sub-100 millisecond response time for end-to-end processing.
* **Command Integrity:** $100\%$ validation rate on SHA-256 checksums.

### Assumptions & Constraints
* **Assumptions:** Continuous telemetry availability from solar payload feeds and updated daily Two-Line Element (TLE) satellite data.
* **Constraints:** Strict adherence to onboard satellite power ($P_{\text{max}}$) and torque ($T_{\text{max}}$) limits; mandatory 10-second manual override safety interlock.

---

## 🌿 2. Branching Strategy (GitHub Flow)

This project strictly follows **GitHub Flow** for software development lifecycle management:

1. **`main` Branch:** Always contains production-ready, deployable code. Direct commits to `main` are restricted.
2. **Feature Branches (`feature/<feature-name>`):** Created off `main` for developing individual capabilities (e.g., `feature/dev-setup`, `feature/dosimetry-engine`).
3. **Pull Requests (PRs):** All feature branches undergo verification before being merged back into `main`.

---

## 🛠️ 3. Local Development Tools

| Tool | Purpose | Version / Spec |
| :--- | :--- | :--- |
| **Python** | Core computational engine & machine learning models | `3.10+` |
| **Streamlit** | Interactive Mission Control GUI frontend | `1.30+` |
| **Docker Desktop** | Containerization runtime environment | `Latest` |
| **VS Code** | Code editor & integrated terminal | `Latest` |
| **Git / GitHub** | Version control, issue tracking, and branching | `2.40+` |

---

## 🚀 4. Quick Start – Local Development

### Option A: Local Python Setup
```bash
# 1. Clone repository
git clone [https://github.com/RomilaMukul/SPARC.git](https://github.com/RomilaMukul/SPARC.git)
cd SPARC

# 2. Create and activate virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run application
streamlit run src/ui/app.py