# Demand Forecasting Dashboard

A local demand planning application for the SEKER AI Project 06 assignment. The FastAPI service starts with clearly marked sample data. When the Kaggle training run is ready, import its output bundle to replace the dashboard's active run.

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

The API is at http://localhost:8000 and interactive API docs are at http://localhost:8000/docs. On its first start, it creates a local SQLite database and seeds sample data. The dashboard identifies this as **Sample data**.

### 2. Start the dashboard

    cd frontend
    npm install
    npm run dev

Open the local address printed by Vite (normally http://localhost:5173).

## Import the Kaggle run

After downloading the ZIP from Kaggle, import it from the backend directory:

    python -m app.import_bundle "C:\path\to\demand_forecasting_bundle.zip"

The bundle should include:

- future_forecast_by_store_family.csv
- historical_sales_by_store_family.csv
- run_metadata.json
- rolling_window_scores.csv

Restart or refresh the API/dashboard. The most recently imported run becomes active. The importer reads files from the archive without extracting arbitrary archive paths. It imports forecast results and historical observations; it does not load or execute the serialized model file.

The SQLite database is stored at backend/data/forecast.db and is excluded from Git. Set DATABASE_URL to use a different database path.

## API routes

- GET /api/health — active data mode and model
- GET /api/dashboard?horizon_days=16&store_nbr=1&family=GROCERY%20I — overview data, chart series and insights
- GET /api/entities — available stores and product families
- GET /api/runs/latest — latest run metadata and metrics

## Current status and limitations

- Sample data is for interface development and must not be presented as model results.
- Inventory recommendations require stock-on-hand and supplier lead-time data; the current dataset does not provide these.
- The Kaggle notebook must export historical_sales_by_store_family.csv for a full historical dashboard after importing a trained run.
- Only local development is configured. Authentication, hosted deployment and production database configuration are not included.
