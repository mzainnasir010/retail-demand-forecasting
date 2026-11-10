export type ChartPoint = {
  date: string;
  actual: number | null;
  forecast: number | null;
  lower: number | null;
  upper: number | null;
  rolling_average: number | null;
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
  rankings: { family: string; forecast: number; share_pct: number; change_pct?: number | null }[];
  family_outlook: { family: string; last30_actual: number; next30_forecast: number; change_pct: number }[];
  volatility: { store_nbr: number; family: string; mean90: number; std90: number; cv90: number }[];
  figures: string[];
  business_insights: { expected_peak_day?: string; expected_peak_units?: number; top_growth_families?: { family: string; change_pct: number }[]; top_decline_families?: { family: string; change_pct: number }[]; lowest_forecast_families?: { family: string; next30_forecast: number }[]; unavailable_inputs?: string[]; note?: string };
  run_metadata: Record<string, unknown>;
  cleaning_log: Record<string, unknown>;
  entities: { stores: number[]; families: string[] };
};
