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
