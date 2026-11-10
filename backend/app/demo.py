from datetime import date, timedelta
import math
import random
from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import DailyActual, ForecastPoint, ForecastRun

FAMILIES = [
    "BEVERAGES", "GROCERY I", "PRODUCE", "DAIRY", "BREAD/BAKERY", "CLEANING",
]
STORES = [1, 2, 3, 4]


def seed_demo_data(db: Session) -> None:
    if db.scalar(select(ForecastRun.id).limit(1)) is not None:
        return

    rng = random.Random(62)
    today = date.today()
    start = today - timedelta(days=179)
    run = ForecastRun(
        mode="demo",
        model_name="Demo seasonal model",
        horizon_days=16,
        source_name="Generated sample data",
        metrics={"MAE": 18.4, "RMSE": 26.9, "sMAPE_pct": 8.7, "baseline_mae": 29.1},
    )
    db.add(run)
    db.flush()

    family_scale = {
        "BEVERAGES": 92, "GROCERY I": 148, "PRODUCE": 76,
        "DAIRY": 81, "BREAD/BAKERY": 58, "CLEANING": 41,
    }
    values: dict[tuple[int, str], list[float]] = {}
    for store in STORES:
        for family in FAMILIES:
            values[(store, family)] = []
            level = family_scale[family] * (0.76 + store * 0.085)
            for offset in range(180):
                d = start + timedelta(days=offset)
                trend = 1 + offset * (0.00065 if family in ("BEVERAGES", "PRODUCE") else 0.00015)
                weekday = [0.93, 0.97, 0.99, 1.02, 1.08, 1.16, 0.86][d.weekday()]
                seasonal = 1 + 0.06 * math.sin(offset * 2 * math.pi / 90)
                sales = max(0, level * trend * weekday * seasonal + rng.gauss(0, level * 0.075))
                values[(store, family)].append(sales)
                db.add(DailyActual(
                    run_id=run.id, date=d, store_nbr=store, family=family, sales=round(sales, 2)
                ))

    for key, history in values.items():
        store, family = key
        family_growth = 0.035 if family in ("BEVERAGES", "PRODUCE") else -0.012
        baseline = history[-7:]
        for step in range(1, 17):
            d = today + timedelta(days=step)
            weekday = [0.93, 0.97, 0.99, 1.02, 1.08, 1.16, 0.86][d.weekday()]
            prediction = max(0, sum(baseline[(step - 1) % 7::7] or baseline) / max(1, len(baseline)) * weekday)
            prediction *= 1 + family_growth * step / 16
            width = prediction * (0.10 + step * 0.004)
            db.add(ForecastPoint(
                run_id=run.id, date=d, store_nbr=store, family=family,
                forecast=round(prediction, 2),
                lower=round(max(0, prediction - width), 2),
                upper=round(prediction + width, 2),
                onpromotion=0,
            ))
    db.commit()
