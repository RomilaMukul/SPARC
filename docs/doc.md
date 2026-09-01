# SPARC — Project Plan & Tracker

_Last updated: 16 Aug 2026_

Legend: [DONE] Done · [IN PROGRESS] In progress · [NOT STARTED] Not started · [BLOCKED] Blocked / needs a decision

---

## Phase 1 (DA1) — Foundation & Core Classification

**Goal:** Prove the concept works on real data with a basic working pipeline.

### Docs
| Task | Owner | Status | Notes |
|---|---|---|---|
| Problem statement | B | [DONE] | In `SPARC_DA1_Report.docx` |
| Literature survey (15 refs) | A & B | [DONE] | Verified against primary sources |
| Architecture diagram | B | [DONE] | `architecture_diagram.png` |
| Feasibility note | A & B | [DONE] | In report |
| Contribution matrix | A & B | [DONE] | In report |
| Convert report to PDF | A | [NOT STARTED] | Required format per checklist |
| DA1 slide deck | A | [NOT STARTED] | Prompt ready, or generate directly |

### Code — Data Pipeline
| Task | Owner | Status | Notes |
|---|---|---|---|
| `fetch_celestrak.py` | B | [IN PROGRESS] | Works logically; **fix indentation bug** before running |
| `parse_aditya.py` | B | [DONE] | Reads real CDF if present, falls back to synthetic data |
| `requirements.txt` update | B | [NOT STARTED] | Missing `sgp4`, `cdflib`, `scikit-learn`, `requests` |
| GitHub repo + commits | A | [DONE] | Repo live, structure in place |

### Code — Core Modules
| Task | Owner | Status | Notes |
|---|---|---|---|
| SGP4 + 3D Euclidean distance (`orbital_position.py`) | B | [NOT STARTED] | Listed in README as "next planned step" |
| Naive Bayes severity classifier (`naive_bayes_classifier.py`) | A (mentored by B) | [NOT STARTED] | Status "designed" only, no code yet |
| Backend skeleton (Flask/FastAPI) | B | [NOT STARTED] | Not started — currently Streamlit-only |

### Code — Frontend
| Task | Owner | Status | Notes |
|---|---|---|---|
| Dashboard skeleton (`app.py`) | A | [IN PROGRESS] | KPI metrics + status view live; no risk table yet |
| Satellite position table view | A | [NOT STARTED] | Depends on `orbital_position.py` |
| Risk level display | A | [NOT STARTED] | Depends on Naive Bayes module |
| Wireframes (6 screens) | A | [DONE] | SVGs generated |

**DA1 exit criteria:** Naive Bayes classifier + orbital position calculator both running, feeding a basic table in the dashboard showing current risk level and satellite positions. No 3D globe yet.

---

## Phase 2 (DA2) — Deep Learning & Spatial Visualization

**Goal:** Add predictive intelligence and the 3D visualization.

| Task | Owner | Status | Notes |
|---|---|---|---|
| LSTM — solar activity + crew dose forecast | B | [NOT STARTED] | |
| CNN-LSTM hybrid — predictive maintenance | B | [NOT STARTED] | Needs multimodal sensor fusion design |
| 3D Plotly/PyDeck globe (satellites + storm corridors) | B | [NOT STARTED] | Wireframe `03_3d_fleet_hazard.svg` already designed |
| A* priority scheduler | A (mentored by B) | [NOT STARTED] | |
| Frontend: forecast charts, prediction graphs | A | [NOT STARTED] | Depends on LSTM/CNN-LSTM output |
| Bayesian hyperparameter tuning (LSTM/CNN-LSTM) | B | [NOT STARTED] | |

**DA2 exit criteria:** Full predictive pipeline connected end-to-end — dosimetry forecast, maintenance prediction, 3D globe, A* action list — functional but not polished.

---

## Phase 3 (DA3) — Integration, Optimization & Polish

**Goal:** Production-ready demo, optimized models, full autonomous loop.

| Task | Owner | Status | Notes |
|---|---|---|---|
| Model optimization (pruning, quantization, transfer learning) | B | [NOT STARTED] | |
| Command packet generator (JSON + SHA-256) + override toggle | B | [NOT STARTED] | Wireframe `05_command_synthesizer.svg` ready |
| UI/UX polish (alert banners, severity colors, history timeline) | A | [NOT STARTED] | Wireframe `06_incident_analytics.svg` ready |
| End-to-end integration test (simulated storm event) | A & B | [NOT STARTED] | |
| Deployment (Docker Compose already set up) | A & B | [IN PROGRESS] | `Dockerfile` + `docker-compose.yml` exist, untested end-to-end |
| Final report + demo script + viva prep | A & B | [NOT STARTED] | |

**DA3 exit criteria:** Fully working, deployed SPARC platform with live demo, final report, presentation.

---

## Known Issues / Decisions Needed

- [BLOCKED] `fetch_celestrak.py` has an indentation bug from a copy-paste — fix before first run.
- [BLOCKED] Aditya-L1 ISSDC/PRADAN portal access method not yet confirmed (manual download vs scriptable) — currently relying on the fallback synthetic generator in `parse_aditya.py`, which is fine for DA1 but should be revisited before DA2 if real CDFs aren't being used.
- [NOT STARTED] Decide: keep Streamlit as the frontend framework long-term, or move to Flask/FastAPI + separate frontend as originally planned? Current code has both `app.py` (Streamlit) and a backend skeleton listed as a to-do — pick one path to avoid duplicate work.

---

## Immediate Next Actions (this week)

1. Fix indentation in `fetch_celestrak.py`, run it, confirm `satellites_tle.json` output
2. Update `requirements.txt`
3. Build `orbital_position.py` (SGP4 + Euclidean distance)
4. Build `naive_bayes_classifier.py`
5. Wire both into `app.py` as a table view
6. Convert DA1 report to PDF, build slide deck
7. Commit + push all of the above