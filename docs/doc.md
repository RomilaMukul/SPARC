# SPARC — Project Plan & Tracker

_Last updated: 16 Aug 2026_

Legend: ✅ Done · 🟡 In progress · ⬜ Not started · ⚠️ Blocked / needs a decision

---

## Phase 1 (DA1) — Foundation & Core Classification

**Goal:** Prove the concept works on real data with a basic working pipeline.

### Docs
| Task | Owner | Status | Notes |
|---|---|---|---|
| Problem statement | B | ✅ | In `SPARC_DA1_Report.docx` |
| Literature survey (15 refs) | A & B | ✅ | Verified against primary sources |
| Architecture diagram | B | ✅ | `architecture_diagram.png` |
| Feasibility note | A & B | ✅ | In report |
| Contribution matrix | A & B | ✅ | In report |
| Convert report to PDF | A | ⬜ | Required format per checklist |
| DA1 slide deck | A | ⬜ | Prompt ready, or generate directly |

### Code — Data Pipeline
| Task | Owner | Status | Notes |
|---|---|---|---|
| `fetch_celestrak.py` | B | 🟡 | Works logically; **fix indentation bug** before running |
| `parse_aditya.py` | B | ✅ | Reads real CDF if present, falls back to synthetic data |
| `requirements.txt` update | B | ⬜ | Missing `sgp4`, `cdflib`, `scikit-learn`, `requests` |
| GitHub repo + commits | A | ✅ | Repo live, structure in place |

### Code — Core Modules
| Task | Owner | Status | Notes |
|---|---|---|---|
| SGP4 + 3D Euclidean distance (`orbital_position.py`) | B | ⬜ | Listed in README as "next planned step" |
| Naive Bayes severity classifier (`naive_bayes_classifier.py`) | A (mentored by B) | ⬜ | Status "designed" only, no code yet |
| Backend skeleton (Flask/FastAPI) | B | ⬜ | Not started — currently Streamlit-only |

### Code — Frontend
| Task | Owner | Status | Notes |
|---|---|---|---|
| Dashboard skeleton (`app.py`) | A | 🟡 | KPI metrics + status view live; no risk table yet |
| Satellite position table view | A | ⬜ | Depends on `orbital_position.py` |
| Risk level display | A | ⬜ | Depends on Naive Bayes module |
| Wireframes (6 screens) | A | ✅ | SVGs generated |

**DA1 exit criteria:** Naive Bayes classifier + orbital position calculator both running, feeding a basic table in the dashboard showing current risk level and satellite positions. No 3D globe yet.

---

## Phase 2 (DA2) — Deep Learning & Spatial Visualization

**Goal:** Add predictive intelligence and the 3D visualization.

| Task | Owner | Status | Notes |
|---|---|---|---|
| LSTM — solar activity + crew dose forecast | B | ⬜ | |
| CNN-LSTM hybrid — predictive maintenance | B | ⬜ | Needs multimodal sensor fusion design |
| 3D Plotly/PyDeck globe (satellites + storm corridors) | B | ⬜ | Wireframe `03_3d_fleet_hazard.svg` already designed |
| A* priority scheduler | A (mentored by B) | ⬜ | |
| Frontend: forecast charts, prediction graphs | A | ⬜ | Depends on LSTM/CNN-LSTM output |
| Bayesian hyperparameter tuning (LSTM/CNN-LSTM) | B | ⬜ | |

**DA2 exit criteria:** Full predictive pipeline connected end-to-end — dosimetry forecast, maintenance prediction, 3D globe, A* action list — functional but not polished.

---

## Phase 3 (DA3) — Integration, Optimization & Polish

**Goal:** Production-ready demo, optimized models, full autonomous loop.

| Task | Owner | Status | Notes |
|---|---|---|---|
| Model optimization (pruning, quantization, transfer learning) | B | ⬜ | |
| Command packet generator (JSON + SHA-256) + override toggle | B | ⬜ | Wireframe `05_command_synthesizer.svg` ready |
| UI/UX polish (alert banners, severity colors, history timeline) | A | ⬜ | Wireframe `06_incident_analytics.svg` ready |
| End-to-end integration test (simulated storm event) | A & B | ⬜ | |
| Deployment (Docker Compose already set up) | A & B | 🟡 | `Dockerfile` + `docker-compose.yml` exist, untested end-to-end |
| Final report + demo script + viva prep | A & B | ⬜ | |

**DA3 exit criteria:** Fully working, deployed SPARC platform with live demo, final report, presentation.

---

## Known Issues / Decisions Needed

- ⚠️ `fetch_celestrak.py` has an indentation bug from a copy-paste — fix before first run.
- ⚠️ Aditya-L1 ISSDC/PRADAN portal access method not yet confirmed (manual download vs scriptable) — currently relying on the fallback synthetic generator in `parse_aditya.py`, which is fine for DA1 but should be revisited before DA2 if real CDFs aren't being used.
- ⬜ Decide: keep Streamlit as the frontend framework long-term, or move to Flask/FastAPI + separate frontend as originally planned? Current code has both `app.py` (Streamlit) and a backend skeleton listed as a to-do — pick one path to avoid duplicate work.

---

## Immediate Next Actions (this week)

1. Fix indentation in `fetch_celestrak.py`, run it, confirm `satellites_tle.json` output
2. Update `requirements.txt`
3. Build `orbital_position.py` (SGP4 + Euclidean distance)
4. Build `naive_bayes_classifier.py`
5. Wire both into `app.py` as a table view
6. Convert DA1 report to PDF, build slide deck
7. Commit + push all of the above