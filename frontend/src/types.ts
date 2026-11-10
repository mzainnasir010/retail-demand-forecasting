export type ChartPoint = {
  date: string;
  actual: number | null;
  forecast: number | null;
  lower: number | null;
  upper: number | null;
};

export type DashboardData = {
  mode: string;
  model_name: string;
  run_id: number;
  generated_at: string;
  horizon_days: number;
  selected_store: number | null;
  selected_family: string | null;
  summary: {
    actual_total: number;
    average_daily_actual: number;
    forecast_total: number;
    growth_pct: number | null;
    history_days: number;
  };
  series: ChartPoint[];
  metrics: { label: string; value: number | null; unit: string; detail: string }[];
  insights: { kind: string; title: string; detail: string; value?: string }[];
  model_comparison: { model: string; MAE: number | null; RMSE: number | null; sMAPE_pct: number | null }[];
  rankings: { family: string; forecast: number; share_pct: number }[];
  entities: { stores: number[]; families: string[] };
};
