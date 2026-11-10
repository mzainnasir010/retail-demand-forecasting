"""Load Kaggle output CSVs into SQLite without extracting uploaded ZIP members."""
import argparse
from io import BytesIO
import json
from pathlib import Path
import zipfile
import pandas as pd
from sqlalchemy import insert
from .database import Base, SessionLocal, engine
from .models import DailyActual, ForecastPoint, ForecastRun


def read_bundle_file(source: Path, name: str):
    if source.is_dir():
        matches = list(source.rglob(name))
        return matches[0] if matches else None
    if zipfile.is_zipfile(source):
        with zipfile.ZipFile(source) as archive:
            members = [m for m in archive.namelist() if Path(m).name == name]
            if not members:
                return None
            info = archive.getinfo(members[0])
            if info.file_size > 1_000_000_000:
                raise ValueError(f"{name} is unexpectedly large.")
            return BytesIO(archive.read(members[0]))
    raise ValueError("Provide a folder or ZIP bundle.")


def load_json(source: Path, name: str) -> dict:
    item = read_bundle_file(source, name)
    if item is None:
        return {}
    if isinstance(item, BytesIO):
        return json.load(item)
    return json.loads(item.read_text(encoding="utf-8"))


def import_bundle(source: Path) -> int:
    Base.metadata.create_all(bind=engine)
    future_file = read_bundle_file(source, "future_forecast_by_store_family.csv")
    history_file = read_bundle_file(source, "historical_sales_by_store_family.csv")
    if future_file is None:
        raise FileNotFoundError("Bundle must include future_forecast_by_store_family.csv.")
    future = pd.read_csv(future_file, parse_dates=["date"])
    needed = {"date", "store_nbr", "family", "forecast"}
    if not needed.issubset(future.columns):
        raise ValueError(f"Forecast CSV is missing columns: {sorted(needed - set(future.columns))}")
    history = pd.read_csv(history_file, parse_dates=["date"]) if history_file is not None else pd.DataFrame()
    metadata = load_json(source, "run_metadata.json")
    rolling = read_bundle_file(source, "rolling_window_scores.csv")
    metrics: dict = {}
    if rolling is not None:
        frame = pd.read_csv(rolling)
        if {"split", "model", "MAE", "RMSE", "sMAPE_pct"}.issubset(frame.columns):
            metrics["rolling"] = frame.groupby(["split", "model"])[
                ["MAE", "RMSE", "sMAPE_pct"]
            ].mean().round(4).reset_index().to_dict(orient="records")
    if "rolling" in metrics:
        selected = metadata.get("selected_model")
        rows = metrics["rolling"]
        test_metrics = next((r for r in rows if r["split"] == "test" and r["model"] == selected), None)
        baseline = next((r for r in rows if r["split"] == "test" and r["model"] == "SeasonalNaive_7"), None)
        if test_metrics:
            metrics["test"] = {**test_metrics, "baseline_MAE": baseline.get("MAE") if baseline else None}
    model_name = str(metadata.get("selected_model", "Imported Kaggle forecast"))
    if history.empty:
        print("Note: no historical_sales_by_store_family.csv found; dashboard history will be empty until supplied.")

    with SessionLocal() as db:
        run = ForecastRun(
            mode="trained",
            model_name=model_name,
            horizon_days=int(metadata.get("horizon_days", max(1, future.date.nunique()))),
            source_name=source.name,
            metrics=metrics,
        )
        db.add(run)
        db.flush()
        if not history.empty:
            history["sales"] = pd.to_numeric(history.get("sales"), errors="coerce")
            history = history.dropna(subset=["sales"])
            history = history.copy()
            history["date"] = history.date.dt.date
            history["store_nbr"] = history.store_nbr.astype(int)
            history["family"] = history.family.astype(str)
            for start in range(0, len(history), 20_000):
                batch = history.iloc[start:start + 20_000]
                db.execute(insert(DailyActual), [
                    {"run_id": run.id, "date": row.date, "store_nbr": row.store_nbr,
                     "family": row.family, "sales": float(row.sales)}
                    for row in batch.itertuples(index=False)
                ])
        future = future.copy()
        future["date"] = future.date.dt.date
        future["store_nbr"] = future.store_nbr.astype(int)
        future["family"] = future.family.astype(str)
        for start in range(0, len(future), 20_000):
            batch = future.iloc[start:start + 20_000]
            db.execute(insert(ForecastPoint), [
                {
                    "run_id": run.id, "date": row.date, "store_nbr": row.store_nbr,
                    "family": row.family, "forecast": max(0.0, float(row.forecast)),
                    "lower": float(row.lower) if hasattr(row, "lower") and pd.notna(row.lower) else None,
                    "upper": float(row.upper) if hasattr(row, "upper") and pd.notna(row.upper) else None,
                    "onpromotion": float(row.onpromotion) if hasattr(row, "onpromotion") and pd.notna(row.onpromotion) else None,
                    "is_holiday": bool(row.is_holiday) if hasattr(row, "is_holiday") and pd.notna(row.is_holiday) else False,
                }
                for row in batch.itertuples(index=False)
            ])
        db.commit()
        return run.id


def main():
    parser = argparse.ArgumentParser(description="Import a Kaggle demand forecasting output bundle.")
    parser.add_argument("bundle", type=Path, help="Kaggle ZIP or extracted output directory")
    args = parser.parse_args()
    run_id = import_bundle(args.bundle)
    print(f"Imported forecast run {run_id}. Restart the API and refresh the dashboard.")


if __name__ == "__main__":
    main()
