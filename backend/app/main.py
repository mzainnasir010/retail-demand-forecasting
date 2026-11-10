import csv
from datetime import date, timedelta
from io import BytesIO, StringIO

import pandas as pd
from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from sqlalchemy import delete, inspect, insert, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from .config import FRONTEND_ORIGIN, TRAINING_OUTPUTS_DIR
from .database import Base, engine, get_db
from .import_bundle import import_bundle
from .inference import InferenceUnavailable, generate_forecast, model_status, prediction_input_template
from .models import DailyActual, ForecastPoint, ForecastRun
from .schemas import DashboardResponse, EntityOptions, HealthResponse
from .service import dashboard_data, entity_options, latest_run

app = FastAPI(
    title="Demand Forecasting API",
    description="Forecasts, model evaluation and business insights for the demand planning dashboard.",
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN, "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.mount(
    "/api/artifacts",
    StaticFiles(directory=TRAINING_OUTPUTS_DIR, check_dir=False),
    name="forecast-artifacts",
)


@app.on_event("startup")
def initialize_database() -> None:
    Base.metadata.create_all(bind=engine)
    if "history_run_id" not in {column["name"] for column in inspect(engine).get_columns("forecast_runs")}:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE forecast_runs ADD COLUMN history_run_id INTEGER"))
    from .database import SessionLocal
    with SessionLocal() as db:
        demo_ids = db.scalars(select(ForecastRun.id).where(ForecastRun.mode == "demo")).all()
        if demo_ids:
            db.execute(delete(DailyActual).where(DailyActual.run_id.in_(demo_ids)))
            db.execute(delete(ForecastPoint).where(ForecastPoint.run_id.in_(demo_ids)))
            db.execute(delete(ForecastRun).where(ForecastRun.id.in_(demo_ids)))
            db.commit()
        has_run = db.scalar(select(ForecastRun.id).limit(1)) is not None
    if not has_run and (TRAINING_OUTPUTS_DIR / "forecast_30d.csv").exists():
        import_bundle(TRAINING_OUTPUTS_DIR)


@app.get("/api/health", response_model=HealthResponse, tags=["system"])
def health(db: Session = Depends(get_db)):
    try:
        run = latest_run(db)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"status": "ok", "mode": run.mode, "model_name": run.model_name, "run_id": run.id}


@app.get("/api/entities", response_model=EntityOptions, tags=["forecast"])
def entities(db: Session = Depends(get_db)):
    run = latest_run(db)
    return entity_options(db, run.id)


@app.get("/api/dashboard", response_model=DashboardResponse, tags=["forecast"])
def dashboard(
    horizon_days: int = Query(default=30, ge=1, le=90),
    store_nbr: int | None = Query(default=None, ge=1),
    family: str | None = Query(default=None, min_length=1, max_length=120),
    db: Session = Depends(get_db),
):
    try:
        return dashboard_data(db, horizon_days, store_nbr, family)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/api/runs/latest", tags=["runs"])
def latest_run_summary(db: Session = Depends(get_db)):
    run: ForecastRun = latest_run(db)
    return {
        "id": run.id,
        "created_at": run.created_at.isoformat(),
        "mode": run.mode,
        "model_name": run.model_name,
        "horizon_days": run.horizon_days,
        "source_name": run.source_name,
        "metrics": run.metrics,
    }


@app.get("/api/runs/latest/forecast.csv", tags=["runs"], summary="Download the active run's store/family forecasts")
def latest_forecast_csv(db: Session = Depends(get_db)):
    run = latest_run(db)
    rows = db.scalars(select(ForecastPoint).where(
        ForecastPoint.run_id == run.id
    ).order_by(ForecastPoint.date, ForecastPoint.store_nbr, ForecastPoint.family)).all()
    if not rows:
        raise HTTPException(status_code=404, detail="The active run has no forecast rows.")
    origin = min(row.date for row in rows) - timedelta(days=1)
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["date", "horizon_day", "store_nbr", "family", "forecast", "lower_p10", "upper_p90"])
    for row in rows:
        writer.writerow([row.date.isoformat(), (row.date - origin).days, row.store_nbr, row.family,
                         row.forecast, row.lower, row.upper])
    return Response(content=buffer.getvalue(), media_type="text/csv",
                    headers={"Content-Disposition": "attachment; filename=latest_forecast.csv"})


@app.get("/api/model/status", tags=["model"], summary="Check the saved model and inference sidecars")
def current_model_status(db: Session = Depends(get_db)):
    try:
        return model_status(latest_run(db))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/api/predictions/input-template.csv", tags=["model"], summary="Download a complete next-day sales input template")
def prediction_template(db: Session = Depends(get_db)):
    try:
        content = prediction_input_template(db, latest_run(db))
    except (RuntimeError, InferenceUnavailable) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return Response(content=content, media_type="text/csv",
                    headers={"Content-Disposition": "attachment; filename=prediction_input_template.csv"})


@app.post(
    "/api/predictions", tags=["model"], summary="Load the saved model and generate a fresh forecast",
    description=("Accepts horizon_days=7, 14, or 30; optional observations CSV with "
                 "date, store_nbr, family, sales; and optional comma-separated national holiday dates. "
                 "Uploaded dates must be consecutive after saved history and contain every trained series."),
)
async def create_prediction(
    horizon_days: int = Form(default=30, ge=7, le=30),
    national_holiday_dates: str = Form(default=""),
    observations: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
):
    if horizon_days not in (7, 14, 30):
        raise HTTPException(status_code=422, detail="horizon_days must be 7, 14, or 30.")
    run = latest_run(db)
    try:
        additional_holidays = {value.strip() for value in national_holiday_dates.split(",") if value.strip()}
        for value in additional_holidays:
            date.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="National holiday dates must be comma-separated ISO dates (YYYY-MM-DD).") from exc
    observation_frame = None
    if observations is not None:
        content = await observations.read(25 * 1024 * 1024 + 1)
        if len(content) > 25 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="CSV input must be 25 MB or smaller.")
        try:
            observation_frame = pd.read_csv(BytesIO(content))
        except Exception as exc:
            raise HTTPException(status_code=422, detail="Could not read the uploaded CSV.") from exc
        required = {"date", "store_nbr", "family", "sales"}
        if not required.issubset(observation_frame.columns):
            raise HTTPException(status_code=422, detail="CSV must contain date, store_nbr, family, and sales columns.")
        if observation_frame.empty:
            raise HTTPException(status_code=422, detail="CSV must contain at least one complete observation date.")
        if len(observation_frame) > 250_000:
            raise HTTPException(status_code=413, detail="CSV input must contain 250,000 rows or fewer.")
        observation_frame = observation_frame[["date", "store_nbr", "family", "sales"]]
    try:
        forecast, new_actuals, origin = generate_forecast(
            db, run, horizon_days, observation_frame, additional_holidays
        )
    except InferenceUnavailable as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    metrics = dict(run.metrics or {})
    metrics["latest_prediction"] = {
        "origin": origin.isoformat(), "horizon_days": horizon_days,
        "input_rows": int(len(new_actuals)), "input_kind": "uploaded_csv" if observations else "saved_history",
        "extra_holiday_dates": sorted(additional_holidays),
    }
    prediction_run = ForecastRun(
        mode="trained", model_name=run.model_name, horizon_days=horizon_days,
        source_name=f"Fresh prediction from run {run.id}",
        history_run_id=run.history_run_id or run.id, metrics=metrics,
    )
    try:
        db.add(prediction_run)
        db.flush()
        if not new_actuals.empty:
            history_destination_id = prediction_run.history_run_id or prediction_run.id
            db.execute(insert(DailyActual), [
                {"run_id": history_destination_id, "date": row.date, "store_nbr": int(row.store_nbr),
                 "family": str(row.family), "sales": float(row.sales)}
                for row in new_actuals.itertuples(index=False)
            ])
        db.execute(insert(ForecastPoint), [
            {"run_id": prediction_run.id, "date": row.date, "store_nbr": int(row.store_nbr),
             "family": str(row.family), "forecast": float(row.forecast), "lower": row.lower,
             "upper": row.upper, "onpromotion": None, "is_holiday": False}
            for row in forecast.itertuples(index=False)
        ])
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="The history changed during prediction. Refresh the input template and retry.") from exc
    return {
        "run_id": prediction_run.id, "model_name": run.model_name,
        "origin": origin.isoformat(), "forecast_start": forecast.date.min().isoformat(),
        "forecast_end": forecast.date.max().isoformat(), "horizon_days": horizon_days,
        "forecast_rows": len(forecast), "input_rows": len(new_actuals),
        "input_kind": "uploaded_csv" if observations else "saved_history",
    }
