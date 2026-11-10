# Demand Forecasting Dashboard

A local demand planning application for the SEKER AI Project 06 assignment. The dashboard is connected to the final Kaggle run in `model_training/outputs` and uses its forecasts, evaluation results, business insights, and exported report figures.

## Stack

- Frontend: React, Vite, TypeScript, Recharts
- Backend: FastAPI, SQLAlchemy, SQLite
- Training: Kaggle notebook in model_training/

## Run locally

Use two terminals from the repository root.

### 1. Start the API

    cd backend
    py -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    uvicorn app.main:app --reload

The API is at http://localhost:8000 and interactive API docs are at http://localhost:8000/docs. On its first start, the API imports `model_training/outputs/forecast_30d.csv` and `window_predictions.csv` into a local SQLite database. Keep the Kaggle output folder in the repository at that path, or set `FORECAST_ARTIFACTS_DIR` to another output directory.

### 2. Start the dashboard

    cd frontend
    npm install
    npm run dev

Open the local address printed by Vite (normally http://localhost:5173).

## Import the Kaggle run

To import a refreshed Kaggle output folder or ZIP, run from the backend directory:

    python -m app.import_bundle "C:\path\to\demand_forecasting_bundle.zip"

The final notebook exports these files (the importer also accepts the previous bundle schema):

- forecast_30d.csv
- window_predictions.csv
- run_metadata.json
- test_metrics_mean.csv and validation_metrics_mean.csv
- insights.json and family_outlook.csv
- figures/ (evaluation plots)

Refresh the API/dashboard after importing. The most recently imported run becomes active. The importer reads files from the archive without extracting arbitrary archive paths. It imports forecast results and historical observations; the model text file is made available as a report artifact but is not loaded or executed by the API.

The SQLite database is stored at backend/data/forecast.db and is excluded from Git. Set DATABASE_URL to use a different database path.

## API routes

- GET /api/health — active data mode and model
- GET /api/dashboard?horizon_days=30&store_nbr=1&family=GROCERY%20I — overview data, chart series and insights
- GET /api/entities — available stores and product families
- GET /api/runs/latest — latest run metadata and metrics

## Current status and limitations

- Only the final trained run is shown; the app does not seed mock or sample forecasts.
- Inventory recommendations require stock-on-hand and supplier lead-time data; the current dataset does not provide these.
- The final notebook's window_predictions.csv supplies six rolling evaluation windows of actuals for the history chart.
- Only local development is configured. Authentication, hosted deployment and production database configuration are not included.
