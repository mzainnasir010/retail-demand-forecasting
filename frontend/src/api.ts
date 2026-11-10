import type { DashboardData } from "./types";

export async function fetchDashboard(
  horizon: number,
  store: number | null,
  family: string | null,
  signal?: AbortSignal,
): Promise<DashboardData> {
  const query = new URLSearchParams({ horizon_days: String(horizon) });
  if (store !== null) query.set("store_nbr", String(store));
  if (family) query.set("family", family);
  const response = await fetch("/api/dashboard?" + query.toString(), { signal });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || "Forecast service returned " + response.status + ".");
  }
  return response.json() as Promise<DashboardData>;
}

export async function fetchHealth(signal?: AbortSignal) {
  const response = await fetch("/api/health", { signal });
  if (!response.ok) throw new Error("The forecasting API is unavailable.");
  return response.json() as Promise<{ status: string; mode: string; model_name: string; run_id: number }>;
}

export type ModelStatus = {
  ready: boolean;
  model_name: string;
  artifact: string | null;
  series_count: number;
  feature_count: number;
  reason: string | null;
};

export async function fetchModelStatus(): Promise<ModelStatus> {
  const response = await fetch("/api/model/status");
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.detail || "Could not inspect the saved model.");
  return body as ModelStatus;
}

export async function createPrediction(horizon: number, observations?: File, nationalHolidayDates = ""): Promise<{
  run_id: number; model_name: string; origin: string; forecast_start: string;
  forecast_end: string; horizon_days: number; forecast_rows: number;
  input_rows: number; input_kind: string;
}> {
  const form = new FormData();
  form.set("horizon_days", String(horizon));
  form.set("national_holiday_dates", nationalHolidayDates);
  if (observations) form.set("observations", observations);
  const response = await fetch("/api/predictions", { method: "POST", body: form });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.detail || "Prediction could not be generated.");
  return body;
}
