# Project Plan — AI-Powered Demand Forecasting

## Project goal

Build a reproducible retail demand forecasting system that turns historical demand into a validated 7–30 day forecast, explains its uncertainty and errors, and presents evidence-backed decisions through a dashboard. Preserve chronological order and prevent future information from leaking into training or evaluation.

## Total modules: 11

**AI / data science: 8 modules** (1–8) · **Development / delivery: 3 modules** (9–11).

| # | Module | Track | Outcome |
|---|---|---|---|
| 1 | Dataset sourcing and business framing | AI / Data | A licensed, documented demand dataset and clear business use case |
| 2 | Data inspection and cleaning | AI / Data | Validated, consistently aggregated time series with documented decisions |
| 3 | Exploratory demand analysis | AI / Data | Interpreted trend, seasonality, distributions, product/store patterns and outliers |
| 4 | Time-series decomposition | AI / Data | Trend, seasonal and residual analysis to inform model choices |
| 5 | Leakage-safe feature engineering | AI / Data | Sorted lag, rolling, calendar and available business features |
| 6 | Baselines and model training | AI / Data | Seasonal-naive baseline and multiple suitable approaches trained reproducibly |
| 7 | Evaluation and error analysis | AI / Data | Chronological comparison with multiple metrics, residual analysis and failure cases |
| 8 | Future forecasts and business recommendations | AI / Data | Horizon forecasts, uncertainty, demand risks and traceable actions |
| 9 | Forecast API and persistence | Development | FastAPI endpoints backed by SQLite for forecast and metadata access |
| 10 | Interactive forecasting dashboard | Development | React + Vite views and filters for trends, forecasts, models and insights |
| 11 | Packaging, documentation and handoff | Development | Reproducible repository, README, screenshots/demo materials and submission readiness |

## Selected stack

- Frontend: React + Vite, TypeScript, a charting library such as Recharts, and responsive CSS.
- Backend: Python + FastAPI, Pydantic schemas, SQLAlchemy, and SQLite for straightforward local setup. Keep the database URL configurable so hosted deployment can move to PostgreSQL without redesigning API contracts.
- Modeling: Kaggle Notebook, Python, pandas/NumPy, scikit-learn, LightGBM and XGBoost where available. The primary workflow is a pooled model with separate store-family histories, causal lag features and chronological rolling-origin evaluation. Tree libraries may train on CPU or an available accelerator depending on the Kaggle build.
- Artifacts: CSV/JSON forecast and metric exports, serialized selected model where supported, and a ZIP bundle generated in Kaggle /kaggle/working with a clickable download link.

## Business framing and dataset decision

Initial scenario: **retail unit demand by date, product and store**, with a 30-day forecast horizon (configurable to 7/14/30 days). Recommended starting dataset: public Kaggle **Store Sales — Time Series Forecasting** training data, with store/product series and calendar/promotion context. In Kaggle, attach the competition dataset through the notebook Input panel and confirm its terms before redistribution. Record exact source, license/terms, retrieval date, dimensions, granularity, target unit and limitations after inspecting the attached files. Do not package raw source data into the model bundle by default.

If the project owner provides another dataset, update the column mapping and business framing before training. The notebook expects daily observations and supports configurable target/date/entity mapping.

## Detailed implementation plan

### Phase 1 — project foundation

1. Establish repository layout: backend/, frontend/, model_training/, docs/, plus runtime artifact/data directories as needed.
2. Keep raw and processed data out of source control unless the source license permits it; ignore credentials, local databases, large models and Kaggle outputs.
3. Document the chain: industry → business problem → dataset → forecasting approach → prediction → business decision.

### Phase 2 — data understanding and preparation (Modules 1–2)

1. Record dataset source, terms/license, download date, fields, row/column counts, time span, granularity, target units and known limitations.
2. Inspect schema, types, missingness, exact duplicates, duplicate date/entity keys, date continuity, entity counts, target distribution and invalid values.
3. Make explicit decisions for missing records versus real zero demand; investigate repeated keys and unusual values before aggregation or correction.
4. Parse dates, validate nonnegative demand where appropriate, aggregate to daily date × store × item, and create a complete calendar per series only when justified.
5. Save a data dictionary and cleaning log; retain provenance and reproducible preprocessing.

### Phase 3 — analysis and decomposition (Modules 3–4)

1. Produce full-history demand and rolling-average charts, weekday/month patterns, distribution and spike/outlier views, and product/store comparisons where available.
2. Pair each key chart with a short interpretation tied to a modeling or business implication.
3. Inspect trend, weekly/yearly seasonality and residual structure with moving averages and seasonal decomposition (additive or multiplicative based on scale behavior).
4. Run stationarity checks only where they inform an ARIMA-family choice; document findings and limits.

### Phase 4 — modeling (Modules 5–6)

1. Sort each series chronologically before feature creation. Add lags (1, 7, 14, 28), shifted rolling means/std (7, 14, 28), weekday/month/quarter/year/weekend, and only known-at-forecast-time promotion/holiday/price/context fields.
2. Use chronological train/validation/test partitions (roughly 70/15/15 where history permits); record exact dates. Keep test untouched until selection is complete. Fit encoders/scalers on training data only.
3. Establish naive and seasonal-naive (weekly) baselines before advanced modeling.
4. Compare suitable methods from at least two families: seasonal-naive statistical baseline and pooled tree models (LightGBM/XGBoost). Add other statistical methods if justified by runtime and the series design.
5. Record package versions, seeds, hardware, elapsed time, selected hyperparameters and whether prediction is direct or recursive. Do not treat deep learning as necessary if it does not beat simpler methods.

### Phase 5 — evaluation, forecasting and recommendations (Modules 7–8)

1. Compare baseline and candidates on validation using MAE, RMSE and sMAPE (robust to zero-demand periods); optionally report R² as supporting context.
2. Use rolling-origin windows that match the operational horizon; select on validation windows only and report the separate held-out test windows.
3. Plot actual vs predicted, residuals over time, residual distribution and largest misses; explain likely causes and data that could improve them.
4. Forecast 7/14/30 days from the latest observed date. Show intervals where supported; otherwise show uncertainty derived from validation residuals and label the method.
5. Derive growth/decline, expected peaks, volatile series and inventory coverage risks where input stock/lead-time data exists. Clearly mark unavailable inputs rather than fabricate recommendations.
6. Connect every recommendation to a forecast, metric or analysis result.

### Phase 6 — application and delivery (Modules 9–11)

1. Build FastAPI routes for health, dataset/model metadata, available entities, forecast retrieval, model comparison and insights. Validate inputs and return clear errors when artifacts are absent.
2. Persist dataset/model run metadata and forecast rows in SQLite; keep large model files on disk and reference them from metadata.
3. Build React dashboard panels for overview, historical/forecast trends, product selection/ranking, model comparison and business insights. Label dates and units; use consistent actual/forecast colors and readable defaults.
4. Add caching or precomputed outputs so filtering does not retrain models or repeat expensive analysis.
5. Complete README setup/use/limitations, data dictionary, charts and screenshots, model report, .gitignore, reproducibility notes and demo outline. Publishing the LinkedIn video/public submission remains an owner action.

## Proposed repository layout

    backend/                 FastAPI application, schemas, database and API services
    frontend/                React + Vite dashboard
    model_training/          Kaggle notebook and reusable training helpers
    docs/                    project.md, progress.md, checklist.md, reports and data dictionary
    data/                    optional local data; raw files ignored unless license allows
    models/                  local model artifacts (usually ignored in Git)
    outputs/                 generated forecasts, metrics and figures (policy-dependent)
    README.md
    .gitignore

## Key implementation safeguards

- Never randomly split time-series rows.
- Shift rolling features so the current target is not included.
- Do not train on future-known values unavailable at serving time; distinguish known-future calendar features from unknown-future business variables.
- Do not tune against the final test period.
- Treat outliers as investigation flags, not automatic deletion candidates.
- Do not claim stockout/inventory risk without inventory and lead-time inputs.
- Report uncertainty and model limitations alongside point forecasts.

## Definition of done

The final product satisfies every applicable item in docs/checklist.md; it includes reproducible data/model steps, honest chronological evaluation against a baseline, a usable dashboard/API, documented limitations and evidence-backed recommendations. External submission items (publishing the LinkedIn video, supplying personal contact details, and submitting repository links) remain user actions.
