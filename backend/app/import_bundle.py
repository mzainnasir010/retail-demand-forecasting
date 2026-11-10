"""Import the final Kaggle output directory or ZIP into SQLite."""
import argparse
from io import BytesIO
import json
from pathlib import Path
import zipfile

import pandas as pd
from sqlalchemy import insert

from .database import Base, SessionLocal, engine
from .models import DailyActual, ForecastPoint, ForecastRun


def read_bundle_file(source: Path, *names: str):
    if source.is_dir():
        for name in names:
            matches = list(source.rglob(name))
            if matches:
                return matches[0]
        return None
    if zipfile.is_zipfile(source):
        with zipfile.ZipFile(source) as archive:
            for name in names:
                members = [m for m in archive.namelist() if Path(m).name == name]
                if members:
                    info = archive.getinfo(members[0])
                    if info.file_size > 1_000_000_000:
                        raise ValueError(f"{name} is unexpectedly large.")
                    return BytesIO(archive.read(members[0]))
        return None
    raise ValueError("Provide an output folder or ZIP bundle.")


def read_json(source: Path, *names: str) -> dict:
    item = read_bundle_file(source, *names)
    if item is None:
        return {}
    if isinstance(item, BytesIO):
        return json.load(item)
    return json.loads(item.read_text(encoding="utf-8"))


def read_records(source: Path, *names: str) -> list[dict]:
    item = read_bundle_file(source, *names)
    if item is None:
        return []
    frame = pd.read_csv(item)
    return json.loads(frame.to_json(orient="records"))


def import_bundle(source: Path) -> int:
    source = source.resolve()
    Base.metadata.create_all(bind=engine)
    forecast_file = read_bundle_file(source, "forecast_30d.csv", "future_forecast_by_store_family.csv")
    if forecast_file is None:
        raise FileNotFoundError("Missing forecast_30d.csv (or compatible future forecast CSV).")
    forecast = pd.read_csv(forecast_file, parse_dates=["date"])
    if "forecast" not in forecast and "sales_forecast" in forecast:
        forecast = forecast.rename(columns={"sales_forecast": "forecast"})
    required = {"date", "store_nbr", "family", "forecast"}
    if not required.issubset(forecast.columns):
        raise ValueError(f"Forecast CSV is missing columns: {sorted(required - set(forecast.columns))}")

    metadata = read_json(source, "run_metadata.json")
    window_file = read_bundle_file(source, "window_predictions.csv")
    if window_file is not None:
        history = pd.read_csv(
            window_file, usecols=["date", "store_nbr", "family", "actual"], parse_dates=["date"]
        ).rename(columns={"actual": "sales"})
        history = history.dropna(subset=["sales"]).drop_duplicates(
            ["date", "store_nbr", "family"], keep="last"
        )
    else:
        history_file = read_bundle_file(source, "historical_sales_by_store_family.csv")
        history = pd.read_csv(history_file, parse_dates=["date"]) if history_file is not None else pd.DataFrame()

    test_rows = read_records(source, "test_metrics_mean.csv")
    validation_rows = read_records(source, "validation_metrics_mean.csv")
    if not test_rows:
        combined_metrics = read_bundle_file(source, "rolling_window_scores.csv")
        if combined_metrics is not None:
            frame = pd.read_csv(combined_metrics)
            if {"split", "model"}.issubset(frame.columns):
                test_rows = json.loads(
                    frame.loc[frame.split == "test"].groupby("model").mean(numeric_only=True)
                    .reset_index().to_json(orient="records")
                )
                validation_rows = json.loads(
                    frame.loc[frame.split == "validation"].groupby("model").mean(numeric_only=True)
                    .reset_index().to_json(orient="records")
                )

    selected = str(metadata.get("selected_model", "lightgbm")).lower()

    def normalize_metrics(rows: list[dict], split: str) -> list[dict]:
        normalized = []
        for row in rows:
            name = str(row.get("model", "unknown")).lower()
            normalized.append({
                "split": split, "model": name,
                **{key: row.get(key) for key in ("MAE", "RMSE", "sMAPE_pct", "RMSLE", "R2")},
            })
        return normalized

    rolling = normalize_metrics(validation_rows, "validation") + normalize_metrics(test_rows, "test")
    metrics: dict = {
        "rolling": rolling,
        "validation_by_window": read_records(source, "validation_metrics_by_window.csv"),
        "test_by_window": read_records(source, "test_metrics_by_window.csv"),
        "business_insights": read_json(source, "insights.json"),
        "family_outlook": read_records(source, "family_outlook.csv"),
        "horizon_summary": read_records(source, "horizon_summary.csv"),
        "largest_misses": read_records(source, "largest_misses.csv"),
        "volatile_series": read_records(source, "volatile_series.csv"),
        "cleaning_log": read_json(source, "cleaning_log.json"),
        "data_dictionary": read_json(source, "data_dictionary.json"),
        "run_metadata": metadata,
        "figure_files": [
            "figures/validation_mae_by_model.png",
            "figures/test_actual_vs_forecast.png",
            "figures/residuals_over_time.png",
            "figures/residual_distribution.png",
        ],
        "model_artifact": "selected_lightgbm.txt" if read_bundle_file(source, "selected_lightgbm.txt") else None,
    }
    selected_test = next((r for r in rolling if r["split"] == "test" and r["model"] == selected), {})
    seasonal_test = next((r for r in rolling if r["split"] == "test" and r["model"] == "seasonal_naive"), {})
    metrics["test"] = {**selected_test, "baseline_MAE": seasonal_test.get("MAE")}

    horizon = int(metadata.get("horizon", forecast.date.nunique()))
    with SessionLocal() as db:
        run = ForecastRun(
            mode="trained",
            model_name=selected,
            horizon_days=horizon,
            source_name=source.name,
            metrics=metrics,
        )
        db.add(run)
        db.flush()

        if not history.empty:
            history = history.copy()
            history["sales"] = pd.to_numeric(history["sales"], errors="coerce")
            history = history.dropna(subset=["sales"])
            history["date"] = pd.to_datetime(history.date).dt.date
            history["store_nbr"] = history.store_nbr.astype(int)
            history["family"] = history.family.astype(str)
            for start in range(0, len(history), 20_000):
                batch = history.iloc[start:start + 20_000]
                db.execute(insert(DailyActual), [
                    {"run_id": run.id, "date": row.date, "store_nbr": row.store_nbr,
                     "family": row.family, "sales": float(row.sales)}
                    for row in batch.itertuples(index=False)
                ])

        forecast = forecast.copy()
        forecast["date"] = pd.to_datetime(forecast.date).dt.date
        forecast["store_nbr"] = forecast.store_nbr.astype(int)
        forecast["family"] = forecast.family.astype(str)
        lower_col = "lower" if "lower" in forecast else "lower_p10" if "lower_p10" in forecast else None
        upper_col = "upper" if "upper" in forecast else "upper_p90" if "upper_p90" in forecast else None
        for start in range(0, len(forecast), 20_000):
            batch = forecast.iloc[start:start + 20_000]
            db.execute(insert(ForecastPoint), [
                {
                    "run_id": run.id, "date": row.date, "store_nbr": row.store_nbr,
                    "family": row.family, "forecast": max(0.0, float(row.forecast)),
                    "lower": max(0.0, float(getattr(row, lower_col))) if lower_col and pd.notna(getattr(row, lower_col)) else None,
                    "upper": max(0.0, float(getattr(row, upper_col))) if upper_col and pd.notna(getattr(row, upper_col)) else None,
                    "onpromotion": float(row.onpromotion) if hasattr(row, "onpromotion") and pd.notna(row.onpromotion) else None,
                    "is_holiday": bool(row.is_holiday) if hasattr(row, "is_holiday") and pd.notna(row.is_holiday) else False,
                }
                for row in batch.itertuples(index=False)
            ])
        db.commit()
        return run.id


def main():
    parser = argparse.ArgumentParser(description="Import final Kaggle forecast outputs.")
    parser.add_argument("outputs", type=Path, help="Output directory or ZIP bundle from Kaggle")
    args = parser.parse_args()
    print(f"Imported trained forecast run {import_bundle(args.outputs)}.")


if __name__ == "__main__":
    main()
