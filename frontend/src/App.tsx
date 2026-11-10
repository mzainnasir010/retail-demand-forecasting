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
import { fetchDashboard, fetchHealth } from "./api";
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
  const [horizon, setHorizon] = useState(16);
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
            <div className="avatar">S</div>
            <div><strong>SEKER AI project</strong><span>Local workspace</span></div>
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
            <div className="top-avatar">S</div>
          </div>
        </header>

        <div className="page-content">
          {data?.mode === "demo" && (
            <div className="demo-banner">
              <span className="demo-dot" />
              <span><strong>Sample data</strong> — preview only. Import your Kaggle run when training is complete.</span>
              <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer">API docs <span>↗</span></a>
            </div>
          )}
          <div className="page-heading">
            <div>
              <div className="eyebrow">RETAIL · DAILY SALES</div>
              <h1>{section === "overview" ? "Demand overview" : section === "performance" ? "Model performance" : "Demand insights"}</h1>
              <p className="subheading">A clearer view of what’s moving, and what’s coming next.</p>
            </div>
            <div className="heading-actions">
              <button className="date-button" onClick={() => setRefresh((value) => value + 1)}><span className="live-dot" />Latest run<CaretDown size={15} /></button>
              <button className="primary-button" onClick={() => setRefresh((value) => value + 1)}><DownloadSimple size={17} />Refresh data</button>
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
                {[7, 16].map((days) => (
                  <button key={days} className={horizon === days ? "horizon-chip selected" : "horizon-chip"} onClick={() => setHorizon(days)}>{days} days</button>
                ))}
              </div>
              {section === "overview" && <Overview data={data} chartData={chartData} origin={origin} />}
              {section === "performance" && <Performance data={data} />}
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
          <div className="chart-legend"><span><i className="legend-dot actual" />Actual</span><span><i className="legend-line forecast" />Forecast</span><span><i className="legend-band" />Uncertainty range</span></div>
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
  const rows = payload.filter((entry) => ["actual", "forecast"].includes(entry.dataKey) && entry.value !== undefined);
  return <div className="chart-tooltip"><strong>{label ? formatDate(label) : ""}</strong>{rows.map((row) => <div key={row.dataKey}><span>{row.dataKey === "actual" ? "Actual" : "Forecast"}</span><b>{number.format(row.value)}</b></div>)}</div>;
}

function RankingList({ data }: { data: DashboardData }) {
  return (
    <div className="ranking-list">
      {data.rankings.map((item, index) => (
        <div className="ranking-row" key={item.family}><span className="rank-number">{String(index + 1).padStart(2, "0")}</span><span className="rank-name">{item.family}</span><div className="rank-track"><span style={{ width: Math.max(4, item.share_pct) + "%" }} /></div><strong>{compact.format(item.forecast)}</strong><small>{item.share_pct}%</small></div>
      ))}
      {!data.rankings.length && <div className="empty-inline">No forecast categories are available.</div>}
    </div>
  );
}

function Performance({ data }: { data: DashboardData }) {
  const comparison = data.model_comparison;
  return (
    <div className="section-stack">
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
      <aside className="method-note"><WarningCircle size={18} /><p>Choose using validation performance and stability. Held-out test windows provide a final check and should not be used to tune the model.</p></aside>
    </div>
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
      <aside className="method-note"><WarningCircle size={18} /><p>Inventory risk and reorder quantities need on-hand stock and supplier lead-time data. This dashboard does not infer those values.</p></aside>
    </div>
  );
}

export default App;
