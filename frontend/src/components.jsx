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
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "./api/client";
import { formatData, formatDate, formatNumber } from "./utils/format";

const riskOrder = ["CRITICAL", "HIGH", "MEDIUM", "LOW"];

function displayText(value, fallback = "—") {
  return formatData(value, fallback);
}

function displayNumber(value, digits = 1, suffix = "") {
  return formatNumber(value, digits, suffix);
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

function paginatedPayload(response) {
  const payload = response?.data && typeof response.data === "object" ? response.data : response;
  return {
    ...payload,
    items: Array.isArray(payload?.items) ? payload.items : [],
  };
}

const riskColors = { LOW: "#10b981", MEDIUM: "#f59e0b", HIGH: "#f97316", CRITICAL: "#ef4444" };

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

function OutcomeBadge({ label, value }) {
  const pending = value === null || value === undefined;
  return (
    <span className={`outcome-badge ${pending ? "pending" : value ? "overrun" : "held"}`}>
      {label}: {pending ? "Outcome unavailable" : value ? "Overrun confirmed" : "No overrun observed"}
    </span>
  );
}

function Sidebar() {
  const location = useLocation();
  const projectSelected = location.pathname.startsWith("/projects/");
  return (
    <aside className="sidebar">
      <Link className="brand" to="/">
        <span className="brand-mark">
          <Activity size={19} />
        </span>
        <span>INFRA<span>SIGHT</span></span>
      </Link>
      <nav className="sidebar-nav" aria-label="Primary navigation">
        <NavLink to="/" end><Activity size={15} /><span>Portfolio Intelligence</span></NavLink>
        <NavLink to="/projects"><Landmark size={15} /><span>Project Ledger</span></NavLink>
        {projectSelected && <NavLink to={location.pathname} className="docket-link"><CircleAlert size={15} /><span>Risk Docket</span></NavLink>}
      </nav>
    </aside>
  );
}

function Shell({ children }) {
  return (
    <div className="app-shell">
      <Sidebar />
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
  const [projects, setProjects] = useState([]);
  const [totalProjects, setTotalProjects] = useState(0);
  const [rawResponse, setRawResponse] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterLevel, setFilterLevel] = useState("All levels");
  const [currentPage, setCurrentPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const ITEMS_PER_PAGE = 10;

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.getPortfolioRisk(1, 100);
      console.log("PORTFOLIO API RESPONSE:", response);
      setRawResponse(response);
      const payload = paginatedPayload(response);
      if (!Array.isArray(payload?.items)) throw new Error("Items array missing from response");
      setProjects(payload.items ?? []);
      setTotalProjects(payload?.total ?? 0);
    } catch (requestError) {
      setError(requestError);
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    let active = true;
    api.getPortfolioRisk(1, 100).then((response) => {
      if (!active) return;
      console.log("PORTFOLIO API RESPONSE:", response);
      setRawResponse(response);
      const payload = paginatedPayload(response);
      if (!Array.isArray(payload?.items)) throw new Error("Items array missing from response");
      setProjects(payload.items ?? []);
      setTotalProjects(payload?.total ?? 0);
    }).catch((requestError) => {
      if (active) setError(requestError);
    }).finally(() => {
      if (active) setLoading(false);
    });
    return () => { active = false; };
  }, []);
  useEffect(() => {
    // Reset the client page whenever filtering changes.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setCurrentPage(1);
  }, [searchQuery, filterLevel]);
  const filteredProjects = projects.filter((project) =>
    (filterLevel === "All levels" || project?.risk_level === filterLevel) &&
    [project?.project_name, project?.project_code, project?.project_id].some((value) =>
      displayText(value, "").toLowerCase().includes(searchQuery.toLowerCase()),
    ),
  );
  const paginatedProjects = filteredProjects.slice(
    (currentPage - 1) * ITEMS_PER_PAGE,
    currentPage * ITEMS_PER_PAGE,
  );
  const totalPages = Math.ceil(filteredProjects.length / ITEMS_PER_PAGE);
  const earlyWarnings = projects.filter((item) => item?.early_warning === true).length;
  const critical = projects.filter((item) => item?.risk_level === "CRITICAL").length;
  const high = projects.filter((item) => item?.risk_level === "HIGH").length;
  const riskDistribution = riskOrder.slice().reverse().map((level) => ({ level, count: projects.filter((item) => item?.risk_level === level).length }));
  const topProjects = [...projects].sort((a, b) => (b?.priority_score ?? -Infinity) - (a?.priority_score ?? -Infinity)).slice(0, 5);

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
      {loading ? <LoadingState label="Loading portfolio data" /> : error ? (
        <div className="state-panel error-state"><CircleAlert size={22} /><div><strong>{error.message}</strong><pre>{JSON.stringify(rawResponse ?? error.response ?? {}, null, 2)}</pre></div><button className="icon-button" onClick={load} title="Retry"><RefreshCw size={16} /></button></div>
      ) : projects.length === 0 ? (
        <div className="state-panel">No projects found or data mapping failed. Check console.<pre>{JSON.stringify(rawResponse ?? {}, null, 2)}</pre></div>
      ) : (
        <>
          <section className="stat-grid">
            <StatCard
              label="Total portfolio"
              value={formatNumber(totalProjects, 0)}
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
            <section className="panel distribution-panel"><div className="panel-heading"><div><span className="eyebrow">CURRENT PAGE</span><h2>Portfolio risk overview</h2><p>Distribution across loaded assessments.</p></div><TrendingUp size={18} /></div><div className="donut-layout"><ResponsiveContainer width="52%" height={190}><PieChart><Pie data={riskDistribution} dataKey="count" nameKey="level" innerRadius={52} outerRadius={78} paddingAngle={3}>{riskDistribution.map((entry) => <Cell key={entry.level} fill={riskColors[entry.level] ?? "#94a3b8"} />)}</Pie></PieChart></ResponsiveContainer><div className="donut-legend">{riskDistribution.map((entry) => <div key={entry.level}><i style={{ background: riskColors[entry.level] ?? "#94a3b8" }} /><span>{entry.level}</span><strong>{entry.count}</strong></div>)}</div></div></section>
            <section className="panel priority-panel">
              <div className="panel-heading">
                <div>
                  <span className="eyebrow">BACKEND RANKING</span>
                  <h2>Highest priority signals</h2>
                </div>
                <TrendingUp size={19} />
              </div>
              {topProjects.length === 0 ? (
                <EmptyState message="No portfolio risk records returned." />
              ) : (
                <div className="priority-list">
                  {topProjects.map((item) => (
                    <Link
                      to={`/projects/${encodeURIComponent(item.project_id)}`}
                      className="priority-row"
                      key={item.project_id}
                    >
                      <span
                        className={`priority-index ${riskClass(item.risk_level)}`}
                      >
                        {String(topProjects.indexOf(item) + 1).padStart(2, "0")}
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
                    value={searchQuery}
                    onChange={(event) => setSearchQuery(event.target.value)}
                    placeholder="Search current page"
                    aria-label="Search current page"
                  />
                </label>
                <label className="select-field">
                  <SlidersHorizontal size={15} />
                  <select
                    value={filterLevel}
                    onChange={(event) => setFilterLevel(event.target.value)}
                    aria-label="Filter by risk level"
                  >
                    <option value="All levels">All levels</option>
                    {riskOrder.map((level) => (
                      <option key={level} value={level}>
                        {level}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
            </div>
            {filteredProjects.length === 0 ? (
              <EmptyState message="No projects match the current page filters." />
            ) : (
              <RiskTable items={paginatedProjects} />
            )}
            <div className="table-footer client-pagination-footer">
              <span>
                Showing {paginatedProjects.length} of {filteredProjects.length} loaded assessments · {formatNumber(totalProjects, 0)} total projects
              </span>
              <div className="client-pagination-controls">
                <button
                  className="pagination-button"
                  disabled={currentPage === 1}
                  onClick={() => setCurrentPage((page) => page - 1)}
                >
                  Previous
                </button>
                <span>Page {currentPage} of {totalPages || 1}</span>
                <button
                  className="pagination-button"
                  disabled={currentPage === totalPages || totalPages === 0}
                  onClick={() => setCurrentPage((page) => page + 1)}
                >
                  Next
                </button>
              </div>
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
  const maxShap = Math.max(
    ...(drivers ?? []).map((driver) => magnitude(driver.shap_value)),
    0,
  );

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
            title={displayText(driver.feature)}
          >
            <div className="driver-heading">
              <strong className="driver-label">{displayText(driver.label)}</strong>
              <span className="driver-direction">
                {driver.direction === "positive" || driver.direction === "increases_risk"
                  ? "Increases risk"
                  : "Decreases risk"}
              </span>
            </div>
            <div className="driver-track" aria-label={`${displayText(driver.label)} impact`}>
              <span
                className={driver.direction === "positive" || driver.direction === "increases_risk" ? "positive" : "negative"}
                style={{
                  width: maxShap ? `${(magnitude(driver.shap_value) / maxShap) * 100}%` : "0%",
                }}
              />
            </div>
            <small className="driver-value">Actual value: {displayNumber(driver.value, 3)}</small>
          </div>
        ))
      )}
    </div>
  );
}

function ObservationFacts({ observation }) {
  if (!observation) return null;
  const facts = [
    ["Original cost", formatNumber(observation.original_cost_crore, 2, " cr")],
    ["Anticipated cost", formatNumber(observation.anticipated_cost_crore, 2, " cr")],
    ["Original completion", formatDate(observation.original_completion_date)],
    ["Anticipated completion", formatDate(observation.anticipated_completion_date)],
    ["Milestones", `${formatNumber(observation.milestones_achieved, 0)} / ${formatNumber(observation.milestones_total, 0)}`],
    ["Cumulative expenditure", formatNumber(observation.cumulative_expenditure_crore, 2, " cr")],
  ];
  return <section className="panel observation-facts"><div className="panel-heading"><div><span className="eyebrow">AUDITED CHECKPOINT DATA</span><h2>Financial and schedule position</h2><p>Reported values at the selected historical observation.</p></div><CalendarDays size={19} /></div><div className="observation-fact-grid">{facts.map(([label, value]) => <div key={label}><span>{label}</span><strong>{value}</strong></div>)}</div>{displayText(observation.delay_reason) !== "—" && <div className="observation-note"><span>Delay reason</span><strong>{formatData(observation.delay_reason)}</strong></div>}</section>;
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
              <Landmark size={14} /> {formatData(project.agency)}
            </span>
            <span>
              <MapPin size={14} /> {formatData(project.state)}
            </span>
            <span>{formatData(project.sector)}</span>
          </div>
        </div>
        <div className="identity-box">
          <span>Identity confidence</span>
          <strong className="confidence-badge">
            <ShieldCheck size={14} />
            {displayText(project.identity_confidence)} confidence
          </strong>
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
                    <span>{formatData(observation.status)}</span>
                    <strong>
                      {observation.physical_progress_pct != null
                        ? `${observation.physical_progress_pct}% progress`
                        : "—"}
                    </strong>
                    <small>{observation.observation_id}</small>
                  </button>
                ))}
              </div>
            ) : (
              <EmptyState message="No observations available for this project." />
            )}
          </section>
          <ObservationFacts observation={selected} />
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
              <div className="backtest-content">
                <div className="backtest-comparison">
                  <div className="backtest-card">
                    <span>What the model said</span>
                    <strong>{formatDate(backtest.prediction_date)}</strong>
                    <div className="backtest-probability">
                      <div><span>Cost overrun</span><b>{percent(backtest.predicted?.cost_probability)}</b></div>
                      <div className="backtest-progress"><span style={{ width: probabilityWidth(backtest.predicted?.cost_probability) }} /></div>
                    </div>
                    <div className="backtest-probability">
                      <div><span>Schedule overrun</span><b>{percent(backtest.predicted?.schedule_probability)}</b></div>
                      <div className="backtest-progress"><span style={{ width: probabilityWidth(backtest.predicted?.schedule_probability) }} /></div>
                    </div>
                  </div>
                  <div className="backtest-card backtest-outcomes">
                    <span>What actually happened</span>
                    <strong>Observed future outcome</strong>
                    <OutcomeBadge label="Cost" value={backtest.actual?.cost_deterioration} />
                    <OutcomeBadge label="Schedule" value={backtest.actual?.schedule_deterioration} />
                  </div>
                </div>
                <div className="backtest-horizon">
                  <span>Horizon context</span>
                  <strong>Evaluated across the next {backtest.horizon_observations ?? 0} reports</strong>
                  {backtest.horizon_complete ? <span className="complete-badge">Complete future horizon</span> : <span className="pending-badge">Incomplete Future Horizon - Outcome Pending</span>}
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
                    <strong>{formatData(selected.status)}</strong>
                  </div>
                  <div>
                    <span>Physical progress</span>
                    <strong>
                      {selected.physical_progress_pct != null
                        ? `${selected.physical_progress_pct}%`
                        : "—"}
                    </strong>
                  </div>
                  <div>
                    <span>Revised cost</span>
                    <strong>
                      {selected.revised_cost_crore != null
                        ? `${displayNumber(selected.revised_cost_crore)} cr`
                        : "—"}
                    </strong>
                  </div>
                  <div>
                    <span>Delay reason</span>
                    <strong>{formatData(selected.delay_reason)}</strong>
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
      .then((response) => setData(paginatedPayload(response)))
      .catch(setError)
      .finally(() => setLoading(false));
  };
  useEffect(() => {
    api
      .getProjects(page)
      .then((response) => setData(paginatedPayload(response)))
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
                    <th>Project code</th>
                    <th>Project name</th>
                    <th>Agency</th>
                    <th>State</th>
                    <th>Sector</th>
                    <th>First report</th>
                    <th>Last report</th>
                    <th>Observations</th>
                    <th>Identity confidence</th>
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
                        <strong>{formatData(item.project_code)}</strong>
                        <small>{formatData(item.project_id)}</small>
                      </td>
                      <td>{formatData(item.project_name)}</td>
                      <td>{formatData(item.agency)}</td>
                      <td>{formatData(item.state)}</td>
                      <td>{formatData(item.sector)}</td>
                      <td>{formatDate(item.first_report_date)}</td>
                      <td>{formatDate(item.last_report_date)}</td>
                      <td>{formatNumber(item.observation_count, 0)}</td>
                      <td>
                        <span className="confidence-badge">
                          <ShieldCheck size={13} />
                          {displayText(item.identity_confidence)}
                        </span>
                      </td>
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
