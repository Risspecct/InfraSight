import { useEffect, useState } from "react";
import { Link, NavLink, useLocation, useNavigate, useParams } from "react-router-dom";
import {
  Activity,
  AlertTriangle,
  ArrowLeft,
  ArrowUpRight,
  BrainCircuit,
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  CircleAlert,
  Gauge,
  Landmark,
  LoaderCircle,
  MapPin,
  RefreshCw,
  Search,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  Target,
  TrendingUp,
  TriangleAlert,
} from "lucide-react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "./api/client";

const riskOrder = ["CRITICAL", "HIGH", "MEDIUM", "LOW"];

function formatDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? "—"
    : date.toLocaleDateString(undefined, {
        month: "short",
        day: "numeric",
        year: "numeric",
      });
}

function displayText(value, fallback = "—") {
  if (value === null || value === undefined || value === "") return fallback;
  const text = String(value).trim();
  return /^(nan|null|undefined)$/i.test(text) ? fallback : text;
}

function displayNumber(value, digits = 1, suffix = "") {
  return typeof value === "number" && Number.isFinite(value)
    ? `${value.toLocaleString(undefined, { maximumFractionDigits: digits })}${suffix}`
    : "—";
}

function probabilityWidth(value) {
  return typeof value === "number" && Number.isFinite(value)
    ? `${Math.max(0, Math.min(value, 1)) * 100}%`
    : "0%";
}

function magnitude(value) {
  return typeof value === "number" && Number.isFinite(value)
    ? Math.abs(value)
    : 0;
}

function percent(value) {
  return typeof value === "number" && Number.isFinite(value)
    ? `${(value * 100).toFixed(1)}%`
    : "—";
}

function riskClass(level = "") {
  return displayText(level, "unassessed").toLowerCase().replace(/\s+/g, "-");
}

function RiskBadge({ level }) {
  return (
    <span className={`risk-badge ${riskClass(level)}`}>
      <span className="status-dot" />
      {displayText(level, "UNASSESSED")}
    </span>
  );
}

function LoadingState({ label = "Loading intelligence" }) {
  return (
    <div className="state-panel">
      <div className="skeleton-state" aria-label={label}>
        <span />
        <span />
        <span />
      </div>
      <span className="sr-only">{label}</span>
    </div>
  );
}

function ErrorState({ error, onRetry }) {
  return (
    <div className="state-panel error-state">
      <CircleAlert size={22} />
      <div>
        <strong>Unable to load this view</strong>
        <p>{error?.message || "The API returned an unexpected response."}</p>
      </div>
      {onRetry && (
        <button className="icon-button" onClick={onRetry} title="Retry">
          <RefreshCw size={17} />
        </button>
      )}
    </div>
  );
}

function EmptyState({ message }) {
  return (
    <div className="state-panel">
      <ShieldCheck size={22} />
      <span>{message}</span>
    </div>
  );
}

function Pagination({ page, totalPages, onChange }) {
  if (!totalPages || totalPages <= 1) return null;
  return (
    <div className="pagination">
      <button
        className="icon-button"
        disabled={page <= 1}
        onClick={() => onChange(page - 1)}
        title="Previous page"
      >
        <ChevronLeft size={17} />
      </button>
      <span>
        Page <strong>{page}</strong> of {totalPages}
      </span>
      <button
        className="icon-button"
        disabled={page >= totalPages}
        onClick={() => onChange(page + 1)}
        title="Next page"
      >
        <ChevronRight size={17} />
      </button>
    </div>
  );
}

function Navbar() {
  const location = useLocation();
  const projectSelected = location.pathname.startsWith("/projects/");
  return (
    <header className="topbar">
      <Link className="brand" to="/">
        <span className="brand-mark">
          <Activity size={19} />
        </span>
        <span>INFRA<span>SIGHT</span></span>
      </Link>
      <nav className="topnav" aria-label="Primary navigation">
        <NavLink to="/" end><Activity size={15} /><span>Portfolio Intelligence</span></NavLink>
        <NavLink to="/projects"><Landmark size={15} /><span>Project Ledger</span></NavLink>
        {projectSelected && <NavLink to={location.pathname} className="docket-link"><CircleAlert size={15} /><span>Risk Docket</span></NavLink>}
      </nav>
    </header>
  );
}

function Shell({ children }) {
  return (
    <div className="app-shell">
      <Navbar />
      <div className="content-shell"><main>{children}</main>
      <footer>
        <span>INFRA SIGHT / PREDICTIVE INFRASTRUCTURE MONITORING</span>
        <span>Decision support, grounded in historical evidence</span>
      </footer>
      </div>
    </div>
  );
}

function StatCard({ label, value, detail, icon: Icon, tone = "" }) {
  return (
    <div className={`stat-card ${tone}`}>
      <div className="stat-label">
        <Icon size={16} />
        {label}
      </div>
      <strong>{value}</strong>
      <span>{detail}</span>
    </div>
  );
}

function RiskDistribution({ items }) {
  const counts = riskOrder.map((level) => ({
    level,
    count: items.filter((item) => item.risk_level === level).length,
  }));
  const total = items.length;
  return (
    <section className="panel distribution">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">CURRENT PAGE</span>
          <h2>Risk distribution</h2>
        </div>
        <span className="muted">{total} assessed projects</span>
      </div>
      {total === 0 ? (
        <EmptyState message="No risk assessments are available on this page." />
      ) : (
        <div className="distribution-grid">
          {counts.map(({ level, count }) => (
            <div className="distribution-item" key={level}>
              <div className="distribution-top">
                <RiskBadge level={level} />
                <strong>{count}</strong>
              </div>
              <div className="distribution-track">
                <span
                  className={`fill ${riskClass(level)}`}
                  style={{ width: `${total ? (count / total) * 100 : 0}%` }}
                />
              </div>
              <small>
                {total ? Math.round((count / total) * 100) : 0}% of current page
              </small>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

function RiskTable({ items }) {
  const navigate = useNavigate();
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Project</th>
            <th>Assessment</th>
            <th>Cost risk</th>
            <th>Schedule risk</th>
            <th>Risk level</th>
            <th>Priority</th>
            <th>Signal</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr
              key={`${item.project_id}-${item.observation_id}`}
              onClick={() =>
                navigate(`/projects/${encodeURIComponent(item.project_id)}`)
              }
            >
              <td>
                <strong>{displayText(item.project_name)}</strong>
                <small>{displayText(item.project_id)}</small>
              </td>
              <td>{formatDate(item.assessment_date)}</td>
              <td>
                <span className="metric-value">
                  {percent(item.cost_probability)}
                </span>
                <div className="mini-bar">
                  <span
                    className="cost"
                    style={{ width: probabilityWidth(item.cost_probability) }}
                  />
                </div>
              </td>
              <td>
                <span className="metric-value">
                  {percent(item.schedule_probability)}
                </span>
                <div className="mini-bar">
                  <span
                    className="schedule"
                    style={{ width: probabilityWidth(item.schedule_probability) }}
                  />
                </div>
              </td>
              <td>
                <RiskBadge level={item.risk_level} />
              </td>
              <td>
                <strong>{displayNumber(item.priority_score)}</strong>
              </td>
              <td>
                {item.early_warning ? (
                  <span className="warning">
                    <TriangleAlert size={15} /> Early warning
                  </span>
                ) : (
                  <span className="muted">Monitoring</span>
                )}
              </td>
              <td>
                <ArrowUpRight size={17} className="row-arrow" />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function PortfolioPage() {
  const [data, setData] = useState(null);
  const [page, setPage] = useState(1);
  const [query, setQuery] = useState("");
  const [riskFilter, setRiskFilter] = useState("ALL");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = () => {
    setLoading(true);
    setError(null);
    api
      .getPortfolioRisk(page, 20)
      .then((response) => {
        console.log("PORTFOLIO API RESPONSE:", response);
        setData(response);
      })
      .catch(setError)
      .finally(() => setLoading(false));
  };
  useEffect(() => {
    api
      .getPortfolioRisk(page, 20)
      .then((response) => {
        console.log("PORTFOLIO API RESPONSE:", response);
        setData(response);
      })
      .catch(setError)
      .finally(() => setLoading(false));
  }, [page]);
  const hasItemsArray = Array.isArray(data?.items);
  const items = hasItemsArray ? data.items : [];
  const visibleItems = items.filter(
    (item) =>
      (riskFilter === "ALL" || item.risk_level === riskFilter) &&
      displayText(item.project_name).toLowerCase().includes(query.toLowerCase()),
  );
  const earlyWarnings = items.filter((item) => item.early_warning).length;
  const critical = items.filter(
    (item) => item.risk_level === "CRITICAL",
  ).length;
  const high = items.filter((item) => item.risk_level === "HIGH").length;

  return (
    <Shell>
      <div className="page-heading">
        <div>
          <span className="eyebrow">PORTFOLIO / COMMAND CENTER</span>
          <h1>See risk before it becomes delay.</h1>
          <p>
            Evidence-led oversight across the infrastructure portfolio, ranked
            by backend priority.
          </p>
        </div>
        <div className="heading-aside">
          <span className="live-pulse" /> Assessment feed active
          <br />
          <small>Page-level risk view</small>
        </div>
      </div>
      {loading ? (
        <div className="state-panel">Loading portfolio data...</div>
      ) : error ? (
        <ErrorState error={error} onRetry={load} />
      ) : !hasItemsArray || items.length === 0 ? (
        <div className="state-panel">
          No projects found or data mapping failed. Check console.
        </div>
      ) : (
        <>
          <section className="stat-grid">
            <StatCard
              label="Total portfolio"
              value={data?.total ?? "—"}
              detail="Projects in backend index"
              icon={Landmark}
            />
            <StatCard
              label="Critical on page"
              value={critical}
              detail="Current risk distribution"
              icon={CircleAlert}
              tone="critical"
            />
            <StatCard
              label="High on page"
              value={high}
              detail="Current risk distribution"
              icon={AlertTriangle}
              tone="high"
            />
            <StatCard
              label="Early warnings"
              value={earlyWarnings}
              detail="Current page only"
              icon={Target}
              tone="warning"
            />
          </section>
          <div className="dashboard-grid">
            <RiskDistribution items={items} />
            <section className="panel priority-panel">
              <div className="panel-heading">
                <div>
                  <span className="eyebrow">BACKEND RANKING</span>
                  <h2>Highest priority signals</h2>
                </div>
                <TrendingUp size={19} />
              </div>
              {items.length === 0 ? (
                <EmptyState message="No portfolio risk records returned." />
              ) : (
                <div className="priority-list">
                  {items.slice(0, 4).map((item) => (
                    <Link
                      to={`/projects/${encodeURIComponent(item.project_id)}`}
                      className="priority-row"
                      key={item.project_id}
                    >
                      <span
                        className={`priority-index ${riskClass(item.risk_level)}`}
                      >
                        {String(items.indexOf(item) + 1).padStart(2, "0")}
                      </span>
                      <span className="priority-project">
                        <strong>{displayText(item.project_name)}</strong>
                        <small>
                          {formatDate(item.assessment_date)} ·{" "}
                          {item.observation_id}
                        </small>
                      </span>
                      <span className="priority-score">
                        {displayNumber(item.priority_score)}
                        <small>priority</small>
                      </span>
                      <ArrowUpRight size={16} />
                    </Link>
                  ))}
                </div>
              )}
            </section>
          </div>
          <section className="panel table-panel">
            <div className="panel-heading table-heading">
              <div>
                <span className="eyebrow">PORTFOLIO WATCHLIST</span>
                <h2>Risk-ranked projects</h2>
                <p>
                  Backend priority order is preserved. Filters apply to the
                  current page.
                </p>
              </div>
              <div className="table-tools">
                <label className="search-field">
                  <Search size={16} />
                  <input
                    value={query}
                    onChange={(event) => setQuery(event.target.value)}
                    placeholder="Search current page"
                    aria-label="Search current page"
                  />
                </label>
                <label className="select-field">
                  <SlidersHorizontal size={15} />
                  <select
                    value={riskFilter}
                    onChange={(event) => setRiskFilter(event.target.value)}
                    aria-label="Filter by risk level"
                  >
                    <option value="ALL">All levels</option>
                    {riskOrder.map((level) => (
                      <option key={level} value={level}>
                        {level}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
            </div>
            {visibleItems.length === 0 ? (
              <EmptyState message="No projects match the current page filters." />
            ) : (
              <RiskTable items={visibleItems} />
            )}
            <div className="table-footer">
              <span>
                Showing {visibleItems.length} of {items.length} loaded
                assessments · {data?.total ?? 0} total projects
              </span>
              <Pagination
                page={data?.page || page}
                totalPages={data?.total_pages}
                onChange={setPage}
              />
            </div>
          </section>
        </>
      )}
    </Shell>
  );
}

function MetricCard({ label, value, threshold, flagged, tone }) {
  return (
    <div className="metric-card">
      <div className="metric-card-top">
        <span>{label}</span>
        <span className={`flag ${flagged ? "is-flagged" : ""}`}>
          {flagged ? "Flagged" : "Below threshold"}
        </span>
      </div>
      <strong>{percent(value)}</strong>
      <div className="threshold-track">
        <span className={tone} style={{ width: probabilityWidth(value) }} />
        <i style={{ left: probabilityWidth(threshold) }} />
      </div>
      <small>Threshold {percent(threshold)}</small>
    </div>
  );
}

function Drivers({ title, drivers }) {
  return (
    <div className="driver-column">
      <div className="subheading">
        <h3>{title}</h3>
        <span>Model contribution, not causality</span>
      </div>
      {!drivers?.length ? (
        <EmptyState message="No drivers returned for this checkpoint." />
      ) : (
        drivers.map((driver) => (
          <div
            className="driver"
            key={`${driver.feature}-${driver.shap_value}`}
          >
            <div className="driver-heading">
              <strong>{driver.label}</strong>
              <span className={driver.direction}>
                {driver.direction === "positive" ? "+" : "−"}{" "}
                {displayNumber(magnitude(driver.shap_value), 3)}
              </span>
            </div>
            <div className="driver-track">
              <span
                className={driver.direction}
                style={{
                  width: `${Math.min(magnitude(driver.shap_value) * 55, 100)}%`,
                }}
              />
            </div>
            <small>
              {displayNumber(driver.value, 3)} · {displayText(driver.feature)}
            </small>
          </div>
        ))
      )}
    </div>
  );
}

function DecisionPanel({ prediction, decision, action, onEvaluate }) {
  return (
    <section className="panel decision-panel">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">DECISION SUPPORT</span>
          <h2>Translate risk into a decision signal</h2>
          <p>
            Evaluate the selected prediction using the backend decision engine.
          </p>
        </div>
        <ShieldCheck size={20} />
      </div>
      {decision ? (
        <div className="decision-result">
          <div>
            <span>Decision assessment</span>
            <RiskBadge level={decision.risk_level} />
          </div>
          <strong>
            {Number.isFinite(decision.priority_score)
              ? decision.priority_score.toFixed(1)
              : "—"}
          </strong>
          <small>
            Backend priority score ·{" "}
            {decision.early_warning
              ? "Early warning active"
              : "No early warning"}
          </small>
          <div className="decision-facts">
            <span>
              Cost threshold:{" "}
              {decision.cost_risk.flagged ? "Flagged" : "Below threshold"}
            </span>
            <span>
              Schedule threshold:{" "}
              {decision.schedule_risk.flagged ? "Flagged" : "Below threshold"}
            </span>
          </div>
        </div>
      ) : (
        <div className="action-empty">
          <p>
            {prediction
              ? "Use the current prediction as the decision engine input."
              : "Run a risk assessment before evaluating a decision."}
          </p>
          <button
            className="secondary-button"
            disabled={!prediction || action === "decision"}
            onClick={onEvaluate}
          >
            {action === "decision" ? (
              <LoaderCircle className="spin" size={16} />
            ) : (
              <ShieldCheck size={16} />
            )}{" "}
            Evaluate decision signal
          </button>
        </div>
      )}
    </section>
  );
}

function DetailPage() {
  const { projectId } = useParams();
  const [project, setProject] = useState(null);
  const [observations, setObservations] = useState(null);
  const [trajectory, setTrajectory] = useState(null);
  const [selectedId, setSelectedId] = useState("");
  const [prediction, setPrediction] = useState(null);
  const [explanation, setExplanation] = useState(null);
  const [backtest, setBacktest] = useState(null);
  const [intelligence, setIntelligence] = useState(null);
  const [decision, setDecision] = useState(null);
  const [loading, setLoading] = useState(true);
  const [action, setAction] = useState("");
  const [error, setError] = useState(null);

  const load = () => {
    setLoading(true);
    setError(null);
    Promise.all([
      api.getProject(projectId),
      api.getObservations(projectId),
      api.getTrajectory(projectId),
    ])
      .then(([projectData, observationData, trajectoryData]) => {
        setProject(projectData);
        setObservations(observationData);
        setTrajectory(trajectoryData);
        setSelectedId(
          (current) =>
            current ||
            observationData.items[observationData.items.length - 1]
              ?.observation_id ||
            "",
        );
      })
      .catch(setError)
      .finally(() => setLoading(false));
  };
  useEffect(() => {
    Promise.all([
      api.getProject(projectId),
      api.getObservations(projectId),
      api.getTrajectory(projectId),
    ])
      .then(([projectData, observationData, trajectoryData]) => {
        setProject(projectData);
        setObservations(observationData);
        setTrajectory(trajectoryData);
        setSelectedId(
          (current) =>
            current ||
            observationData.items[observationData.items.length - 1]
              ?.observation_id ||
            "",
        );
      })
      .catch(setError)
      .finally(() => setLoading(false));
  }, [projectId]);
  const selected = observations?.items.find(
    (item) => item.observation_id === selectedId,
  );
  const runAction = (name, callback) => {
    setAction(name);
    setError(null);
    callback()
      .then((value) => {
        if (name === "prediction") setPrediction(value);
        if (name === "explanation") setExplanation(value);
        if (name === "backtest") setBacktest(value);
        if (name === "intelligence") setIntelligence(value);
        if (name === "decision") setDecision(value);
      })
      .catch(setError)
      .finally(() => setAction(""));
  };
  const runCheckpoint = (id) => {
    setSelectedId(id);
    setPrediction(null);
    setExplanation(null);
    setBacktest(null);
    setIntelligence(null);
    setDecision(null);
  };

  if (loading)
    return (
      <Shell>
        <LoadingState label="Loading project intelligence" />
      </Shell>
    );
  if (error && !project)
    return (
      <Shell>
        <ErrorState error={error} onRetry={load} />
      </Shell>
    );
  return (
    <Shell>
      <Link to="/" className="back-link">
        <ArrowLeft size={16} /> Back to command center
      </Link>
      <section className="project-hero">
        <div>
          <span className="eyebrow">PROJECT INTELLIGENCE</span>
          <h1>{displayText(project.project_name)}</h1>
          <div className="project-meta">
            <span>{project.project_code || project.project_id}</span>
            <span>
              <Landmark size={14} /> {displayText(project.agency, "Unreported")}
            </span>
            <span>
              <MapPin size={14} /> {displayText(project.state, "Unreported")}
            </span>
            <span>{displayText(project.sector, "Unreported")}</span>
          </div>
        </div>
        <div className="identity-box">
          <span>Identity confidence</span>
          <strong>{displayText(project.identity_confidence)}</strong>
          <small>{displayNumber(project.observation_count, 0)} historical checkpoints</small>
        </div>
      </section>
      <section className="overview-strip">
        <div>
          <span>First report</span>
          <strong>{formatDate(project.first_report_date)}</strong>
        </div>
        <div>
          <span>Latest report</span>
          <strong>{formatDate(project.last_report_date)}</strong>
        </div>
        <div>
          <span>Project ID</span>
          <strong>{project.project_id}</strong>
        </div>
        <div>
          <span>Analysis point</span>
          <strong>
            {selected
              ? formatDate(selected.report_date)
              : "Select a checkpoint"}
          </strong>
        </div>
      </section>
      {error && <ErrorState error={error} />}
      <div className="detail-layout">
        <div className="detail-main">
          <section className="panel checkpoint-panel">
            <div className="panel-heading">
              <div>
                <span className="eyebrow">POINT-IN-TIME ANALYSIS</span>
                <h2>Historical checkpoints</h2>
                <p>Select a report to anchor every risk explanation below.</p>
              </div>
              <CalendarDays size={19} />
            </div>
            {observations?.items.length ? (
              <div className="checkpoint-list">
                {observations.items.map((observation) => (
                  <button
                    className={`checkpoint ${selectedId === observation.observation_id ? "selected" : ""}`}
                    key={observation.observation_id}
                    onClick={() => runCheckpoint(observation.observation_id)}
                  >
                    <span className="checkpoint-date">
                      {formatDate(observation.report_date)}
                    </span>
                    <span>{displayText(observation.status, "Unreported")}</span>
                    <strong>
                      {observation.physical_progress_pct != null
                        ? `${observation.physical_progress_pct}% progress`
                        : "Unreported"}
                    </strong>
                    <small>{observation.observation_id}</small>
                  </button>
                ))}
              </div>
            ) : (
              <EmptyState message="No observations available for this project." />
            )}
          </section>
          <section className="panel prediction-panel">
            <div className="panel-heading">
              <div>
                <span className="eyebrow">SELECTED CHECKPOINT</span>
                <h2>Predictive risk</h2>
                <p>
                  {selected
                    ? `${formatDate(selected.report_date)} · ${selected.observation_id}`
                    : "Select a historical checkpoint to begin."}
                </p>
              </div>
              <Gauge size={21} />
            </div>
            {prediction ? (
              <>
                <div className="prediction-grid">
                  <MetricCard
                    label="Cost overrun risk"
                    value={prediction.cost_overrun_probability}
                    threshold={prediction.cost_risk.threshold}
                    flagged={prediction.cost_risk.flagged}
                    tone="cost"
                  />
                  <MetricCard
                    label="Schedule overrun risk"
                    value={prediction.schedule_overrun_probability}
                    threshold={prediction.schedule_risk.threshold}
                    flagged={prediction.schedule_risk.flagged}
                    tone="schedule"
                  />
                  <div className="risk-outcome">
                    <span>Backend assessment</span>
                    <RiskBadge level={prediction.risk_level} />
                    <strong>{displayNumber(prediction.priority_score)}</strong>
                    <small>Priority score</small>
                  </div>
                </div>
                <div className="prediction-footer">
                  <span>
                    <CalendarDays size={15} /> Predicted{" "}
                    {formatDate(prediction.prediction_date)}
                  </span>
                  <span
                    className={prediction.early_warning ? "warning" : "muted"}
                  >
                    {prediction.early_warning
                      ? "Early warning active"
                      : "No early warning"}
                  </span>
                </div>
              </>
            ) : (
              <div className="action-empty">
                <p>Run the model for this exact historical checkpoint.</p>
                <button
                  className="primary-button"
                  disabled={!selected || action === "prediction"}
                  onClick={() =>
                    runAction("prediction", () =>
                      api.predict(projectId, selectedId),
                    )
                  }
                >
                  {action === "prediction" ? (
                    <LoaderCircle className="spin" size={16} />
                  ) : (
                    <Gauge size={16} />
                  )}{" "}
                  Run risk assessment
                </button>
              </div>
            )}
          </section>
          <DecisionPanel
            prediction={prediction}
            decision={decision}
            action={action}
            onEvaluate={() =>
              runAction("decision", () =>
                api.evaluateDecision({
                  project_id: project.project_id,
                  prediction_date: prediction.prediction_date,
                  cost_probability: prediction.cost_overrun_probability,
                  schedule_probability: prediction.schedule_overrun_probability,
                }),
              )
            }
          />
          <section className="panel drivers-panel">
            <div className="panel-heading">
              <div>
                <span className="eyebrow">MODEL EXPLANATION</span>
                <h2>Why is this project at risk?</h2>
                <p>
                  Drivers show how features contributed to the model output at
                  the selected checkpoint.
                </p>
              </div>
              <BrainCircuit size={20} />
            </div>
            {explanation ? (
              <div className="drivers-grid">
                <Drivers
                  title="Cost risk drivers"
                  drivers={explanation.cost_drivers}
                />
                <Drivers
                  title="Schedule risk drivers"
                  drivers={explanation.schedule_drivers}
                />
              </div>
            ) : (
              <div className="action-empty">
                <p>Inspect the strongest cost and schedule contributors.</p>
                <button
                  className="secondary-button"
                  disabled={!selected || action === "explanation"}
                  onClick={() =>
                    runAction("explanation", () =>
                      api.getExplanation(projectId, selectedId),
                    )
                  }
                >
                  {action === "explanation" ? (
                    <LoaderCircle className="spin" size={16} />
                  ) : (
                    <BrainCircuit size={16} />
                  )}{" "}
                  Load risk drivers
                </button>
              </div>
            )}
          </section>
          <section className="panel trajectory-panel">
            <div className="panel-heading">
              <div>
                <span className="eyebrow">LONGITUDINAL VIEW</span>
                <h2>Risk trajectory</h2>
                <p>
                  When did risk begin to rise across historical assessments?
                </p>
              </div>
              <TrendingUp size={20} />
            </div>
            {trajectory?.trajectory?.length ? (
              <div className="chart-wrap">
                <ResponsiveContainer width="100%" height={280}>
                  <LineChart
                    data={trajectory.trajectory}
                    margin={{ top: 10, right: 16, left: -16, bottom: 0 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis
                      dataKey="assessment_date"
                      tickFormatter={(value) =>
                        formatDate(value).replace(/,? \d{4}/, "")
                      }
                    />
                    <YAxis
                      domain={[0, 1]}
                      tickFormatter={(value) => `${value * 100}%`}
                    />
                    <Tooltip
                      formatter={(value, name) => [
                        percent(value),
                        name === "cost_probability"
                          ? "Cost risk"
                          : "Schedule risk",
                      ]}
                      labelFormatter={(label) => formatDate(label)}
                    />
                    <Line
                      type="monotone"
                      dataKey="cost_probability"
                      stroke="#d45f4d"
                      strokeWidth={2.5}
                      dot={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="schedule_probability"
                      stroke="#188b83"
                      strokeWidth={2.5}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
                <div className="chart-legend">
                  <span>
                    <i className="legend-cost" /> Cost risk
                  </span>
                  <span>
                    <i className="legend-schedule" /> Schedule risk
                  </span>
                </div>
              </div>
            ) : (
              <EmptyState message="No risk trajectory returned for this project." />
            )}
          </section>
          <section className="panel backtest-panel">
            <div className="panel-heading">
              <div>
                <span className="eyebrow">HISTORICAL VALIDATION</span>
                <h2>What happened afterward?</h2>
                <p>
                  Compare a checkpoint prediction with the future observed
                  horizon.
                </p>
              </div>
              <Target size={20} />
            </div>
            {backtest ? (
              <div className="backtest-grid">
                <div className="backtest-step">
                  <span>Prediction at checkpoint</span>
                  <strong>{formatDate(backtest.prediction_date)}</strong>
                  <p>
                    Cost {percent(backtest.predicted.cost_probability)} ·
                    Schedule {percent(backtest.predicted.schedule_probability)}
                  </p>
                </div>
                <div className="backtest-arrow">→</div>
                <div className="backtest-step">
                  <span>Future reporting horizon</span>
                  <strong>{backtest.horizon_observations} observations</strong>
                  <p>
                    {backtest.horizon_complete
                      ? "Complete horizon"
                      : "Horizon incomplete"}
                  </p>
                </div>
                <div className="backtest-arrow">→</div>
                <div className="backtest-step outcome">
                  <span>Observed outcome</span>
                  <strong>
                    {backtest.actual.cost_deterioration == null
                      ? "Not available"
                      : `Cost ${backtest.actual.cost_deterioration ? "deteriorated" : "held"}`}
                  </strong>
                  <p>
                    {backtest.actual.schedule_deterioration == null
                      ? "Schedule outcome not available"
                      : `Schedule ${backtest.actual.schedule_deterioration ? "deteriorated" : "held"}`}
                  </p>
                </div>
              </div>
            ) : (
              <div className="action-empty">
                <p>
                  Use the selected checkpoint to inspect future observed
                  outcomes.
                </p>
                <button
                  className="secondary-button"
                  disabled={!selected || action === "backtest"}
                  onClick={() =>
                    runAction("backtest", () =>
                      api.getBacktest(projectId, selectedId),
                    )
                  }
                >
                  {action === "backtest" ? (
                    <LoaderCircle className="spin" size={16} />
                  ) : (
                    <Target size={16} />
                  )}{" "}
                  Load historical backtest
                </button>
              </div>
            )}
          </section>
          <section className="panel intelligence-panel">
            <div className="panel-heading">
              <div>
                <span className="eyebrow">GROUNDED AI</span>
                <h2>AI risk intelligence</h2>
                <p>
                  Generate an evidence-grounded intervention for the selected
                  observation.
                </p>
              </div>
              <Sparkles size={20} />
            </div>
            {intelligence ? (
              <div className="intelligence-content">
                <div className="intelligence-summary">
                  <span>Summary</span>
                  <p>{intelligence.summary}</p>
                </div>
                <div className="intelligence-columns">
                  <div>
                    <span>Risk explanation</span>
                    <p>{intelligence.risk_explanation}</p>
                  </div>
                  <div>
                    <span>Recommended intervention</span>
                    <strong>{intelligence.intervention.action}</strong>
                    <p>{intelligence.intervention.rationale}</p>
                    <small>
                      Priority: {intelligence.intervention.priority}
                    </small>
                  </div>
                </div>
                <div className="evidence">
                  <span>Key evidence</span>
                  <ul>
                    {intelligence.key_evidence.map((evidence) => (
                      <li key={evidence}>{evidence}</li>
                    ))}
                  </ul>
                </div>
                <div className="limitations">
                  <span>Limitations</span>
                  <ul>
                    {intelligence.limitations.map((limitation) => (
                      <li key={limitation}>{limitation}</li>
                    ))}
                  </ul>
                </div>
              </div>
            ) : (
              <div className="action-empty">
                <p>
                  Ask the intelligence service to synthesize evidence and
                  recommend the next intervention.
                </p>
                <button
                  className="primary-button"
                  disabled={!selected || action === "intelligence"}
                  onClick={() =>
                    runAction("intelligence", () =>
                      api.getIntelligence(
                        projectId,
                        selectedId,
                        "Explain the current project risk and recommend the most important intervention.",
                      ),
                    )
                  }
                >
                  {action === "intelligence" ? (
                    <LoaderCircle className="spin" size={16} />
                  ) : (
                    <Sparkles size={16} />
                  )}{" "}
                  Generate AI intelligence
                </button>
              </div>
            )}
          </section>
        </div>
        <aside className="detail-aside">
          <div className="aside-sticky">
            <div className="aside-label">Selected observation</div>
            <h3>
              {selected ? formatDate(selected.report_date) : "None selected"}
            </h3>
            <span className="aside-id">
              {selected?.observation_id || "Choose a checkpoint"}
            </span>
            {selected && (
              <>
                <div className="aside-facts">
                  <div>
                    <span>Status</span>
                    <strong>{displayText(selected.status, "Unreported")}</strong>
                  </div>
                  <div>
                    <span>Physical progress</span>
                    <strong>
                      {selected.physical_progress_pct != null
                        ? `${selected.physical_progress_pct}%`
                        : "Unreported"}
                    </strong>
                  </div>
                  <div>
                    <span>Revised cost</span>
                    <strong>
                      {selected.revised_cost_crore != null
                        ? `${displayNumber(selected.revised_cost_crore)} cr`
                        : "Unreported"}
                    </strong>
                  </div>
                  <div>
                    <span>Delay reason</span>
                    <strong>{displayText(selected.delay_reason, "Unreported")}</strong>
                  </div>
                </div>
                <div className="aside-source">
                  <span>Source evidence</span>
                  <strong>{selected.source_report}</strong>
                  <small>
                    {selected.source_table} · page {selected.source_page} ·
                    serial {selected.source_serial_no}
                  </small>
                </div>
              </>
            )}
          </div>
        </aside>
      </div>
    </Shell>
  );
}

function ProjectsPage() {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const load = () => {
    setLoading(true);
    setError(null);
    api
      .getProjects(page)
      .then(setData)
      .catch(setError)
      .finally(() => setLoading(false));
  };
  useEffect(() => {
    api
      .getProjects(page)
      .then(setData)
      .catch(setError)
      .finally(() => setLoading(false));
  }, [page]);
  return (
    <Shell>
      <div className="page-heading compact">
        <div>
          <span className="eyebrow">PROJECT DIRECTORY</span>
          <h1>Explore the project index.</h1>
          <p>
            Browse metadata, then open a project for point-in-time risk
            intelligence.
          </p>
        </div>
      </div>
      {loading ? (
        <LoadingState label="Loading project directory" />
      ) : error ? (
        <ErrorState error={error} onRetry={load} />
      ) : (
        <section className="panel table-panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">CANONICAL PROJECTS</span>
              <h2>{data?.total ?? 0} projects</h2>
              <p>Identity and reporting coverage from the backend index.</p>
            </div>
          </div>
          {data?.items?.length ? (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Project</th>
                    <th>Agency</th>
                    <th>State</th>
                    <th>Sector</th>
                    <th>Reporting window</th>
                    <th>Observations</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((item) => (
                    <tr
                      key={item.project_id}
                      onClick={() =>
                        navigate(
                          `/projects/${encodeURIComponent(item.project_id)}`,
                        )
                      }
                    >
                      <td>
                        <strong>{item.project_name}</strong>
                        <small>{item.project_code || item.project_id}</small>
                      </td>
                      <td>{item.agency || "—"}</td>
                      <td>{item.state || "—"}</td>
                      <td>{item.sector || "—"}</td>
                      <td>
                        {formatDate(item.first_report_date)} –{" "}
                        {formatDate(item.last_report_date)}
                      </td>
                      <td>{item.observation_count}</td>
                      <td>
                        <ArrowUpRight size={17} className="row-arrow" />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <EmptyState message="No projects returned by the backend." />
          )}
          <div className="table-footer">
            <span>{data?.total ?? 0} projects indexed</span>
            <Pagination
              page={data?.page || page}
              totalPages={data?.total_pages}
              onChange={setPage}
            />
          </div>
        </section>
      )}
    </Shell>
  );
}

export { PortfolioPage, ProjectsPage, DetailPage };
