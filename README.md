# Retail Demand Forecasting

A local forecasting application for retail demand by date, store, and product family. The project includes a Kaggle training notebook, chronological evaluation, a FastAPI inference service, SQLite run history, and a React dashboard.

## Dataset

The notebook uses Kaggle's *Store Sales — Time Series Forecasting* competition data. The supplied training output reports 3,000,888 rows and six source columns across 1,782 store/family series (54 stores, 33 families), from 2013-01-01 through 2017-08-15. The target is daily sales units. The source is subject to the [competition rules](https://www.kaggle.com/competitions/store-sales-time-series-forecasting/rules); the [Kaggle data page](https://www.kaggle.com/competitions/store-sales-time-series-forecasting/data) identifies it as subject to those rules. The notebook records its retrieval date and column profile. Raw competition data is not committed or included in the model bundle.

The training notebook records row counts, nulls, duplicate keys, missing calendar dates, zero-filled cells and the outlier policy. It treats dates absent for all stores as closures, fills missing date/entity cells with zero, and retains spikes for investigation. It builds a data dictionary and produces demand trend, weekday/month/year patterns, distribution, heatmap, store/family comparison, decomposition and residual figures. See [the data dictionary](docs/data_dictionary.md) and [model report](docs/model_report.md).

## Modeling and evaluation

The notebook compares naive and weekly seasonal-naive baselines with pooled LightGBM and XGBoost models. It uses lag features (1, 7, 14, 28), shifted rolling statistics, calendar fields and store/family context. Predictions are recursive and use a log1p target. Validation rolling windows choose the model; two later rolling windows are held out for final reporting. Unknown future promotions are excluded.

The pooled trees share information across related store/family series and accept calendar and static context directly. Separate ARIMA models would require maintaining thousands of independent fits and do not use the same context as directly; deep learning was not adopted without evidence it improves on these baselines and tree candidates. The notebook records seeds, package versions, hardware, fitting times and hyperparameters.

The supplied final run selected LightGBM. On its held-out windows, MAE was 62.82 units, RMSE 240.82, sMAPE 55.84%, and RMSLE 0.438. The seasonal-naive baseline scored MAE 78.89, RMSE 309.59, sMAPE 41.57%, and RMSLE 0.553. Thus LightGBM reduced absolute and squared errors, while seasonal naive had lower sMAPE. The selection rule is a mean rank of MAE, RMSE and sMAPE on validation windows; the test results are disclosed here as a final check, not a tuning target.

Uncertainty bounds are empirical validation-residual quantiles by forecast step. Inventory reorder/stockout recommendations are omitted because stock-on-hand and supplier lead times are not provided.

## Stack

- Frontend: React, Vite, TypeScript, Recharts
- Backend: FastAPI, Pydantic, SQLAlchemy, SQLite
- Model inference: LightGBM and XGBoost CPU runtimes
- Training: Kaggle notebook in `model_training/`

## Run locally

Keep the Kaggle output bundle under `model_training/outputs/`. It must include the forecast CSV, actuals, selected model, `series_metadata.csv`, and `inference_metadata.json`. The updated notebook writes these serving sidecars along with evaluation and EDA outputs. If starting from the older supplied bundle, run the updated notebook and re-import the resulting ZIP before using fresh prediction.

In one PowerShell terminal from the repository root:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite address (usually http://localhost:5173). The API docs are at http://localhost:8000/docs. On first start, the API imports `model_training/outputs/forecast_30d.csv` and its rolling-window actuals into SQLite. The database lives at `backend/data/forecast.db` and is ignored by Git. Set `FORECAST_ARTIFACTS_DIR` or `DATABASE_URL` to use alternate locations.

## Generate a fresh forecast

The **New prediction** flow loads the selected model artifact and runs the same recursive feature calculation as the training notebook for 7, 14, or 30 days. With no upload, it forecasts from the latest history saved in SQLite. To incorporate newer observations, download the CSV template from the Model performance page, fill its `sales` column, and upload it. Each added date must be consecutive and include every trained store/family series. For future periods beyond the holiday calendar exported by the training run, enter known national holiday dates as comma-separated `YYYY-MM-DD` values.

The prediction is stored as a new forecast run and becomes the dashboard's active result. Model files remain on disk; the API stores their run metadata and forecast rows in SQLite. The API never executes arbitrary uploaded model files.

API routes:

- `GET /api/health` — service and active run
- `GET /api/model/status` — artifact/metadata readiness
- `GET /api/predictions/input-template.csv` — complete next-date input template
- `POST /api/predictions` — multipart form with `horizon_days`, optional `observations` CSV, and optional `national_holiday_dates`
- `GET /api/dashboard?horizon_days=30` — chart, metrics, insights, family outlook and volatility
- `GET /api/entities` — available stores and families
- `GET /api/runs/latest` — current run and metrics
- `GET /api/runs/latest/forecast.csv` — download all store/family predictions and interval bounds for the active run

To update from a fresh Kaggle ZIP, run from the backend directory:

```powershell
python -m app.import_bundle "C:\path\to\demand_forecast_bundle.zip"
```

The importer accepts the output folder directly or the notebook ZIP. It safely copies only allowlisted model, metadata and figure files from an archive; it does not extract arbitrary archive paths.

## Limitations and next steps

- Competition data and outputs represent historical observations through 2017, not a live retailer feed. Upload complete, newer daily actuals to advance the forecast origin.
- The supplied output bundle predates inference sidecars. The updated notebook must be run and its ZIP imported before `/api/model/status` reports ready.
- Tree models do not extrapolate year trends well, and recursive errors can accumulate at longer horizons.
- Inventory, purchasing and deployment integrations require separate data and configuration.
- Screenshots, a public demo, and official submission details are not included in this local application.
