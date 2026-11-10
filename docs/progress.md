# Project Progress

This is the handoff log. Update it whenever functionality is implemented so another contributor can resume without repeating completed work.

## Current status

- **Stage:** Final Kaggle notebook outputs integrated into FastAPI/SQLite and React dashboard; mock-data mode removed.
- **Last updated:** 2026-11-10
- **Next action:** Launch both local servers and review the dashboard. Refresh output data by running the importer from backend when a new Kaggle run is available.

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
- [x] Implemented the FastAPI/SQLite backend with health, entity, dashboard and latest-run endpoints.
- [x] Added generated sample history and forecasts so the app can run before model files arrive.
- [x] Added a Kaggle output-bundle importer and updated the notebook to export one year of history for dashboard use.
- [x] Added backend/frontend setup and model-bundle import instructions to the root README.
- [x] Built the React + Vite dashboard with overview, forecast chart, store/family filters, model comparison and demand insight views.
- [x] Connected the dashboard to the FastAPI service and added loading, API error and sample-data states.
- [x] Added responsive layouts and local API proxy configuration.
- [x] Replaced the earlier notebook with the user's final `model_training/demand-forecasting-notebook.ipynb`.
- [x] Imported the final 30-day forecast and rolling-window actuals output formats, along with metrics, family outlook, cleaning metadata, business insights, and figure paths.
- [x] Connected the API to `model_training/outputs`, enabled first-start import, served exported figures, and removed mock-data seeding and UI messaging.
- [x] Added 7/14/30-day dashboard horizon controls, final-run metrics, family outlook and evaluation figures.
- [x] Imported the local output folder and confirmed the dashboard response validates with trained model metrics, 120 chart points, 33 family outlook rows and all four exported figures.
- [x] Confirmed backend modules compile and the React production build succeeds.

## Not started

- [ ] Dataset attached, source terms verified, and data profile recorded.
- [ ] EDA, cleaning decisions, decomposition and data dictionary completed on the actual dataset.
- [x] Model training completed and selected model/artifacts reviewed (final LightGBM notebook outputs supplied by user).
- [x] FastAPI backend and SQLite persistence implemented.
- [x] React dashboard implemented and connected to backend.
- [x] Updated README for final output layout and local startup/import workflow.
- [ ] Screenshots, demo and submission details completed.

## Handoff notes

- The attached assignment PDF is the requirements source in the project root.
- Notebook expects the Store Sales competition files under /kaggle/input/competitions/store-sales-time-series-forecasting, including train.csv, test.csv, holidays_events.csv and stores.csv when present.
- The revised notebook predicts each store × family series, uses known promotions in backtests and test.csv for future promotion inputs, and compares three validation windows plus two held-out test windows. Check package availability, memory use, promotion coverage and all fold outputs in Kaggle; only notebook structure and Python syntax have been checked locally.
- Kaggle notebook code can create a ZIP in /kaggle/working and display a clickable file link. A browser download requires the user to click that link; a remote notebook cannot silently write files onto the user's local device.
- The two-T4 setting is not needed for the revised tree-model comparison; LightGBM/XGBoost acceleration depends on the Kaggle package build.
- Backend commands and route behavior are documented in the root README. Frontend dependencies are locked in frontend/package-lock.json.
- The live Kaggle outputs are present under `model_training/outputs/`; generated CSVs and model artifacts are git-ignored due to their size. The local app auto-imports them on first launch. A fresh clone needs the output folder supplied separately.
- The final notebook/output bundle was supplied already run by the user; this implementation session validated/imported those output files and did not repeat GPU training.
- Do not commit credentials, Kaggle tokens, raw data with unclear terms, or large model binaries.
