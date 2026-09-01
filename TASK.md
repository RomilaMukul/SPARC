# SPARC Project — Master Task & Bug Resolution Plan (`TASK.md`)

> **Project:** Space Particle Radiation Alert & Resilience Center (SPARC-PM)  
> **Status:** Active Development (DA2 Benchmark & Integration Phase)  
> **Last Updated:** September 2026  

---

## 1. Executive Summary & Current System Status

The SPARC platform integrates real-time NOAA/Aditya-L1 space weather telemetry, satellite orbital propagation (SGP4), machine learning risk classifiers, 1D-CNN+LSTM predictive maintenance models, and an A* telecommand scheduler. 

While core dynamic telemetry fetching and baseline evaluation pipelines are operational, several **critical machine learning convergence/imbalance issues**, **UI interactivity gaps**, and **testing deficiencies** remain to be addressed prior to final submission.

---

## 2. Outstanding Bugs & Technical Debt

### A. Machine Learning Pipeline Bugs
- [ ] **Logistic Regression Convergence Failure:** `LogisticRegression` in `src/evaluate_baselines.py` throws `ConvergenceWarning: lbfgs failed to converge after 1000 iteration(s)`. Requires `StandardScaler` feature normalization and `max_iter=3000`.
- [ ] **Severe Class Imbalance in Space Weather Classifier:**
  - `Warning` class F1-score is currently `0.00` (Precision: `0.00`, Recall: `0.00`).
  - `Emergency` class Recall is `0.20` (only 1 out of 5 severe events detected).
  - *Root Cause:* Solar telemetry dataset is dominated by `Calm` conditions (~80%+).
  - *Fix Required:* Implement SMOTE (Synthetic Minority Over-sampling Technique) or class-weighted loss (`class_weight='balanced'`) in `src/naive_bayes_classifier.py`.
- [ ] **Subsystem Predictive Maintenance Underperformance:**
  - SPARC 5-Channel Model B F1-score is `0.3654` vs SOTA baseline (Muthukumar & Philip [11]) of `0.8800`.
  - *Fix Required:* Normalize sensor inputs (Battery SoC, Gyro Drift, CMOS noise), apply `BCEWithLogitsLoss(pos_weight=...)`, and tune CNN-LSTM hyperparameters.
- [ ] **Single-Class Telemetry Fallback Triggering:**
  - When live NOAA telemetry is uniform/calm, `assign_ground_truth()` collapses to a single label. Although fallback to percentile-based labeling works, dataset variance monitoring needs smoothing to avoid artificial metric jumps.

### B. UI / Dashboard Bugs & Performance Issues
- [ ] **3D Globe Rerender Flickering:** Re-instantiating Plotly 3D scatter plots inside Streamlit fragment loops (`run_every=refresh_rate`) causes visual flicker and browser memory buildup. Needs figure caching (`@st.cache_data` or persistent state).
- [ ] **State Loss on Table Filtering:** Interactive table multiselect filters and search queries reset state during background fragment reruns.
- [ ] **Static Telecommand Display:** The scheduler tab reads static pre-generated JSON rather than executing live A* scheduling when telemetry alerts are triggered.

---

## 3. Required Machine Learning Enhancements

### Task 3.1: Classifier Re-Balancing & Optimization
- **File:** `src/naive_bayes_classifier.py`
- **Actions:**
  - Add `StandardScaler` preprocessing pipeline.
  - Implement class weighting and sample oversampling for `Warning` and `Emergency` space weather tiers.
  - Target metrics: `Emergency` Recall $\ge 0.70$, Overall Weighted F1 $\ge 0.82$.

### Task 3.2: 5-Channel CNN-LSTM Model Refinement
- **File:** `src/predictive_maintenance.py`
- **Actions:**
  - Scale input telemetry channels (SoC, Gyro, CMOS, Temp, Solar Severity) using `MinMaxScaler` / `StandardScaler`.
  - Introduce weighted binary cross-entropy loss to handle anomaly sparsity.
  - Bridge performance gap toward SOTA benchmark (Target F1 $\ge 0.75$, AUC $\ge 0.88$).

### Task 3.3: Solar Flux Forecaster Tuning
- **File:** `src/solar_dose_forecaster.py`
- **Actions:**
  - Add residual connection and sequence normalization to 2-layer PyTorch LSTM.
  - Ensure validation RMSE remains under BLEO paper baseline ($\le 12.50\text{ pfu}$).

### Task 3.4: Baseline Harness Optimization
- **File:** `src/evaluate_baselines.py`
- **Actions:**
  - Fix scikit-learn convergence warnings.
  - Update benchmark report markdown export with improved performance metrics.

---

## 4. Required UI & Front-End Enhancements

### Task 4.1: Solar Storm Event Simulator & Injector
- **File:** `src/ui/app.py`
- **Actions:**
  - Add a **"Solar Storm Simulator"** control in the sidebar.
  - Enable mission operators to override live telemetry with synthetic severe storm events (e.g., May 2024 Geomagnetic Storm: $v_{sw} = 850\text{ km/s}$, $B_z = -22\text{ nT}$, Proton Flux $= 10^3\text{ pfu}$).
  - Verify immediate HUD alert status transition (`Calm` $\rightarrow$ `EMERGENCY`).

### Task 4.2: Dynamic Closed-Loop Telecommand Triggering
- **File:** `src/ui/app.py`, `src/astarscheduler.py`
- **Actions:**
  - Add an interactive **"Run Autonomous A* Mitigation"** action button in the Telecommand Scheduler tab.
  - Execute A* graph search live, generate SHA-256 signed commands, and display execution results in real-time.

### Task 4.3: Mission Telemetry & Hazard Export
- **File:** `src/ui/app.py`
- **Actions:**
  - Add CSV and JSON download buttons for:
    1. Active Fleet Orbital Telemetry & Hazard Distance Logs.
    2. Authenticated Telecommand Schedule.
    3. Model Benchmark & Ablation Report.

### Task 4.4: 3D Globe Visual Polish & Caching
- **File:** `src/globe_visualization.py`
- **Actions:**
  - Cache base Earth sphere mesh and orbital trajectory traces.
  - Smooth camera transitions and add hover tooltips for SAA (South Atlantic Anomaly) and Auroral Oval hazard zones.

---

## 5. Testing & DevOps Infrastructure

- [ ] **Unit & Integration Test Suite (`tests/`):**
  - Create `tests/test_telemetry.py` to test live NOAA URL fetching & fallback mechanisms.
  - Create `tests/test_classifier.py` to test Naive Bayes inference & metric validation.
  - Create `tests/test_scheduler.py` to test A* search runtime (< 100ms constraint) and SHA-256 signature generation.
- [ ] **Automated Pipeline Execution Script (`run_pipeline.sh`):**
  - Script to run data fetching, model training, evaluation harness, and launch Streamlit dashboard.

---