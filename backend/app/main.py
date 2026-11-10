from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from .config import FRONTEND_ORIGIN, TRAINING_OUTPUTS_DIR
from .database import Base, engine, get_db
from .import_bundle import import_bundle
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
