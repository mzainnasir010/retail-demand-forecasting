# Project Progress

This is the handoff log. Update it whenever functionality is implemented so another contributor can resume without repeating completed work.

## Current status

- **Stage:** Revised Kaggle training workflow prepared; application implementation has not started.
- **Last updated:** 2026-11-10
- **Next action:** Replace the previous Kaggle notebook with the revised model_training/demand_forecasting_kaggle.ipynb (or paste its updated cells), rerun from the top, and share rolling-window validation/test scores plus the new output bundle.

## Completed

- [x] Inspected the 20-page assignment brief and mapped requirements into 11 AI/development modules.
- [x] Selected React + Vite, FastAPI, and SQLite as the initial stack.
- [x] Created the detailed implementation plan in docs/project.md.
- [x] Created the requirement ground-truth checklist in docs/checklist.md.
- [x] Created a Kaggle-compatible notebook, then revised it after reviewing the first run to forecast each store-family series, include promotion/holiday context, and use rolling 16-day evaluation.
- [x] Created backend/, frontend/, and model_training/ project folders.
- [x] Checked notebook JSON structure and parsed all Python code cells successfully.
- [x] Set three rolling windows for validation and two final windows for held-out testing; report baseline and model scores on every window.
- [x] Added store-level and product-family-level fold metrics, plus a final 16-day forecast bundle output.
- [x] Rechecked notebook JSON and parsed all Python code cells after the revision.

## Not started

- [ ] Dataset attached, source terms verified, and data profile recorded.
- [ ] EDA, cleaning decisions, decomposition and data dictionary completed on the actual dataset.
- [ ] Model training completed and selected model/artifacts reviewed.
- [ ] FastAPI backend and SQLite persistence implemented.
- [ ] React dashboard implemented and connected to backend.
- [ ] Final README, screenshots, demo and submission details completed.

## Handoff notes

- The attached assignment PDF is the requirements source in the project root.
- Notebook expects the Store Sales competition files under /kaggle/input/competitions/store-sales-time-series-forecasting, including train.csv, test.csv, holidays_events.csv and stores.csv when present.
- The revised notebook predicts each store × family series, uses known promotions in backtests and test.csv for future promotion inputs, and compares three validation windows plus two held-out test windows. Check package availability, memory use, promotion coverage and all fold outputs in Kaggle; only notebook structure and Python syntax have been checked locally.
- Kaggle notebook code can create a ZIP in /kaggle/working and display a clickable file link. A browser download requires the user to click that link; a remote notebook cannot silently write files onto the user's local device.
- The two-T4 setting is not needed for the revised tree-model comparison; LightGBM/XGBoost acceleration depends on the Kaggle package build.
- Do not commit credentials, Kaggle tokens, raw data with unclear terms, or large model binaries.
