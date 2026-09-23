# SPARC-PM: Space Weather Risk Classification & Predictive Maintenance Engine

**Space Priority Alert & Response Command Engine with Predictive Maintenance**
Target: ISRO Mission Control Center simulation (ISTRAC / MCF)

SPARC-PM is a mission-control decision-support prototype that classifies space-weather severity, assesses satellite fleet and crew radiation risk, predicts spacecraft subsystem failures, and generates a prioritized, resource-constrained response queue with verifiable telecommands.

> Space-weather telemetry → Risk intelligence → Fleet protection → Crew safety → Autonomous mission response.

---

## Overview

Severe space-weather events (CMEs, SPEs) threaten satellite electronics, orbital environments, and crew radiation safety. SPARC-PM addresses four problems:

1. **Space-weather classification** — telemetry → operational severity class (G0–G3)
2. **3D satellite hazard awareness** — TLE propagation vs. a dynamic storm corridor
3. **Predictive maintenance** — CNN-LSTM failure probability over a 72-hour horizon
4. **Automated response** — A*-scheduled, resource-constrained action queue with signed telecommands

It is a **software simulation** — no physical spacecraft hardware is involved.

---

## Key Features

| Module | What it does |
|---|---|
| **Space-Weather Classifier** | ML model mapping proton flux, solar-wind speed, IMF Bz, proton density, and dynamic pressure to G0–G3 |
| **3D Fleet Hazard Profiler** | SGP4 orbit propagation + dynamic hazard corridor + risk scoring, visualized in 3D |
| **CNN-LSTM Predictive Maintenance** | 1D CNN + LSTM over temporal telemetry (battery, temperature, gyro drift, dosimeter count, storm severity) |
| **Crew Radiation Dosimetry** | Deterministic model estimating peak/cumulative dose and EVA clearance (3.5 g/cm² Al-equivalent shielding) |
| **A\* Mission Response Scheduler** | Prioritizes protective actions under power/torque constraints |
| **Telecommand Integrity** | Cryptographic verification of generated command frames |

---

## Architecture

<img width="1254" height="1254" alt="architecture" src="https://github.com/user-attachments/assets/757beba1-0b50-4647-8d70-f06043da798b" />



## Data Sources

- **Aditya-L1 space-weather data** — 267,249 raw records, 15 features, May–Oct 2024
- **Synthetic spacecraft telemetry** — 72,000 records, 50 satellites, 1,440 timesteps each (1-min sampling), 5 features
- **Orbital/TLE data** — 8 satellites (6 LEO, 2 GEO): GAGANYAAN-1 (SIM), ISS, CARTOSAT-2F, OCEANSAT-3, RISAT-2B, EOS-04, INSAT-3DR, GSAT-24

Severity class distribution (G0/G1/G2/G3): 15.8% / 9.7% / 65.1% / 9.5%. Split 80/10/10 train/val/test.

---

## Results Summary

| Module | Metric | Result |
|---|---|---:|
| Space-weather classifier | Accuracy / Macro F1 | 99.87% / 99.81% |
| Historical event validation | Accuracy | 80.0% |
| CNN-LSTM predictive maintenance | Accuracy / F1 / ROC-AUC | 99.10% / 99.54% / 0.984 |
| Spatial hazard | Satellites evaluated | 8 (all Critical) |
| A* scheduler | Latency | 0.602 ms |
| Telecommand verification | Validation rate | 100% |
| End-to-end pipeline | Mean / P95 latency | 5.60 ms / 9.19 ms |

**Note on predictive maintenance:** the dataset is highly imbalanced (70,164 of 70,800 windows positive), so accuracy alone is not representative — see full confusion matrix in project docs.

**Note on dosimetry & proton-flux projection:** these are deterministic projection engines, not trained forecasting/dosimetry models against ground-truth splits.

---

## Tech Stack

Python 3.10+ · Scikit-learn · PyTorch · Pandas / NumPy · SGP4 · Plotly · Streamlit · Docker

---

## Project Structure

```
SPARC/
├── src/
│   ├── ui/app.py
│   ├── models/  data/  analysis/  scheduler/  telemetry/
├── data/
│   ├── space_weather/  satellite/  synthetic/
├── models/predictive_maint.pt
├── results/
│   ├── classification/  predictive_maintenance/  spatial_hazard/  dosimetry/  scheduler/
├── docs/
├── requirements.txt
├── Dockerfile
└── README.md
```

---

## Quick Start

```bash
git clone <SPARC_REPOSITORY_URL>
cd SPARC
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run src/ui/app.py
```

**Docker:**
```bash
docker build -t sparc-pm .
docker run -p 8501:8501 sparc-pm
```

---

## Limitations

- Synthetic telemetry used for predictive-maintenance evaluation
- Crew dosimetry and proton-flux projection are deterministic, not trained models
- No physical spacecraft hardware in the loop
- Predictive-maintenance data is highly class-imbalanced
- Operational deployment would need validation against certified space-agency telemetry, radiation models, and command protocols

## Future Work

- Train an LSTM/Transformer proton-flux forecasting model
- Integrate real-time space-weather feeds and richer atmospheric-drag modelling
- Add uncertainty estimation, fleet-level optimization, authenticated command channels
- Hardware-in-the-loop testing and a digital-twin mission-control environment
- Validate against additional historical CME/SPE events

---

## Team

**Nirvik Goswami** — Reg. No. 24BRS1315, CSE (AI & Robotics), VIT Chennai
**Romila Mukul** — Reg. No. 24BRS1294, CSE (AI & Robotics), VIT Chennai
