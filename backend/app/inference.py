"""Load a trained artifact and generate a fresh recursive forecast."""
from __future__ import annotations

from datetime import date, timedelta
import calendar
import csv
from io import StringIO
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import TRAINING_OUTPUTS_DIR
from .models import DailyActual, ForecastRun

LAGS = (1, 7, 14, 28)
ROLLS = (7, 14, 28)
CALENDAR_FEATURES = ["dow", "dom", "month", "quarter", "year", "is_weekend", "is_payday", "national_holiday"]
REQUIRED_SERIES_COLUMNS = {"store_nbr", "family", "family_code", "cluster", "store_type_code"}


class InferenceUnavailable(RuntimeError):
    """The imported run does not include a compatible serving artifact."""


@lru_cache(maxsize=4)
def _load_model(path_string: str, modified_ns: int, model_name: str):
    path = Path(path_string)
    if model_name == "lightgbm":
        try:
            import lightgbm as lgb
        except ImportError as exc:
            raise InferenceUnavailable("Install the backend requirements to load the LightGBM artifact.") from exc
        try:
            return lgb.Booster(model_file=str(path))
        except Exception as exc:
            raise InferenceUnavailable(f"Could not load the LightGBM model artifact: {exc}") from exc
    if model_name == "xgboost":
        try:
            import xgboost as xgb
        except ImportError as exc:
            raise InferenceUnavailable("Install the backend requirements to load the XGBoost artifact.") from exc
        try:
            model = xgb.XGBRegressor()
            model.load_model(str(path))
            model.set_params(device="cpu")
            return model
        except Exception as exc:
            raise InferenceUnavailable(f"Could not load the XGBoost model artifact: {exc}") from exc
    raise InferenceUnavailable(f"Unsupported saved model type: {model_name}.")


def _artifact_name(model_name: str) -> str:
    if model_name == "lightgbm":
        return "selected_lightgbm.txt"
    if model_name == "xgboost":
        return "selected_xgboost.json"
    raise InferenceUnavailable(f"No serving adapter is configured for {model_name}.")


def _expected_features(calendar_features: list[str]) -> list[str]:
    return (list(calendar_features) + ["store_nbr", "family_code", "cluster", "store_type_code"]
            + [f"lag_{lag}" for lag in LAGS]
            + [name for width in ROLLS for name in (f"roll_mean_{width}", f"roll_std_{width}")])


def _inference_files(run: ForecastRun) -> tuple[Path, Path, Path, dict]:
    artifact_name = _artifact_name(run.model_name.lower())
    artifact = TRAINING_OUTPUTS_DIR / artifact_name
    series_path = TRAINING_OUTPUTS_DIR / "series_metadata.csv"
    metadata_path = TRAINING_OUTPUTS_DIR / "inference_metadata.json"
    metadata = (run.metrics or {}).get("inference_metadata", {})
    if not artifact.is_file() or not series_path.is_file() or not metadata_path.is_file():
        raise InferenceUnavailable(
            "Fresh prediction needs the saved model plus series_metadata.csv and inference_metadata.json. "
            "Re-run the updated Kaggle notebook and import its output bundle."
        )
    if not metadata:
        import json
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    return artifact, series_path, metadata_path, metadata


def model_status(run: ForecastRun) -> dict:
    try:
        artifact, series, _, metadata = _inference_files(run)
        model = _load_model(str(artifact), artifact.stat().st_mtime_ns, run.model_name.lower())
        feature_names = metadata.get("features", [])
        if metadata.get("calendar_features") != CALENDAR_FEATURES:
            raise InferenceUnavailable("The inference calendar feature order does not match the trained model.")
        if feature_names != _expected_features(metadata.get("calendar_features", [])):
            raise InferenceUnavailable("Inference feature metadata is incomplete or does not match the training contract.")
        if len(metadata.get("residual_q10_by_horizon", [])) < 30 or len(metadata.get("residual_q90_by_horizon", [])) < 30:
            raise InferenceUnavailable("The run must include 30-step validation residual quantiles for forecast intervals.")
        series_frame = pd.read_csv(series)
        if not REQUIRED_SERIES_COLUMNS.issubset(series_frame.columns):
            raise InferenceUnavailable("series_metadata.csv is missing required static feature columns.")
        if series_frame.duplicated(["store_nbr", "family"]).any() or series_frame.empty:
            raise InferenceUnavailable("series_metadata.csv must contain unique, non-empty store/family rows.")
        if run.model_name.lower() == "lightgbm":
            if feature_names and int(model.num_feature()) != len(feature_names):
                raise InferenceUnavailable("Model feature count does not match inference_metadata.json.")
        elif run.model_name.lower() == "xgboost" and int(model.get_booster().num_features()) != len(feature_names):
            raise InferenceUnavailable("Model feature count does not match inference_metadata.json.")
        return {"ready": True, "model_name": run.model_name, "artifact": artifact.name,
                "series_count": int(len(series_frame)), "feature_count": len(feature_names),
                "reason": None}
    except Exception as exc:
        return {"ready": False, "model_name": run.model_name, "artifact": None,
                "series_count": 0, "feature_count": 0, "reason": str(exc)}


def prediction_input_template(db: Session, run: ForecastRun) -> str:
    """Build a CSV starter with every known series and the next expected date."""
    _, series_path, _, _ = _inference_files(run)
    history_run_ids = [run.id, run.history_run_id] if run.history_run_id else [run.id]
    latest_date = db.scalar(select(DailyActual.date).where(
        DailyActual.run_id.in_(history_run_ids)
    ).order_by(DailyActual.date.desc()).limit(1))
    if latest_date is None:
        raise InferenceUnavailable("No saved sales history is available for this model run.")
    series = pd.read_csv(series_path)
    next_date = latest_date + timedelta(days=1)
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["date", "store_nbr", "family", "sales"])
    for row in series.itertuples(index=False):
        writer.writerow([next_date.isoformat(), int(row.store_nbr), row.family, ""])
    return buffer.getvalue()


def _future_calendar(day: date, holiday_dates: set[str]) -> list[float]:
    return [
        float(day.weekday()), float(day.day), float(day.month), float((day.month - 1) // 3 + 1),
        float(day.year), float(day.weekday() >= 5), float(day.day == 15 or day.day == calendar.monthrange(day.year, day.month)[1]),
        float(day.isoformat() in holiday_dates),
    ]


def generate_forecast(
    db: Session, run: ForecastRun, horizon_days: int,
    observations: pd.DataFrame | None = None,
    additional_holidays: set[str] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, date]:
    """Return forecast rows, newly appended actual rows, and the forecast origin."""
    artifact, series_path, _, inference_meta = _inference_files(run)
    model = _load_model(str(artifact), artifact.stat().st_mtime_ns, run.model_name.lower())
    series = pd.read_csv(series_path)
    missing = REQUIRED_SERIES_COLUMNS - set(series.columns)
    if missing:
        raise InferenceUnavailable(f"series_metadata.csv is missing: {', '.join(sorted(missing))}.")
    series["store_nbr"] = pd.to_numeric(series.store_nbr, errors="raise").astype(int)
    series["family"] = series.family.astype(str)
    series = series.sort_values("series_index" if "series_index" in series else ["store_nbr", "family"]).reset_index(drop=True)
    keys = list(zip(series.store_nbr, series.family))
    if not keys or len(keys) != len(set(keys)):
        raise InferenceUnavailable("series_metadata.csv must contain unique store and family rows.")

    history_run_ids = {run.id}
    if run.history_run_id is not None:
        history_run_ids.add(run.history_run_id)
    stored = db.scalars(select(DailyActual).where(DailyActual.run_id.in_(history_run_ids))).all()
    if not stored:
        raise InferenceUnavailable("No saved sales history is available for this model run.")
    history = pd.DataFrame([{"date": row.date, "store_nbr": row.store_nbr,
                             "family": row.family, "sales": row.sales} for row in stored])
    new_rows = pd.DataFrame(columns=["date", "store_nbr", "family", "sales"])
    if observations is not None and not observations.empty:
        new_rows = observations.copy()
        new_rows["date"] = pd.to_datetime(new_rows.date).dt.date
        store_values = pd.to_numeric(new_rows.store_nbr, errors="raise")
        if not (store_values % 1 == 0).all():
            raise ValueError("store_nbr values must be whole numbers.")
        new_rows["store_nbr"] = store_values.astype(int)
        new_rows["family"] = new_rows.family.astype(str)
        new_rows["sales"] = pd.to_numeric(new_rows.sales, errors="raise")
        if (new_rows.sales < 0).any() or not np.isfinite(new_rows.sales.to_numpy(dtype=float)).all():
            raise ValueError("Sales values must be finite and non-negative.")
        if new_rows.duplicated(["date", "store_nbr", "family"]).any():
            raise ValueError("The input CSV contains duplicate date/store/family rows.")
        unknown = set(zip(new_rows.store_nbr, new_rows.family)) - set(keys)
        if unknown:
            raise ValueError("Input rows include store/family combinations not present in the trained model.")
        origin = max(history.date)
        incoming_dates = sorted(set(new_rows.date))
        expected_dates = [origin + timedelta(days=i) for i in range(1, len(incoming_dates) + 1)]
        if incoming_dates != expected_dates:
            raise ValueError("Input dates must be consecutive and begin the day after saved history ends.")
        counts = new_rows.groupby("date").size()
        if not (counts == len(keys)).all():
            raise ValueError("Each appended date must include every trained store/family series.")
        if new_rows.duplicated(["date", "store_nbr", "family"]).any() or any(
            set(zip(group.store_nbr, group.family)) != set(keys)
            for _, group in new_rows.groupby("date")
        ):
            raise ValueError("Each appended date must have exactly one row for every trained series.")
        history = pd.concat([history, new_rows], ignore_index=True)

    history["date"] = pd.to_datetime(history.date).dt.date
    pivot = history.pivot_table(index="date", columns=["store_nbr", "family"], values="sales", aggfunc="last")
    column_keys = pd.MultiIndex.from_tuples(keys, names=["store_nbr", "family"])
    dates = pd.date_range(min(pivot.index), max(pivot.index), freq="D").date
    pivot = pivot.reindex(index=dates, columns=column_keys)
    if pivot.isna().any().any():
        raise InferenceUnavailable("Saved history has missing days or series; provide complete daily series inputs.")
    origin = dates[-1]
    max_history = max(28, int(inference_meta.get("minimum_history_days", 28)))
    history_values = pivot.to_numpy(dtype=np.float32)[-max_history:]
    if len(history_values) < 28:
        raise InferenceUnavailable("At least 28 consecutive days of sales are needed to calculate model features.")
    log_target = bool(inference_meta.get("log_target", True))
    work = np.log1p(np.maximum(history_values, 0)) if log_target else history_values.copy()
    static = series[["store_nbr", "family_code", "cluster", "store_type_code"]].to_numpy(dtype=np.float32)
    feature_names = list(inference_meta.get("features", []))
    expected_features = _expected_features(inference_meta.get("calendar_features", []))
    if feature_names != expected_features:
        raise InferenceUnavailable("The feature definition in the model metadata is unsupported or incomplete.")
    holiday_dates = set(inference_meta.get("national_holiday_dates", [])) | (additional_holidays or set())
    requested_range = {origin + timedelta(days=step) for step in range(1, horizon_days + 1)}
    if additional_holidays and not {date.fromisoformat(value) for value in additional_holidays}.issubset(requested_range):
        raise ValueError("Additional holiday dates must fall inside the requested forecast horizon.")
    lower_q = inference_meta.get("residual_q10_by_horizon", [])
    upper_q = inference_meta.get("residual_q90_by_horizon", [])
    outputs = []
    for step in range(1, horizon_days + 1):
        target_date = origin + timedelta(days=step)
        calendar = np.asarray(_future_calendar(target_date, holiday_dates), dtype=np.float32)
        parts = [np.repeat(calendar[None, :], len(keys), axis=0), static]
        parts.extend(work[-lag][:, None] for lag in LAGS)
        for width in ROLLS:
            block = work[-width:]
            parts.extend([block.mean(axis=0)[:, None], block.std(axis=0)[:, None]])
        features = np.concatenate(parts, axis=1).astype(np.float32, copy=False)
        pred_space = np.asarray(model.predict(features), dtype=np.float32).reshape(-1)
        if len(pred_space) != len(keys):
            raise InferenceUnavailable("Loaded model returned an unexpected number of series predictions.")
        pred_space = np.maximum(pred_space, 0.0)
        point = np.maximum(np.expm1(pred_space), 0.0) if log_target else np.maximum(pred_space, 0.0)
        lower = upper = None
        if len(lower_q) >= step and len(upper_q) >= step:
            lower_space = np.maximum(pred_space + float(lower_q[step - 1]), 0.0)
            upper_space = np.maximum(pred_space + float(upper_q[step - 1]), 0.0)
            lower = np.maximum(np.expm1(lower_space), 0.0) if log_target else lower_space
            upper = np.maximum(np.expm1(upper_space), 0.0) if log_target else upper_space
        for idx, (store_nbr, family) in enumerate(keys):
            outputs.append({"date": target_date, "store_nbr": store_nbr, "family": family,
                            "forecast": float(point[idx]),
                            "lower": float(lower[idx]) if lower is not None else None,
                            "upper": float(upper[idx]) if upper is not None else None})
        work = np.vstack([work, pred_space[None, :]])
    return pd.DataFrame(outputs), new_rows, origin
