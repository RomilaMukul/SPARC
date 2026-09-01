🚀 Comprehensive Implementation Plan: SPARC Engine
The SPARC (Space Priority Alert & Response Command Engine) is an autonomous space operations decision-support framework designed to protect ISRO's satellite constellations and Gaganyaan human spaceflight missions from space weather threats (such as Coronal Mass Ejections and Solar Proton Events).
This document outlines the detailed architecture, mathematical algorithms, data schemas, deep learning models, decision scheduler, and multi-page Mission Control UI.
📑 Table of Contents
System Architecture & Data Flow
Algorithms & Mathematical Formulations
Algorithm 1: Gaussian Naive Bayes Space Weather Classifier
Algorithm 2: SGP4 Orbital Propagation & 3D Spatial Hazard Engine
Algorithm 3: Storm-Conditioned CNN-LSTM Predictive Maintenance
Algorithm 4: LSTM Solar Flux & Gaganyaan Dosimetry Forecaster
Algorithm 5: A* Priority Action Scheduler & Telecommand Synthesizer
Step-by-Step Code Component Breakdown
User Interface Design (Streamlit Multi-Page GUI)
Verification & Benchmark Plan
🏗️ 1. System Architecture & Data Flow
+-----------------------------------------------------------------------------------+|                                 STAGE 1: DATA INGESTION                           ||  - ISRO Aditya-L1 Level-2 (ASPEX/SWIS, SoLEXS, MAG) -> X-ray, Flux, Wind Speed, Bz ||  - NORAD / CelesTrak TLE API -> Active ISRO Satellites (NavIC, Cartosat, etc.)     ||  - Telemetry Generator -> Satellite Health (Battery, Temp, Gyro Drift, Radiation) |+----------------------------------------+------------------------------------------+                                         |                                         v+-----------------------------------------------------------------------------------+|                                STAGE 2: PREPROCESSING                             ||  - Time Synchronization (1-minute UTC intervals)                                  ||  - Feature Resampling, Imputation, MinMax Scaling                                 |+----------------------------------------+------------------------------------------+                                         |                                         v+-----------------------------------------------------------------------------------+|                                  STAGE 3: MODEL LAYER                             ||                                                                                   ||  [Alg 1: Naive Bayes]  [Alg 2: SGP4 3D Hazard]  [Alg 3: CNN-LSTM]   [Alg 4: LSTM]  ||  Space Weather         Satellite Proximity     Predictive Maint.   Solar & Crew   ||  Severity Level        to Storm Corridor        72h Failure Prob    6h Dose Curve  ||  (Calm/Watch/Warn/Emer) (Euclidean Dist Alert)  (Storm-Conditioned)  (Gaganyaan)   |+----------------------------------------+------------------------------------------+                                         |                                         v+-----------------------------------------------------------------------------------+|                         STAGE 4: DECISION & COMMAND SYNTHESIS                     ||  - Alg 5: A* Priority Scheduler -> Ranks (Satellite, Action) pairs by risk/cost   ||  - SHA-256 Telecommand Synthesizer -> Generates cryptographically signed commands |+----------------------------------------+------------------------------------------+                                         |                                         v+-----------------------------------------------------------------------------------+|                             STAGE 5: MISSION CONTROL GUI                          ||  - Streamlit Multi-Page Application (6 Interactive Operational Views)             |+-----------------------------------------------------------------------------------+
🔬 2. Algorithms & Mathematical Formulations
Algorithm 1: Gaussian Naive Bayes Space Weather Classifier
Objective: Rapidly classify incoming solar particle & magnetic telemetry into 4 severity classes: $$\mathcal{C} \in {\text{Calm (0)}, \text{Watch (1)}, \text{Warning (2)}, \text{Emergency (3)}}$$
Input Vector: $$\mathbf{x} = \left[ F_{\text{Xray}}, v_{\text{sw}}, |B|, F_{\text{SEP}} \right]^T$$
$F_{\text{Xray}}$: X-ray flux ($\text{W/m}^2$) from SoLEXS
$v_{\text{sw}}$: Solar wind speed ($\text{km/s}$) from ASPEX/SWIS
$|B|$: Interplanetary Magnetic Field magnitude ($\text{nT}$) from MAG
$F_{\text{SEP}}$: Solar Energetic Particle flux ($\text{pfu}$)
Mathematical Formulation: Using Bayes' Theorem, the posterior probability for class $c_k$ is: $$P(C = c_k \mid \mathbf{x}) = \frac{P(C = c_k) \prod_{i=1}^{4} P(x_i \mid C = c_k)}{P(\mathbf{x})}$$ Assuming a Gaussian likelihood for feature $x_i$: $$P(x_i \mid C = c_k) = \frac{1}{\sqrt{2\pi \sigma_{k,i}^2}} \exp\left( -\frac{(x_i - \mu_{k,i})^2}{2\sigma_{k,i}^2} \right)$$ The predicted class is: $$\hat{c} = \arg\max_{c_k} P(C = c_k \mid \mathbf{x})$$
Why Gaussian Naive Bayes?: Extremely lightweight (sub-1ms execution), transparent for mission operators, and handles small training samples robustly without overfitting.
Algorithm 2: SGP4 Orbital Propagation & 3D Spatial Hazard Engine
Objective: Compute the 3D position of every ISRO satellite in the fleet and evaluate spatial overlap/proximity with solar storm corridors.
Input: Two-Line Element (TLE) orbital sets from CelesTrak and target UTC timestamp $t$.
Step-by-Step Propagation:
Parse TLE parameters (inclination $i$, right ascension of ascending node $\Omega$, eccentricity $e$, argument of perigee $\omega$, mean anomaly $M$, mean motion $n$).
Execute SGP4 numerical integration algorithm to calculate orbital state vectors in the Earth-Centered Inertial (ECI / TEME) reference frame: $$\mathbf{r}{\text{ECI}}(t) = [x{\text{eci}}, y_{\text{eci}}, z_{\text{eci}}]^T, \quad \mathbf{v}_{\text{ECI}}(t) = [v_x, v_y, v_z]^T$$
Transform ECI coordinates to Earth-Centered Earth-Fixed (ECEF) coordinates accounting for Earth rotation angle $\theta_{\text{GST}}$: $$\begin{bmatrix} x_{\text{ECEF}} \ y_{\text{ECEF}} \ z_{\text{ECEF}} \end{bmatrix} = \begin{bmatrix} \cos\theta & \sin\theta & 0 \ -\sin\theta & \cos\theta & 0 \ 0 & 0 & 1 \end{bmatrix} \begin{bmatrix} x_{\text{ECI}} \ y_{\text{ECI}} \ z_{\text{ECI}} \end{bmatrix}$$
3D Euclidean Distance to Storm Corridor: Model storm hazard corridor as a spatial geometric envelope $\mathcal{S}{\text{storm}}$ centered at coordinates $(x_c, y_c, z_c)$ with dynamic radius $R{\text{storm}}(t)$ proportional to solar wind speed $v_{\text{sw}}$: $$d_j(t) = \sqrt{(x_{\text{ECEF}, j} - x_c)^2 + (y_{\text{ECEF}, j} - y_c)^2 + (z_{\text{ECEF}, j} - z_c)^2}$$ $$\text{Hazard Ratio } H_j = \max\left(0, 1 - \frac{d_j(t)}{R_{\text{storm}}(t)}\right)$$
Algorithm 3: Storm-Conditioned CNN-LSTM Predictive Maintenance
Objective: Predict the 72-hour component failure probability $P_{\text{fail}}$ for each satellite (battery decay, gyro drift, thermal stress).
Input Tensor: A rolling telemetry window of 24 time steps (24 minutes) across 4 telemetry channels + 1 Storm Conditioning Channel (the Naive Bayes posterior vector $P(C \mid \mathbf{x})$): $$\mathbf{X}_{\text{telemetry}} \in \mathbb{R}^{24 \times 5}$$
Channel 1: Battery Voltage ($V_{\text{bat}}$)
Channel 2: Subsystem Temperature ($T_{\text{sys}}$)
Channel 3: Gyroscope Drift Rate ($\omega_{\text{drift}}$)
Channel 4: Onboard Dosimeter Count ($D_{\text{onboard}}$)
Channel 5: Storm Severity Index ($S_{\text{storm}} \in [0, 3]$ from Naive Bayes)
Architecture:
Input Tensor (24 x 5)       │       ▼1D Convolutional Layer (Filters=32, Kernel Size=3, ReLU activation)[Extracts local cross-sensor correlations]       │       ▼1D Max Pooling Layer (Pool Size=2)       │       ▼LSTM Layer (Hidden Units=64, Return Sequences=False)[Learns temporal decay and degradation trends]       │       ▼Dense Fully Connected Layer (Units=32, ReLU)       │       ▼Output Layer (1 Unit, Sigmoid activation) ──> P_fail in [0, 1]
Novelty: Existing satellite failure models evaluate telemetry in isolation. SPARC conditions component health forecasts on incoming space weather severity, directly modeling storm-induced hardware stress.
Algorithm 4: LSTM Solar Flux & Gaganyaan Dosimetry Forecaster
Objective: Forecast 6-hour ahead solar proton flux trends and compute cumulative radiation absorbed dose ($\mu\text{Sv/hr}$) scaled to Gaganyaan cabin shielding specs ($3.5\text{ g/cm}^2$ Aluminum equivalent).
Formulation: Given historical solar flux sequence $\mathbf{F} = [F_{t-360}, \dots, F_t]$, the LSTM model predicts future flux sequence $\hat{\mathbf{F}} = [\hat{F}{t+1}, \dots, \hat{F}{t+360}]$.
The cumulative absorbed dose $D_{\text{crew}}$ for astronauts over exposure period $T$ is computed using composite flux integration: $$D_{\text{crew}}(T) = K_{\text{shield}} \cdot \int_{0}^{T} \left( \sum_{e} \Phi_e(t) \cdot S_e \right) dt$$ where $K_{\text{shield}}$ is the attenuation factor for Gaganyaan cabin wall thickness, $\Phi_e(t)$ is proton flux per energy bin $e$, and $S_e$ is the linear energy transfer (LET) stopping power in human tissue.
Algorithm 5: A* Priority Action Scheduler & Telecommand Synthesizer
Objective: Rank and prioritize corrective telecommands across 50+ satellites under strict operator response time limits and onboard hardware constraints.
Graph Representation:
Nodes: $(s_i, a_k)$ pairs representing Satellite $i$ and Candidate Action $k$ (e.g., Safe Mode, Orbit Adjust, Payload Power-Down, Payload Shielding Tilt).
Edge Cost Function $g(n)$: $$g(n) = w_1 \cdot (1 - \text{Proximity Distance}) + w_2 \cdot P_{\text{fail}} + w_3 \cdot \text{Asset Criticality}$$ where $w_1 = 0.4$, $w_2 = 0.4$, $w_3 = 0.2$.
Admissible Heuristic $h(n)$: $$h(n) = \frac{d_{\text{storm}}}{\text{Relative Velocity } v_{\text{rel}}} = \text{Estimated Time-to-Storm-Entry (seconds)}$$
Total Evaluation Function: $$f(n) = g(n) + h(n)$$
Telecommand Synthesis & SHA-256 Signing: When an action is scheduled, SPARC builds a binary command frame and appends a cryptographic SHA-256 checksum: $$\text{Payload} = \text{SAT_ID} \parallel \text{CMD_CODE} \parallel \text{TIMESTAMP} \parallel \text{PARAMS}$$ $$\text{Checksum} = \text{SHA256}(\text{Payload} \parallel \text{SECRET_KEY})$$
🛠️ 3. Step-by-Step Code Component Breakdown
d:\projects\sparc\├── data/│   ├── raw/                       # Raw ISSDC CDF & CelesTrak TLE files│   └── processed/                 # Telemetry CSVs, satellite JSONs├── src/│   ├── data/│   │   ├── ingest_aditya.py       # [NEW] ISRO CDF Level-2 Science parser│   │   ├── fetch_tle.py           # [NEW] CelesTrak ISRO fleet TLE grabber│   │   ├── telemetry_simulator.py # [NEW] Synthetic satellite health generator│   │   └── preprocessor.py        # [NEW] Time-sync, scaling, & tensor formatting│   ├── models/│   │   ├── severity_classifier.py # [NEW] Gaussian Naive Bayes implementation│   │   ├── spatial_hazard.py      # [NEW] SGP4 orbital propagator & 3D Euclidean distance│   │   ├── predictive_maint.py    # [NEW] PyTorch CNN-LSTM model class & trainer│   │   └── crew_dosimetry.py      # [NEW] PyTorch LSTM solar trend & dose calculator│   ├── scheduler/│   │   └── a_star_scheduler.py    # [NEW] A* search queue & SHA-256 command packager│   ├── evaluation/│   │   └── benchmark_eval.py      # [NEW] Historical storm validator (May/Oct 2024)│   └── ui/│       ├── app.py                 # [MODIFY] Main Streamlit entrance & layout│       └── components/            # [NEW] UI tab view rendering functions└── docs/    └── wireframes/                # Generated SVG dashboard designs
Detailed Description of Key Files
1. src/data/ingest_aditya.py
Function: parse_aditya_cdf_dataset(raw_dir, output_csv)
Reads .cdf files from data/raw/SWIS-ISSDC/positive and negative directories.
Extracts zVariables: Epoch, proton_flux, sw_speed, bz_field, xray_flux.
Fills missing values using linear interpolation and exports clean tabular CSV.
2. src/data/telemetry_simulator.py
Function: generate_fleet_telemetry(num_satellites=50, timesteps=1440)
Simulates telemetry data for 50 ISRO satellites (Cartosat-3, Oceansat-3, NavIC-1I, GSAT-11, RISAT-2BR1, etc.).
Perturbs nominal values based on current space weather severity level (e.g. higher radiation counts and gyro drift during Emergency state).
3. src/models/severity_classifier.py
Class: SpaceWeatherClassifier
Implements fit(X, y) and predict_proba(X).
Trained on historical NOAA / ISRO storm records.
Provides quick predictions for live solar metrics.
4. src/models/spatial_hazard.py
Class: SpatialHazardEngine
Method propagate_fleet(tle_json, timestamp): Propagates satellite TLEs using sgp4.api.Satrec.
Method compute_storm_intersections(satellite_coords, storm_center, storm_radius): Returns list of satellites inside or approaching storm corridors.
5. src/models/predictive_maint.py
Class: CNNLSTMPredictor(nn.Module)
PyTorch implementation of the 1D CNN + LSTM architecture.
Trains on synthetic telemetry + storm severity conditioning channel.
Outputs failure probabilities $P_{\text{fail}} \in [0, 1]$.
6. src/scheduler/a_star_scheduler.py
Class: AStarActionScheduler
Method solve(fleet_hazards, failure_probabilities, power_budget): Runs A* priority search.
Returns ordered list of telecommand objects: {"rank": 1, "sat_id": "CARTOSAT-3", "action": "ENTER_SAFE_MODE", "sha256": "e3b0c442..."}.
🖥️ 4. User Interface Design (Streamlit Multi-Page GUI)
The GUI in src/ui/app.py will feature a dark space-themed layout with 6 navigation tabs:
┌────────────────────────────────────────────────────────────────────────────────────────┐| 🚀 SPARC-PM | ISRO Mission Control Center                                 UTC: 16:55:00|├────────────────────────────────────────────────────────────────────────────────────────┤| [1. Overview]  [2. Dosimetry]  [3. 3D Fleet]  [4. Maintenance]  [5. Commands]  [6. Reports]|└────────────────────────────────────────────────────────────────────────────────────────┘
Tab 1: Executive Overview (01_executive_overview.svg)
Metrics: Fleet Status (NOMINAL / ALERT), Active Satellites (50/50), Peak Solar Proton Flux (pfu), Gaganyaan Cabin Radiation Rate ($\mu\text{Sv/hr}$).
Real-time space weather alert banner & solar wind speed gauge.
Tab 2: Gaganyaan Crew Dosimetry (02_gaganyaan_dosimetry.svg)
Interactive Plotly time-series chart showing 6-hour forecast solar flux and cumulative astronaut absorbed dose curves.
Safety threshold line ($20\text{ mSv}$ career limit / acute sickness warning).
Tab 3: 3D Fleet Hazard Profiler (03_3d_fleet_hazard.svg)
Interactive 3D orbital globe visualizing 50 satellite orbits and dynamic red storm hazard corridor envelopes.
Distance-to-corridor table with warning highlights for high-risk assets.
Tab 4: Subsystem Predictive Maintenance (04_predictive_maintenance.svg)
Component degradation heatmaps (Battery degradation, Gyro drift, CMOS sensor noise).
Top 5 highest risk satellites with predicted 72-hour failure probability $P_{\text{fail}}$.
Tab 5: Closed-Loop Command Synthesizer (05_command_synthesizer.svg)
A*-ranked recommended action queue.
Interactive "Execute Command" trigger button with verified SHA-256 signature generation.
Tab 6: Incident Analytics & Model Benchmarks (06_incident_analytics.svg)
Evaluation metrics table (Recall, F1, TSS) validated on May 2024 & Oct 2024 storm events.
Model ablation comparison charts (A* vs. Priority Queue, Naive Bayes vs. Logistic Regression).
🧪 5. Verification & Benchmark Plan
Automated Testing Suite
Data Ingestion Verification:
Test ingest_aditya.py against sample CDF files to confirm zero missing timestamps and proper numeric extraction.
SGP4 Accuracy Test:
Verify generated ECEF coordinates match known orbital ephemeris within $< 1.0\text{ km}$ tolerance.
Model Performance Validation:
Naive Bayes: Validate $\ge 90%$ recall on historical solar flare events.
CNN-LSTM: Verify loss convergence during PyTorch training loop.
A Scheduler*: Ensure zero state deadlocks and verifying SHA-256 checksum format.
Manual UI Verification
Launch Streamlit app (streamlit run src/ui/app.py).
Verify seamless tab switching across all 6 views.
Verify interactive filtering and command execution simulations.