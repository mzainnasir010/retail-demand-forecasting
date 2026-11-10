from collections import defaultdict
from datetime import date, timedelta
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from .models import DailyActual, ForecastPoint, ForecastRun


def latest_run(db: Session) -> ForecastRun:
    run = db.scalar(select(ForecastRun).order_by(ForecastRun.id.desc()).limit(1))
    if run is None:
        raise RuntimeError("No forecast run is available.")
    return run


def entity_options(db: Session, run_id: int) -> dict:
    actual_stores = set(db.scalars(
        select(DailyActual.store_nbr).where(DailyActual.run_id == run_id).distinct()
    ).all())
    forecast_stores = set(db.scalars(
        select(ForecastPoint.store_nbr).where(ForecastPoint.run_id == run_id).distinct()
    ).all())
    actual_families = set(db.scalars(
        select(DailyActual.family).where(DailyActual.run_id == run_id).distinct()
    ).all())
    forecast_families = set(db.scalars(
        select(ForecastPoint.family).where(ForecastPoint.run_id == run_id).distinct()
    ).all())
    return {"stores": sorted(actual_stores | forecast_stores), "families": sorted(actual_families | forecast_families)}


def dashboard_data(
    db: Session, horizon_days: int = 16, store_nbr: int | None = None,
    family: str | None = None,
) -> dict:
    run = latest_run(db)
    horizon_days = max(1, min(horizon_days, 90, run.horizon_days))
    actual_query = select(DailyActual).where(DailyActual.run_id == run.id)
    forecast_query = select(ForecastPoint).where(ForecastPoint.run_id == run.id)
    if store_nbr is not None:
        actual_query = actual_query.where(DailyActual.store_nbr == store_nbr)
        forecast_query = forecast_query.where(ForecastPoint.store_nbr == store_nbr)
    if family is not None:
        actual_query = actual_query.where(DailyActual.family == family)
        forecast_query = forecast_query.where(ForecastPoint.family == family)

    latest_query = select(func.max(DailyActual.date)).where(DailyActual.run_id == run.id)
    if store_nbr is not None:
        latest_query = latest_query.where(DailyActual.store_nbr == store_nbr)
    if family is not None:
        latest_query = latest_query.where(DailyActual.family == family)
    latest_actual_date = db.scalar(latest_query)
    if latest_actual_date is not None:
        actual_query = actual_query.where(DailyActual.date >= latest_actual_date - timedelta(days=89))
    actuals = db.scalars(actual_query.order_by(DailyActual.date)).all()
    forecasts = db.scalars(forecast_query.order_by(ForecastPoint.date)).all()
    if not actuals and not forecasts:
        return _empty_dashboard(run, horizon_days, store_nbr, family, entity_options(db, run.id))

    by_date: dict[date, dict[str, float | None]] = defaultdict(
        lambda: {"actual": None, "forecast": None, "lower": None, "upper": None}
    )
    for row in actuals:
        item = by_date[row.date]
        item["actual"] = (item["actual"] or 0.0) + row.sales
    for row in forecasts:
        item = by_date[row.date]
        item["forecast"] = (item["forecast"] or 0.0) + row.forecast
        if row.lower is not None:
            item["lower"] = (item["lower"] or 0.0) + row.lower
        if row.upper is not None:
            item["upper"] = (item["upper"] or 0.0) + row.upper

    latest_actual_date = max((r.date for r in actuals), default=latest_actual_date)
    future_dates = sorted(d for d in by_date if latest_actual_date is None or d > latest_actual_date)
    selected_future = set(future_dates[:horizon_days])
    history_dates = sorted(d for d in by_date if latest_actual_date is not None and d <= latest_actual_date)
    history_dates = history_dates[-90:]
    visible_dates = history_dates + sorted(selected_future)
    series = [
        {"date": d, **by_date[d]}
        for d in visible_dates
    ]

    horizon_actual = [
        r.sales for r in actuals
        if latest_actual_date and latest_actual_date - timedelta(days=horizon_days - 1) <= r.date <= latest_actual_date
    ]
    forecast_sum = sum(
        float(by_date[d]["forecast"] or 0)
        for d in selected_future
    )
    previous_sum = sum(horizon_actual)
    average_actual = previous_sum / max(1, len({r.date for r in actuals if latest_actual_date and latest_actual_date - timedelta(days=horizon_days - 1) <= r.date <= latest_actual_date}))
    growth = ((forecast_sum / previous_sum) - 1) * 100 if previous_sum > 0 else None
    metrics_blob = run.metrics or {}
    model_metrics = _selected_metrics(metrics_blob, run.model_name)
    model_comparison = _model_comparison(metrics_blob, run)
    metrics = [
        {"label": "Test MAE", "value": _number(model_metrics.get("MAE")), "unit": "sales", "detail": "Held-out rolling windows"},
        {"label": "Test RMSE", "value": _number(model_metrics.get("RMSE")), "unit": "sales", "detail": "Penalizes larger misses"},
        {"label": "Test sMAPE", "value": _number(model_metrics.get("sMAPE_pct")), "unit": "%", "detail": "Zero-safe percentage error"},
        {"label": "Baseline MAE", "value": _number(model_metrics.get("baseline_MAE")), "unit": "sales", "detail": "Seasonal naive comparison"},
    ]
    selected_forecasts = [row for row in forecasts if row.date in selected_future]
    insights = _make_insights(selected_forecasts, horizon_days)
    business = metrics_blob.get("business_insights", {})
    if store_nbr is None and family is None and business:
        peak_day = business.get("expected_peak_day")
        peak_units = business.get("expected_peak_units")
        if peak_day:
            insights.insert(0, {
                "kind": "positive", "title": "Expected peak day",
                "detail": f"The model projects the highest total demand on {peak_day}.",
                "value": f"{float(peak_units):,.0f} units" if peak_units is not None else "",
            })
        for item in business.get("top_growth_families", [])[:2]:
            insights.append({"kind": "positive", "title": f"{item['family']} outlook",
                "detail": "Forecast change versus the previous 30 days.",
                "value": f"+{float(item['change_pct']):.1f}%"})
        for item in business.get("top_decline_families", [])[:2]:
            insights.append({"kind": "caution", "title": f"{item['family']} outlook",
                "detail": "Forecast change versus the previous 30 days.",
                "value": f"{float(item['change_pct']):.1f}%"})
    outlook = metrics_blob.get("family_outlook", [])
    if store_nbr is not None or family is not None:
        outlook = []
    return {
        "mode": run.mode, "model_name": run.model_name, "run_id": run.id,
        "generated_at": run.created_at.isoformat(), "horizon_days": horizon_days,
        "selected_store": store_nbr, "selected_family": family,
        "summary": {
            "actual_total": round(previous_sum, 2),
            "average_daily_actual": round(average_actual, 2),
            "forecast_total": round(forecast_sum, 2),
            "growth_pct": round(growth, 2) if growth is not None else None,
            "history_days": len(history_dates),
        },
        "series": series, "metrics": metrics, "insights": insights,
        "model_comparison": model_comparison,
        "rankings": _family_rankings(selected_forecasts, outlook),
        "family_outlook": outlook,
        "figures": metrics_blob.get("figure_files", []),
        "business_insights": business,
        "run_metadata": metrics_blob.get("run_metadata", {}),
        "cleaning_log": metrics_blob.get("cleaning_log", {}),
        "entities": entity_options(db, run.id),
    }


def _selected_metrics(metrics: dict, model_name: str) -> dict:
    if any(key in metrics for key in ("MAE", "RMSE", "sMAPE_pct")):
        return metrics
    if isinstance(metrics.get("test"), dict) and any(
        key in metrics["test"] for key in ("MAE", "RMSE", "sMAPE_pct")
    ):
        return metrics["test"]
    for split in ("test", "rolling"):
        rows = metrics.get(split, [])
        if isinstance(rows, list):
            selected = next((r for r in rows if r.get("split") == "test" and r.get("model") == model_name), None)
            baseline = next((r for r in rows if r.get("split") == "test" and r.get("model") == "SeasonalNaive_7"), None)
            if selected:
                return {**selected, "baseline_MAE": baseline.get("MAE") if baseline else None}
    return {}


def _number(value) -> float | None:
    try:
        return round(float(value), 3) if value is not None else None
    except (TypeError, ValueError):
        return None


def _make_insights(rows: list[ForecastPoint], horizon_days: int) -> list[dict]:
    if not rows:
        return [{"kind": "neutral", "title": "No rows for this selection", "detail": "Choose another store or product family to view available results."}]
    by_family: dict[str, float] = defaultdict(float)
    by_store: dict[int, float] = defaultdict(float)
    for row in rows:
        by_family[row.family] += row.forecast
        by_store[row.store_nbr] += row.forecast
    top_family = max(by_family, key=by_family.get)
    top_store = max(by_store, key=by_store.get)
    intervals = [r for r in rows if r.lower is not None and r.upper is not None]
    insights = [
        {"kind": "positive", "title": "Largest forecast category", "detail": f"{top_family} leads expected demand across the selected horizon.", "value": f"{by_family[top_family]:,.0f}"},
        {"kind": "neutral", "title": "Highest-volume location", "detail": f"Store {top_store} has the largest forecast total.", "value": f"{by_store[top_store]:,.0f}"},
    ]
    if intervals:
        spread = sum(r.upper - r.lower for r in intervals) / max(1, sum(r.forecast for r in intervals))
        insights.append({
            "kind": "caution" if spread > 0.35 else "neutral",
            "title": "Forecast uncertainty",
            "detail": "Intervals are available for the selected run." if spread else "Intervals are not available for this run.",
            "value": f"{spread * 100:.1f}% average spread",
        })
    else:
        insights.append({"kind": "caution", "title": "Uncertainty unavailable", "detail": "This run contains point forecasts only; avoid treating them as exact demand.", "value": f"{horizon_days} days"})
    return insights


def _model_comparison(metrics: dict, run: ForecastRun) -> list[dict]:
    rows = metrics.get("rolling", [])
    if isinstance(rows, list) and rows:
        return [
            {"model": row["model"], "MAE": row.get("MAE"), "RMSE": row.get("RMSE"),
             "sMAPE_pct": row.get("sMAPE_pct")}
            for row in rows if row.get("split") == "test"
        ]
    values = metrics or {}
    return [
        {"model": run.model_name, "MAE": values.get("MAE"), "RMSE": values.get("RMSE"),
         "sMAPE_pct": values.get("sMAPE_pct")},
        {"model": "Seasonal naive", "MAE": values.get("baseline_mae"), "RMSE": None, "sMAPE_pct": None},
    ]


def _family_rankings(rows: list[ForecastPoint], outlook: list[dict] | None = None) -> list[dict]:
    totals: dict[str, float] = defaultdict(float)
    for row in rows:
        totals[row.family] += row.forecast
    grand_total = sum(totals.values())
    return [
        {"family": family, "forecast": round(value, 2),
         "share_pct": round(value / grand_total * 100, 1) if grand_total else 0,
         "change_pct": next((row.get("change_pct") for row in (outlook or []) if row.get("family") == family), None)}
        for family, value in sorted(totals.items(), key=lambda item: item[1], reverse=True)[:8]
    ]


def _empty_dashboard(run, horizon_days, store_nbr, family, entities):
    return {
        "mode": run.mode, "model_name": run.model_name, "run_id": run.id,
        "generated_at": run.created_at.isoformat(), "horizon_days": horizon_days,
        "selected_store": store_nbr, "selected_family": family,
        "summary": {"actual_total": 0, "average_daily_actual": 0, "forecast_total": 0, "growth_pct": None, "history_days": 0},
        "series": [], "metrics": [], "insights": [],
        "model_comparison": [], "rankings": [], "family_outlook": [], "figures": [],
        "business_insights": {}, "run_metadata": {}, "cleaning_log": {},
        "entities": entities,
    }
