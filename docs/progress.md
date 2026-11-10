# Project Progress

This is the implementation handoff log. Update it after each feature so another contributor can resume without repeating completed work.

## Current status

- **Stage:** Saved model inference, CSV input, forecast persistence and dashboard controls are implemented in code. The trained artifact bundle currently in `model_training/outputs/` predates the required inference sidecars.
- **Last updated:** 2026-11-10
- **Next action:** Run the updated notebook in Kaggle, download its new ZIP, import it, install backend requirements, then generate and review a fresh prediction in the dashboard.

## Completed

- [x] Mapped the assignment brief into 11 AI/data and development modules and wrote the implementation plan/checklist.
- [x] Selected React + Vite + TypeScript, FastAPI, SQLAlchemy and SQLite.
- [x] Added the Kaggle training notebook with daily series preparation, lag/rolling/calendar features, naive/seasonal-naive baselines, LightGBM/XGBoost candidates, rolling-origin validation and held-out tests.
- [x] Added an EDA section for trend and rolling mean, weekday/month patterns, distribution, calendar heatmap, store/family comparisons, outlier flags, and additive weekly decomposition; it writes an EDA summary and report figures.
- [x] Set the notebook to enable concurrent XGBoost jobs automatically when Kaggle detects two GPUs; LightGBM remains CPU by default because Kaggle's stock LightGBM build may not support GPU.
- [x] Added model-serving sidecars to notebook export: ordered `series_metadata.csv` and `inference_metadata.json` with features, holiday dates and calibration quantiles.
- [x] Added FastAPI model readiness, downloadable next-day input template, multipart fresh-prediction endpoint for 7/14/30-day horizons, holiday-date input and active-run forecast CSV download.
- [x] Implemented LightGBM and XGBoost artifact loading, CPU inference, matching recursive feature engineering, optional complete CSV updates, interval construction and validation errors.
- [x] Persisted predictions as new SQLite forecast runs while keeping incremental observed sales linked to the original history run.
- [x] Added the dashboard prediction workflow, artifact readiness state, input template and output download links, CSV upload, holiday dates, progress/success/error messages, rolling 7-day history line, family outlook, volatility, and low-volume families.
- [x] Updated the requirement checklist and added a model-serving implementation addendum to the plan.
- [x] Rewrote the README as an independent project document with dataset provenance, evaluation, setup, fresh-inference flow and limits.
- [x] Removed project-specific organization references from application code and docs; renamed the source brief to `assignment-brief.pdf`.

## Pending external/runtime actions

- [ ] Execute the updated notebook in Kaggle. The existing output folder lacks `series_metadata.csv` and `inference_metadata.json`, so fresh inference currently reports not ready until the bundle is refreshed.
- [ ] On Kaggle, select two T4 GPUs (when available) and confirm the updated automatic parallel mode detects and uses both for XGBoost windows.
- [ ] Download and import the refreshed bundle; generated outputs and the model binary remain Git-ignored due to their size.
- [ ] Install the new LightGBM/XGBoost backend requirements, then check `/api/model/status` and generate a prediction from the dashboard.
- [ ] Capture dashboard/report screenshots and complete any public demo or formal submission materials required by the assignment.
- [ ] Confirm the competition terms for intended sharing. The source data is not redistributed.

## Handoff details

- Run backend from `backend/` with `uvicorn app.main:app --reload`; run frontend from `frontend/` with `npm run dev`.
- Fresh prediction request: `POST /api/predictions` multipart fields `horizon_days` and optional `observations` CSV with `date,store_nbr,family,sales`.
- Uploaded rows must append consecutive days after saved history and contain exactly one observation for every trained store/family series on each day. The input template endpoint creates the complete next-day series list.
- Model files are loaded only from the configured artifact directory. ZIP imports copy an allowlist of files and never extract arbitrary paths.
- The currently supplied held-out results show LightGBM with lower MAE/RMSE than seasonal naive, while seasonal naive has lower sMAPE; this mixed outcome is stated in the README.
- The dataset ends at 2017-08-15. A forecast without an appended CSV uses that historical endpoint; it is a new inference run, not a live-data feed.
- Inventory levels and supplier lead times are unavailable, so the dashboard does not make stockout/reorder claims.
