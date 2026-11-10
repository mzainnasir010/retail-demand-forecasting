import { useEffect, useMemo, useState } from "react";
import {
  Area, CartesianGrid, ComposedChart, Line, ReferenceLine,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import {
  ArrowDownRight, ArrowUpRight, ChartLineUp, CaretDown, CircleNotch,
  DownloadSimple, Gauge, House, Lightbulb, MagnifyingGlass, Package,
  Storefront, WarningCircle,
} from "@phosphor-icons/react";
import { createPrediction, fetchDashboard, fetchHealth, fetchModelStatus } from "./api";
import type { ModelStatus } from "./api";
import type { DashboardData } from "./types";

type Section = "overview" | "performance" | "insights";
const compact = new Intl.NumberFormat("en", { notation: "compact", maximumFractionDigits: 1 });
const number = new Intl.NumberFormat("en", { maximumFractionDigits: 0 });

function formatValue(value: number | null | undefined, unit = "") {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return unit === "%" ? value.toFixed(1) + "%" : number.format(value) + (unit ? " " + unit : "");
}

function formatDate(value: string, short = false) {
  const date = new Date(value.length > 10 ? value : value + "T00:00:00");
  return new Intl.DateTimeFormat("en", {
    month: "short", day: "numeric", ...(short ? {} : { year: "numeric" }),
  }).format(date);
}

function App() {
  const [section, setSection] = useState<Section>("overview");
  const [horizon, setHorizon] = useState(30);
  const [store, setStore] = useState<number | null>(null);
  const [family, setFamily] = useState<string | null>(null);
  const [data, setData] = useState<DashboardData | null>(null);
  const [apiState, setApiState] = useState<"loading" | "ready" | "error">("loading");
  const [error, setError] = useState("");
  const [refresh, setRefresh] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setApiState("loading");
    Promise.all([
      fetchDashboard(horizon, store, family, controller.signal),
      fetchHealth(controller.signal),
    ]).then(([dashboard]) => {
      setData(dashboard);
      setApiState("ready");
      setError("");
    }).catch((reason: unknown) => {
      if (controller.signal.aborted) return;
      setError(reason instanceof Error ? reason.message : "Could not load the forecast.");
      setApiState("error");
    });
    return () => controller.abort();
  }, [horizon, store, family, refresh]);

  const chartData = useMemo(() => (data?.series ?? []).map((point) => ({
    ...point,
    band: point.lower !== null && point.upper !== null ? [point.lower, point.upper] as [number, number] : undefined,
  })), [data]);
  const actualPoints = data?.series.filter((point) => point.actual !== null) ?? [];
  const origin = actualPoints.length ? actualPoints[actualPoints.length - 1].date : undefined;
  const nav = [
    { id: "overview" as const, label: "Overview", icon: House },
    { id: "performance" as const, label: "Model performance", icon: Gauge },
    { id: "insights" as const, label: "Demand insights", icon: Lightbulb },
  ];

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark"><ChartLineUp size={19} weight="bold" /></div>
          <div><strong>fieldnote</strong><span>DEMAND PLANNING</span></div>
        </div>
        <div className="workspace-label">WORKSPACE</div>
        <nav aria-label="Main navigation">
          {nav.map(({ id, label, icon: Icon }) => (
            <button key={id} className={section === id ? "nav-item active" : "nav-item"} onClick={() => setSection(id)}>
              <Icon size={19} weight={section === id ? "fill" : "regular"} /><span>{label}</span>
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="sidebar-note">
            <span className="note-icon"><Package size={17} /></span>
            <div><strong>Planning horizon</strong><p>Prepare inventory and teams with a clear view of demand.</p></div>
          </div>
          <div className="profile">
            <div className="avatar">R</div>
            <div><strong>Demand forecast workspace</strong><span>Local workspace</span></div>
            <CaretDown size={15} />
          </div>
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div className="breadcrumbs"><span>Workspace</span><i>/</i><strong>{nav.find((item) => item.id === section)?.label}</strong></div>
          <div className="topbar-right">
            <span className={"connection " + apiState}><span />{apiState === "ready" ? "API connected" : apiState === "error" ? "API unavailable" : "Connecting"}</span>
            <button className="icon-button" aria-label="Search" title="Search"><MagnifyingGlass size={18} /></button>
            <div className="top-avatar">R</div>
          </div>
        </header>

        <div className="page-content">
          <div className="page-heading">
            <div>
              <div className="eyebrow">RETAIL · DAILY SALES</div>
              <h1>{section === "overview" ? "Demand overview" : section === "performance" ? "Model performance" : "Demand insights"}</h1>
              <p className="subheading">A clearer view of what’s moving, and what’s coming next.</p>
            </div>
            <div className="heading-actions">
              <button className="date-button" onClick={() => setRefresh((value) => value + 1)}><span className="live-dot" />Latest run<CaretDown size={15} /></button>
              <button className="primary-button" onClick={() => setSection("performance")}><ChartLineUp size={17} />New prediction</button>
            </div>
          </div>

          {apiState === "error" ? (
            <section className="error-panel">
              <WarningCircle size={27} /><h2>Couldn’t reach the forecasting service</h2>
              <p>{error}. Start the API from the backend folder, then refresh this page.</p>
              <button className="primary-button" onClick={() => setRefresh((value) => value + 1)}>Try again</button>
            </section>
          ) : apiState === "loading" && !data ? (
            <section className="loading-panel"><CircleNotch className="spin" size={27} /><span>Loading forecast workspace…</span></section>
          ) : data ? (
            <>
              <div className="filter-row">
                <div className="filter-copy"><Storefront size={17} /><span>View by</span></div>
                <label className="select-wrap">
                  <span className="sr-only">Store filter</span>
                  <select value={store ?? ""} onChange={(event) => setStore(event.target.value ? Number(event.target.value) : null)}>
                    <option value="">All stores</option>{data.entities.stores.map((item) => <option key={item} value={item}>Store {item}</option>)}
                  </select><CaretDown size={14} />
                </label>
                <label className="select-wrap family-select">
                  <span className="sr-only">Product family filter</span>
                  <select value={family ?? ""} onChange={(event) => setFamily(event.target.value || null)}>
                    <option value="">All product families</option>{data.entities.families.map((item) => <option key={item} value={item}>{item}</option>)}
                  </select><CaretDown size={14} />
                </label>
                <div className="filter-spacer" /><span className="horizon-label">Forecast</span>
                {[7, 14, 30].map((days) => (
                  <button key={days} className={horizon === days ? "horizon-chip selected" : "horizon-chip"} onClick={() => setHorizon(days)}>{days} days</button>
                ))}
              </div>
              {section === "overview" && <Overview data={data} chartData={chartData} origin={origin} />}
              {section === "performance" && <Performance data={data} onPrediction={() => { setStore(null); setFamily(null); setRefresh((value) => value + 1); }} />}
              {section === "insights" && <Insights data={data} />}
              <footer className="page-footer">
                <span>Forecast output · Run {data.run_id} · {data.model_name}</span>
                <span>Generated {formatDate(data.generated_at)}</span>
              </footer>
            </>
          ) : null}
        </div>
      </main>
    </div>
  );
}

type ChartDatum = DashboardData["series"][number] & { band?: [number, number] };

function Overview({ data, chartData, origin }: { data: DashboardData; chartData: ChartDatum[]; origin?: string }) {
  const growth = data.summary.growth_pct;
  const cards = [
    { label: "Demand · previous window", value: compact.format(data.summary.actual_total), unit: "units", hint: "Average " + compact.format(data.summary.average_daily_actual) + " per day", icon: Package, tone: "sage" },
    { label: "Forecast · next " + data.horizon_days + " days", value: compact.format(data.summary.forecast_total), unit: "units", hint: "Across selected stores and families", icon: ChartLineUp, tone: "amber" },
    { label: "Expected change", value: growth === null ? "—" : (growth > 0 ? "+" : "") + growth.toFixed(1) + "%", unit: "", hint: "Compared with the previous period", icon: growth !== null && growth < 0 ? ArrowDownRight : ArrowUpRight, tone: growth !== null && growth < 0 ? "blue" : "sage" },
  ];
  return (
    <>
      <div className="kpi-grid">
        {cards.map(({ label, value, unit, hint, icon: Icon, tone }) => (
          <article className="kpi-card" key={label}>
            <div className="kpi-top"><span>{label}</span><span className={"kpi-icon " + tone}><Icon size={18} /></span></div>
            <div className="kpi-value">{value}<small>{unit}</small></div><div className="kpi-hint">{hint}</div>
          </article>
        ))}
      </div>
      <div className="content-grid">
        <section className="panel trend-panel">
          <div className="panel-heading"><div><h2>Demand over time</h2><p>Actual sales and projected demand</p></div><span className="chart-period">Recent history · {data.horizon_days}-day outlook</span></div>
          <div className="chart-legend"><span><i className="legend-dot actual" />Actual</span><span><i className="legend-line forecast" />Forecast</span><span><i className="legend-line rolling" />7-day mean</span><span><i className="legend-band" />Uncertainty range</span></div>
          <div className="chart-wrap">
            {chartData.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={chartData} margin={{ top: 12, right: 10, left: 5, bottom: 2 }}>
                  <CartesianGrid vertical={false} stroke="#e9e9e2" strokeDasharray="3 5" />
                  <XAxis dataKey="date" tickFormatter={(value: string) => formatDate(value, true)} tickLine={false} axisLine={false} minTickGap={34} tick={{ fill: "#8b9089", fontSize: 11 }} />
                  <YAxis tickFormatter={(value: number) => compact.format(value)} tickLine={false} axisLine={false} width={47} tick={{ fill: "#8b9089", fontSize: 11 }} />
                  <Tooltip content={<ForecastTooltip />} />
                  {origin && <ReferenceLine x={origin} stroke="#a8aca6" strokeDasharray="4 4" label={{ value: "Today", position: "insideTopRight", fill: "#858b83", fontSize: 11 }} />}
                  <Area dataKey="band" type="monotone" fill="#dcece2" stroke="none" connectNulls={false} />
                  <Area dataKey="actual" type="monotone" fill="#e3efe8" fillOpacity={0.5} stroke="#4f8068" strokeWidth={2} connectNulls />
                  <Line dataKey="rolling_average" type="monotone" stroke="#78899b" strokeWidth={1.6} strokeDasharray="3 3" dot={false} connectNulls />
                  <Line dataKey="forecast" type="monotone" stroke="#c18b3f" strokeWidth={2.4} strokeDasharray="6 4" dot={false} connectNulls />
                </ComposedChart>
              </ResponsiveContainer>
            ) : <div className="empty-chart">No time-series rows are available for this selection.</div>}
          </div>
          <div className="chart-footnote">Intervals appear when provided by the model run. Point forecasts are estimates, not exact demand.</div>
        </section>
        <section className="panel signal-panel">
          <div className="panel-heading"><div><h2>Demand signals</h2><p>What stands out in this view</p></div><span className="signal-mark"><Lightbulb size={18} /></span></div>
          <div className="signal-list">
            {data.insights.map((item, index) => (
              <article className={"signal-item " + item.kind} key={item.title + index}>
                <div className="signal-marker">{item.kind === "caution" ? <WarningCircle size={16} /> : <span />}</div>
                <div className="signal-copy"><strong>{item.title}</strong><p>{item.detail}</p>{item.value && <span className="signal-value">{item.value}</span>}</div>
              </article>
            ))}
          </div>
          <div className="signal-foot">Signals reflect the selected products and stores.</div>
        </section>
      </div>
      <section className="panel ranking-panel">
        <div className="panel-heading"><div><h2>Forecast mix</h2><p>Product families by expected volume</p></div><button className="text-button">View insights <span>→</span></button></div>
        <RankingList data={data} />
      </section>
    </>
  );
}

function ForecastTooltip({ active, payload, label }: { active?: boolean; payload?: { dataKey: string; value: number }[]; label?: string }) {
  if (!active || !payload?.length) return null;
  const rows = payload.filter((entry) => ["actual", "forecast", "rolling_average"].includes(entry.dataKey) && entry.value !== undefined);
  return <div className="chart-tooltip"><strong>{label ? formatDate(label) : ""}</strong>{rows.map((row) => <div key={row.dataKey}><span>{row.dataKey === "actual" ? "Actual" : row.dataKey === "rolling_average" ? "7-day mean" : "Forecast"}</span><b>{number.format(row.value)}</b></div>)}</div>;
}

function RankingList({ data }: { data: DashboardData }) {
  return (
    <div className="ranking-list">
      {data.rankings.map((item, index) => (
        <div className="ranking-row" key={item.family}><span className="rank-number">{String(index + 1).padStart(2, "0")}</span><span className="rank-name">{item.family}</span><div className="rank-track"><span style={{ width: Math.max(4, item.share_pct) + "%" }} /></div><strong>{compact.format(item.forecast)}</strong><small>{item.change_pct == null ? `${item.share_pct}%` : `${item.change_pct > 0 ? "+" : ""}${item.change_pct.toFixed(1)}%`}</small></div>
      ))}
      {!data.rankings.length && <div className="empty-inline">No forecast categories are available.</div>}
    </div>
  );
}

function Performance({ data, onPrediction }: { data: DashboardData; onPrediction: () => void }) {
  const comparison = data.model_comparison;
  return (
    <div className="section-stack">
      <PredictionPanel modelName={data.model_name} onComplete={onPrediction} />
      <section className="panel performance-panel">
        <div className="panel-heading"><div><h2>Held-out model comparison</h2><p>Mean scores across final rolling forecast windows</p></div><span className="test-badge">TEST WINDOWS</span></div>
        {comparison.length ? (
          <div className="table-scroll"><table className="data-table">
            <thead><tr><th>Model</th><th>MAE ↓</th><th>RMSE ↓</th><th>sMAPE ↓</th><th>Status</th></tr></thead>
            <tbody>{comparison.map((row) => (
              <tr key={row.model} className={row.model === data.model_name ? "selected-model" : ""}>
                <td><span className="model-name">{row.model}</span>{row.model === data.model_name && <span className="selected-label">Selected</span>}</td>
                <td>{formatValue(row.MAE)}</td><td>{formatValue(row.RMSE)}</td><td>{formatValue(row.sMAPE_pct, "%")}</td>
                <td>{row.MAE == null ? "Not reported" : row.model === data.model_name ? "Current run" : "Compared"}</td>
              </tr>
            ))}</tbody>
          </table></div>
        ) : <div className="empty-state"><Gauge size={26} /><strong>Model comparison will appear here</strong><p>Import a Kaggle bundle containing rolling-window scores to show held-out comparisons.</p></div>}
      </section>
      <div className="metric-grid">{data.metrics.map((item) => <article className="metric-card" key={item.label}><span>{item.label}</span><strong>{formatValue(item.value, item.unit)}</strong><small>{item.detail}</small></article>)}</div>
      <section className="panel performance-panel"><div className="panel-heading"><div><h2>Evaluation reports</h2><p>Figures exported from the final Kaggle run</p></div></div><div className="report-figures">{data.figures.map((file) => <figure key={file}><img src={`/api/artifacts/${file}`} alt={file.split("/").pop()?.replace(/_/g, " ").replace(".png", "") ?? "Model evaluation figure"} /><figcaption>{file.split("/").pop()?.replace(/_/g, " ").replace(".png", "")}</figcaption></figure>)}</div></section>
      <aside className="method-note"><WarningCircle size={18} /><p>Choose using validation performance and stability. Held-out test windows provide a final check and should not be used to tune the model.</p></aside>
    </div>
  );
}

function PredictionPanel({ modelName, onComplete }: { modelName: string; onComplete: () => void }) {
  const [status, setStatus] = useState<ModelStatus | null>(null);
  const [statusError, setStatusError] = useState("");
  const [horizon, setHorizon] = useState(30);
  const [file, setFile] = useState<File | undefined>();
  const [holidayDates, setHolidayDates] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    fetchModelStatus().then((result) => { if (active) setStatus(result); })
      .catch((reason: unknown) => { if (active) setStatusError(reason instanceof Error ? reason.message : "Could not inspect the saved model."); });
    return () => { active = false; };
  }, []);

  async function generate() {
    setBusy(true); setError(""); setMessage("");
    try {
      const result = await createPrediction(horizon, file, holidayDates);
      setMessage(`Run ${result.run_id} created from ${formatDate(result.origin)}. ${number.format(result.forecast_rows)} forecasts are ready.`);
      onComplete();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Prediction could not be generated.");
    } finally { setBusy(false); }
  }

  return (
    <section className="panel prediction-panel">
      <div className="panel-heading"><div><h2>Generate a fresh forecast</h2><p>Load the saved model and run recursive predictions for all trained store and family series.</p></div><span className={status?.ready ? "model-badge ready" : "model-badge"}>{status?.ready ? "MODEL READY" : "MODEL SETUP REQUIRED"}</span></div>
      <div className="prediction-form">
        <div className="prediction-model"><span>Saved model</span><strong>{status?.model_name || modelName}</strong><small>{status?.ready ? `${status.series_count.toLocaleString()} store/family series · ${status.feature_count} trained features` : statusError || status?.reason || "Checking model files…"}</small></div>
        <label className="prediction-field"><span>Horizon</span><select value={horizon} onChange={(event) => setHorizon(Number(event.target.value))}><option value={7}>7 days</option><option value={14}>14 days</option><option value={30}>30 days</option></select></label>
        <label className="prediction-field input-file-field"><span>New observed sales CSV <small>(optional)</small></span><input type="file" accept=".csv,text/csv" onChange={(event) => setFile(event.target.files?.[0])} /></label>
        <label className="prediction-field holiday-field"><span>Known national holidays <small>(optional dates)</small></span><input type="text" value={holidayDates} placeholder="YYYY-MM-DD, YYYY-MM-DD" onChange={(event) => setHolidayDates(event.target.value)} /></label>
        {status?.ready && <a className="text-button template-link" href="/api/predictions/input-template.csv"><DownloadSimple size={15} />Download input template</a>}
        <button className="primary-button prediction-submit" disabled={!status?.ready || busy} onClick={generate}>{busy ? <CircleNotch className="spin" size={17} /> : <ChartLineUp size={17} />}{busy ? "Generating…" : "Generate forecast"}</button>
      </div>
      <p className="prediction-help">Without a file, the model uses the latest sales history already saved in this workspace. To use new data, fill the downloaded CSV: date, store_nbr, family, sales. Each appended date must include every trained series and continue directly after saved history. Add known future national holiday dates in YYYY-MM-DD format, separated by commas.</p>
      {message && <p className="prediction-message success">{message} <a href="/api/runs/latest/forecast.csv">Download forecast CSV</a></p>}{(error || statusError || (status && !status.ready && status.reason)) && <p className="prediction-message error">{error || statusError || status?.reason}</p>}
    </section>
  );
}

function Insights({ data }: { data: DashboardData }) {
  return (
    <div className="insights-layout">
      <section className="panel insight-main"><div className="panel-heading"><div><h2>What to prepare for</h2><p>Evidence from the current forecast run</p></div></div>
        <div className="insight-cards">{data.insights.map((item, index) => (
          <article className={"insight-card " + item.kind} key={item.title + index}>
            <div className="insight-card-top"><span className="insight-icon">{item.kind === "caution" ? <WarningCircle size={18} /> : <Lightbulb size={18} />}</span><span className="insight-kind">{item.kind === "caution" ? "WATCH" : "SIGNAL"}</span></div>
            <h3>{item.title}</h3><p>{item.detail}</p>{item.value && <strong className="insight-value">{item.value}</strong>}
          </article>
        ))}</div>
      </section>
      <section className="panel ranking-panel insight-ranking"><div className="panel-heading"><div><h2>Expected demand by family</h2><p>Selected horizon · forecast units</p></div></div><RankingList data={data} /></section>
      {data.family_outlook.length > 0 && <section className="panel performance-panel"><div className="panel-heading"><div><h2>30-day family outlook</h2><p>Forecast volume compared with the previous 30 days</p></div></div><div className="table-scroll"><table className="data-table"><thead><tr><th>Family</th><th>Previous 30 days</th><th>Next 30 days</th><th>Change</th></tr></thead><tbody>{data.family_outlook.map((row) => <tr key={row.family}><td>{row.family}</td><td>{number.format(row.last30_actual)}</td><td>{number.format(row.next30_forecast)}</td><td>{row.change_pct > 0 ? "+" : ""}{row.change_pct.toFixed(1)}%</td></tr>)}</tbody></table></div></section>}
      {data.volatility.length > 0 && <section className="panel performance-panel"><div className="panel-heading"><div><h2>Volatile store and family series</h2><p>Highest coefficient of variation over recent observed demand</p></div></div><div className="table-scroll"><table className="data-table"><thead><tr><th>Store</th><th>Family</th><th>90-day mean</th><th>Coefficient of variation</th></tr></thead><tbody>{data.volatility.slice(0, 12).map((row) => <tr key={`${row.store_nbr}-${row.family}`}><td>{row.store_nbr}</td><td>{row.family}</td><td>{number.format(row.mean90)}</td><td>{row.cv90.toFixed(2)}</td></tr>)}</tbody></table></div></section>}
      {(data.business_insights.lowest_forecast_families?.length ?? 0) > 0 && <section className="panel ranking-panel insight-ranking"><div className="panel-heading"><div><h2>Lowest forecast family volumes</h2><p>Low expected volume over the next 30 days; not a stockout signal</p></div></div><div className="ranking-list">{data.business_insights.lowest_forecast_families?.map((row) => <div className="ranking-row" key={row.family}><span className="rank-name">{row.family}</span><span /><span /><strong>{compact.format(row.next30_forecast)}</strong><small>units</small></div>)}</div></section>}
      <aside className="method-note"><WarningCircle size={18} /><p>Inventory risk and reorder quantities need on-hand stock and supplier lead-time data. This dashboard does not infer those values.</p></aside>
    </div>
  );
}

export default App;
