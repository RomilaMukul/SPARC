<div align="center">

# 🚀 SPARC-PM
### **Space Weather Risk Classification & Predictive Maintenance Engine**

*Autonomous Space Operations, AI-Driven Radiation Dosimetry, & Orbital Asset Survivability for ISRO Missions*

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![Domain](https://img.shields.io/badge/ISRO-Aditya--L1%20Telemetry-FF9933?style=for-the-badge)](https://www.isro.gov.in)
[![Status](https://img.shields.io/badge/Build-Passing-brightgreen?style=for-the-badge)]()

---

</div>

> [!NOTE]
> **Target Operations Center:** ISRO Mission Control Center Simulation (ISTRAC / MCF)  
> **Core Focus:** Real-time space weather defense, crew dosimetry, and sub-100ms autonomous command synthesis.

---

## 📌 Table of Contents
- [Executive Overview](#-1-executive-overview)
- [Problem Statement](#-2-problem-statement)
- [Target User Personas](#-3-target-user-personas)
- [Core System Features](#-4-core-system-features)
- [Success Metrics & Constraints](#-5-success-metrics--constraints)
- [Quick Start Guide](#-6-quick-start-guide)

---

## 📑 1. Executive Overview

**SPARC-PM** is an enterprise-grade autonomous space operations platform designed to protect orbital assets and crewed space missions from severe space weather threats.

By fusing real-time interplanetary telemetry streams from **ISRO's Aditya-L1** payloads (**PAPA**, **ASPEX**, **MAG**) with satellite **Two-Line Element (TLE)** orbital ephemeris, SPARC-PM bridges the gap between passive monitoring and millisecond-level threat response.

[ Aditya-L1 Telemetry ] + [ CelesTrak Satellite TLEs ]
                             │
                             ▼
                 ┌───────────────────────┐
                 │   SPARC-PM AI Engine  │
                 └───────────────────────┘
                             │
     ┌───────────────────────┼───────────────────────┐
     ▼                       ▼                       ▼
🛡️ Crew Dosimetry       📡 3D Fleet Twin       ⚡ Auto Commands
(Gaganyaan Radiation)  (SGP4 Spatial Risk)    (CCSDS JSON Signed)

---

## 🛑 2. Problem Statement

Space weather events such as Coronal Mass Ejections (CMEs) and Solar Proton Events (SPEs) pose severe threats to orbital hardware and human spaceflight. Current ground station workflows suffer from three critical bottlenecks:

1. 🙈 **Dosimetry Blind Spots:** Raw proton counts from sensors are not automatically integrated into cumulative absorbed dose curves for flight surgeons.
2. 🌐 **Lack of 3D Spatial Awareness:** Generic alerts fail to pinpoint which specific satellites in a constellation cross high-drag or radiation storm corridors.
3. ⏱️ **Emergency Response Latency:** Manual ground station workflows take 30+ minutes, while high-energy solar proton flares reach peak intensity in minutes.

---

## 👥 3. Target User Personas

| Avatar | Persona Name | Role & Domain | Primary Operational Goal |
| :---: | :--- | :--- | :--- |
| 🧑‍⚕️ | **Dr. Vikram Sharma** | Gaganyaan Flight Surgeon | Protect *Gaganauts* from acute radiation sickness during solar proton events. |
| 🛰️ | **Ananya Roy** | Fleet Operations Lead | Monitor orbital fleet health, atmospheric drag, and 3D storm proximity. |
| 🛠️ | **Rajesh Kumar** | Subsystem Reliability Specialist | Detect early component degradation (CMOS noise, gyro drift, battery decay). |

---

## ✨ 4. Core System Features

### 🛡️ Module 1: Gaganyaan Crew Radiation Shield Engine
* **LSTM Flux Forecasting:** 2-layer LSTM model predicts 6-hour solar proton flux curves $\hat{\Phi}(t)$ from historical Aditya-L1 observations.
* **Simpson's Composite Dosimetry:** Calculates cumulative absorbed dose $D$ in milliSieverts ($\text{mSv}$):
  $$D = \int_{0}^{T} \hat{\Phi}(t) \cdot S(E) \, dt$$
* **Finite State Machine Triage:**
  * 🟢 **GREEN:** $D < 1.0\text{ mSv}$ — Nominal Operations
  * 🟡 **YELLOW:** $1.0 \le D < 10.0\text{ mSv}$ — Elevate Shielding / Suspend EVAs
  * 🔴 **RED:** $D \ge 10.0\text{ mSv}$ — Emergency Storm Shelter Alert

### 📡 Module 2: 3D Satellite Fleet Hazard Profiler
* **SGP4 Orbital Propagator:** Converts NORAD/CelesTrak TLE parameters into Earth-Centered Earth-Fixed (ECEF) Cartesian coordinates $(x_s, y_s, z_s)$.
* **3D Spatial Euclidean Proximity:** Measures exact separation $d$ relative to active magnetospheric storm centers $(x_c, y_c, z_c)$:
  $$d = \sqrt{(x_s - x_c)^2 + (y_s - y_c)^2 + (z_s - z_c)^2}$$

### ⚡ Module 3: Closed-Loop Command Synthesizer
* **Constrained $A^*$ / ILP Optimization:** Selects recovery maneuvers under onboard power ($P_{\text{max}}$) and torque ($T_{\text{max}}$) limits.
* **CCSDS Compliance:** Synthesizes machine-executable JSON telecommand packets signed with **SHA-256 integrity hashes**.

---

## 📈 5. Success Metrics & Constraints

> [!IMPORTANT]
> * **Forecast Accuracy:** $\ge 90\%$ accuracy in predicting 6-hour solar proton flux curves.
> * **Execution Latency:** Sub-100 millisecond response time for end-to-end command generation.
> * **Command Integrity:** $100\%$ validation rate on SHA-256 checksum signatures.
> * **Safeguards:** 5-second manual override safety window before automated uplink execution.

---

## 🛠️ 6. Quick Start Guide

### 1. Local Python Setup
```bash
# Clone repository
git clone [https://github.com/RomilaMukul/SPARC.git](https://github.com/RomilaMukul/SPARC.git)
cd SPARC

# Install dependencies
pip install -r requirements.txt

# Run Dashboard
streamlit run src/ui/app.py
