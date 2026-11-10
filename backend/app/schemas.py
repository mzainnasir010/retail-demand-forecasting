from datetime import date
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    mode: str
    model_name: str
    run_id: int


class EntityOptions(BaseModel):
    stores: list[int]
    families: list[str]


class ChartPoint(BaseModel):
    date: date
    actual: float | None = None
    forecast: float | None = None
    lower: float | None = None
    upper: float | None = None


class MetricResult(BaseModel):
    label: str
    value: float | None
    unit: str = ""
    detail: str = ""


class Insight(BaseModel):
    kind: str
    title: str
    detail: str
    value: str = ""


class DashboardResponse(BaseModel):
    mode: str
    model_name: str
    run_id: int
    generated_at: str
    horizon_days: int
    selected_store: int | None
    selected_family: str | None
    summary: dict[str, float | int | str | None]
    series: list[ChartPoint]
    metrics: list[MetricResult]
    insights: list[Insight]
    model_comparison: list[dict]
    rankings: list[dict]
    family_outlook: list[dict]
    figures: list[str]
    business_insights: dict
    run_metadata: dict
    cleaning_log: dict
    entities: EntityOptions
