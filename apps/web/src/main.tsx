import React from "react";
import ReactDOM from "react-dom/client";
import {
  Activity,
  Archive,
  Database,
  Download,
  FileDown,
  Gauge,
  LockKeyhole,
  Search,
  ShieldCheck,
  UserRound,
} from "lucide-react";
import "./styles.css";

type TargetType = "username" | "email" | "domain" | "ip";
type FindingStatus = "found" | "not_found" | "unknown" | "skipped" | "error";
type View = "search" | "reports" | "sources" | "admin";

type SourceHealth = { source_id: string; status: "healthy" | "degraded" | "disabled" | "needs_key"; latency_ms?: number | null; last_checked_at: string; note: string; };

type PlanResponse = { id: string; name: string; monthly_search_limit: number; export_enabled: boolean; api_access_enabled: boolean; };

type LaunchChecklistItem = { id: string; label: string; status: "done" | "partial" | "blocked" | "todo"; owner: string; note: string; };

type Finding = {
  id: string;
  source: string;
  category: string;
  status: FindingStatus;
  confidence: number;
  title: string;
  url?: string;
  evidence: string;
  checked_at: string;
  compliance_flags: string[];
};

type SearchResponse = {
  id: string;
  target_type: TargetType;
  target: string;
  status: string;
  findings: Finding[];
  generated_at: string;
  next_actions: string[];
};

type SourceCapability = {
  id: string;
  name: string;
  category: string;
  target_types: TargetType[];
  status: "ready" | "stubbed" | "needs_api_key" | "disabled";
  terms_note: string;
  data_returned: string[];
  raw_payload_storage_allowed: boolean;
};

type EngineContract = {
  version: string;
  accepted_input: Record<string, string>;
  expected_output_fields: string[];
  prohibited_capabilities: string[];
  integration_notes: string[];
};

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

const sampleSearch: SearchResponse = {
  id: "demo-search",
  target_type: "username",
  target: "socialhunter",
  status: "completed",
  generated_at: new Date().toISOString(),
  next_actions: ["Verify high-confidence findings manually before operational use."],
  findings: [
    {
      id: "sample-1",
      source: "GitHub",
      category: "developer",
      status: "found",
      confidence: 0.86,
      title: "GitHub profile check",
      url: "https://github.com/socialhunter",
      evidence: "Demo fixture indicates a likely public profile.",
      checked_at: new Date().toISOString(),
      compliance_flags: ["public_source", "no_bypass", "no_raw_secret"],
    },
    {
      id: "sample-2",
      source: "Have I Been Pwned",
      category: "breach",
      status: "skipped",
      confidence: 0,
      title: "HIBP breach lookup not enabled",
      evidence: "Add a Vault-backed API key and terms review before enabling live breach lookup.",
      checked_at: new Date().toISOString(),
      compliance_flags: ["api_terms_required", "no_raw_secret", "no_bypass"],
    },
  ],
};

const fallbackSources: SourceCapability[] = [
  {
    id: "whatsmyname-import",
    name: "WhatsMyName Dataset Import",
    category: "username",
    target_types: ["username"],
    status: "stubbed",
    terms_note: "Use the published dataset under its project license and preserve attribution.",
    data_returned: ["source", "profile_url", "existence_signal", "confidence"],
    raw_payload_storage_allowed: false,
  },
  {
    id: "external-engine-slot",
    name: "Separate Engine Slot",
    category: "external",
    target_types: ["username", "email", "domain", "ip"],
    status: "disabled",
    terms_note: "Only attach lawful, authorized, terms-compliant engines.",
    data_returned: ["normalized_findings"],
    raw_payload_storage_allowed: false,
  },
];

function App() {
  const [view, setView] = React.useState<View>("search");
  const [targetType, setTargetType] = React.useState<TargetType>("username");
  const [target, setTarget] = React.useState("socialhunter");
  const [consent, setConsent] = React.useState(true);
  const [lastSearch, setLastSearch] = React.useState<SearchResponse>(sampleSearch);
  const [selectedId, setSelectedId] = React.useState(sampleSearch.findings[0].id);
  const [sources, setSources] = React.useState<SourceCapability[]>(fallbackSources);
  const [sourceHealth, setSourceHealth] = React.useState<SourceHealth[]>([]);
  const [plans, setPlans] = React.useState<PlanResponse[]>([]);
  const [checklist, setChecklist] = React.useState<LaunchChecklistItem[]>([]);
  const [categoryFilter, setCategoryFilter] = React.useState("all");
  const [contract, setContract] = React.useState<EngineContract | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState("");

  React.useEffect(() => {
    fetch(`${API_BASE_URL}/api/sources`).then((res) => res.json()).then(setSources).catch(() => undefined);
    fetch(`${API_BASE_URL}/api/engine-contract`).then((res) => res.json()).then(setContract).catch(() => undefined);
    fetch(`${API_BASE_URL}/api/sources/health`).then((res) => res.json()).then(setSourceHealth).catch(() => undefined);
    fetch(`${API_BASE_URL}/api/plans`).then((res) => res.json()).then(setPlans).catch(() => undefined);
    fetch(`${API_BASE_URL}/api/admin/launch-checklist`).then((res) => res.json()).then(setChecklist).catch(() => undefined);
  }, []);

  const categories = ["all", ...Array.from(new Set(lastSearch.findings.map((finding) => finding.category)))];
  const results = categoryFilter === "all" ? lastSearch.findings : lastSearch.findings.filter((finding) => finding.category === categoryFilter);
  const selected = results.find((finding) => finding.id === selectedId) ?? results[0];
  const foundCount = results.filter((finding) => finding.status === "found").length;
  const reviewCount = results.filter((finding) => finding.status === "unknown" || finding.status === "skipped").length;

  async function runSearch(event: React.FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_BASE_URL}/api/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          target_type: targetType,
          target,
          consent_confirmed: consent,
          source_groups: ["username", "breach", "ip"],
          dry_run: true,
        }),
      });

      if (!response.ok) {
        const body = await response.json().catch(() => ({ detail: "Search failed" }));
        throw new Error(body.detail ?? "Search failed");
      }

      const data = (await response.json()) as SearchResponse;
      setLastSearch(data);
      setSelectedId(data.findings[0]?.id ?? "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setLoading(false);
    }
  }

  async function exportReport(format: "json" | "csv" | "markdown") {
    const response = await fetch(`${API_BASE_URL}/api/export`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ search: lastSearch, format }),
    });
    const data = await response.json();
    const blob = new Blob([data.content], { type: data.content_type });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = data.filename;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <ShieldCheck size={24} />
          <span>Social Hunter</span>
        </div>
        <nav aria-label="Primary">
          <button className={view === "search" ? "nav-item active" : "nav-item"} onClick={() => setView("search")}><Search size={18} />Search</button>
          <button className={view === "reports" ? "nav-item active" : "nav-item"} onClick={() => setView("reports")}><Archive size={18} />Reports</button>
          <button className={view === "sources" ? "nav-item active" : "nav-item"} onClick={() => setView("sources")}><Database size={18} />Sources</button>
          <button className={view === "admin" ? "nav-item active" : "nav-item"} onClick={() => setView("admin")}><Gauge size={18} />Admin</button>
        </nav>
        <div className="policy-box">
          <strong>Education build</strong>
          <span>Public sources, approved APIs, normalized evidence.</span>
        </div>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <h1>{viewLabels[view]}</h1>
            <p>{viewSubtitles[view]}</p>
          </div>
          <div className="operator">
            <UserRound size={18} />
            <span>Analyst demo</span>
          </div>
        </header>

        {view === "search" ? (
          <>
            <section className="search-panel" id="search">
              <form onSubmit={runSearch}>
                <div className="tabs" role="tablist" aria-label="Target type">
                  {(["username", "email", "domain", "ip"] as TargetType[]).map((type) => (
                    <button type="button" key={type} className={targetType === type ? "tab active" : "tab"} onClick={() => setTargetType(type)}>
                      {type}
                    </button>
                  ))}
                </div>

                <div className="search-row">
                  <label>
                    Target
                    <input value={target} onChange={(event) => setTarget(event.target.value)} placeholder="username, email, domain, or IP" />
                  </label>
                  <button className="primary-button" type="submit" disabled={loading}>
                    <Search size={18} />
                    {loading ? "Searching" : "Run search"}
                  </button>
                </div>

                <label className="consent-row">
                  <input type="checkbox" checked={consent} onChange={(event) => setConsent(event.target.checked)} />
                  Authorized educational use confirmed
                </label>
                {error ? <div className="error-state">{error}</div> : null}
              </form>
            </section>
            <ResultsView results={results} selectedId={selectedId} selected={selected} foundCount={foundCount} reviewCount={reviewCount} setSelectedId={setSelectedId} exportReport={exportReport} categories={categories} categoryFilter={categoryFilter} setCategoryFilter={setCategoryFilter} />
          </>
        ) : null}

        {view === "reports" ? <ReportsView search={lastSearch} exportReport={exportReport} jobsEnabled /> : null}
        {view === "sources" ? <SourcesView sources={sources} health={sourceHealth} /> : null}
        {view === "admin" ? <AdminView contract={contract} sources={sources} plans={plans} checklist={checklist} /> : null}
      </section>
    </main>
  );
}

const viewLabels: Record<View, string> = {
  search: "Search workspace",
  reports: "Reports",
  sources: "Source registry",
  admin: "Admin controls",
};

const viewSubtitles: Record<View, string> = {
  search: "Run source-attributed checks and review confidence-scored findings.",
  reports: "Export normalized findings and review generated report metadata.",
  sources: "Track source readiness, data returned, and terms notes.",
  admin: "Review integration contract, safety boundaries, and launch blockers.",
};

function ResultsView(props: {
  results: Finding[];
  selectedId: string;
  selected?: Finding;
  foundCount: number;
  reviewCount: number;
  setSelectedId: (id: string) => void;
  exportReport: (format: "json" | "csv" | "markdown") => void;
  categories: string[];
  categoryFilter: string;
  setCategoryFilter: (category: string) => void;
}) {
  return (
    <section className="dashboard-grid">
      <section className="results-panel">
        <div className="metric-strip">
          <div><strong>{props.results.length}</strong><span>checks</span></div>
          <div><strong>{props.foundCount}</strong><span>found</span></div>
          <div><strong>{props.reviewCount}</strong><span>review</span></div>
        </div>
        <div className="filter-row"><span>Category</span>{props.categories.map((category) => <button key={category} className={props.categoryFilter === category ? "mini-tab active" : "mini-tab"} onClick={() => props.setCategoryFilter(category)}>{category}</button>)}</div><div className="table-wrap"><FindingsTable results={props.results} selectedId={props.selectedId} setSelectedId={props.setSelectedId} /></div>
      </section>
      <EvidencePanel selected={props.selected} exportReport={props.exportReport} />
    </section>
  );
}

function FindingsTable(props: { results: Finding[]; selectedId: string; setSelectedId: (id: string) => void }) {
  return (
    <table>
      <thead><tr><th>Source</th><th>Category</th><th>Status</th><th>Confidence</th></tr></thead>
      <tbody>
        {props.results.map((finding) => (
          <tr key={finding.id} className={finding.id === props.selectedId ? "selected" : ""} onClick={() => props.setSelectedId(finding.id)}>
            <td>{finding.source}</td><td>{finding.category}</td><td><span className={`status ${finding.status}`}>{finding.status.replace("_", " ")}</span></td><td>{Math.round(finding.confidence * 100)}%</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function EvidencePanel(props: { selected?: Finding; exportReport: (format: "json" | "csv" | "markdown") => void }) {
  if (!props.selected) return <aside className="detail-panel"><p className="empty-state">Select a finding to inspect evidence.</p></aside>;
  return (
    <aside className="detail-panel">
      <div className="detail-header"><Activity size={20} /><div><h2>{props.selected.title}</h2><p>{props.selected.source}</p></div></div>
      <div className="confidence"><span>Confidence</span><strong>{Math.round(props.selected.confidence * 100)}%</strong></div>
      <p className="evidence">{props.selected.evidence}</p>
      {props.selected.url ? <a className="source-link" href={props.selected.url} target="_blank" rel="noreferrer">Open source URL</a> : null}
      <div className="flag-list">{props.selected.compliance_flags.map((flag) => <span key={flag}>{flag.replaceAll("_", " ")}</span>)}</div>
      <div className="button-row"><button className="secondary-button" type="button" onClick={() => props.exportReport("json")}><FileDown size={18} />JSON</button><button className="secondary-button" type="button" onClick={() => props.exportReport("csv")}><Download size={18} />CSV</button><button className="secondary-button" type="button" onClick={() => props.exportReport("markdown")}><FileDown size={18} />MD</button></div>
    </aside>
  );
}

function ReportsView(props: { search: SearchResponse; exportReport: (format: "json" | "csv" | "markdown") => void; jobsEnabled: boolean }) {
  return (
    <section className="content-panel">
      <div className="section-head"><h2>Latest report package</h2><p>Search ID {props.search.id}</p></div>
      <div className="report-grid">
        <div><strong>{props.search.target}</strong><span>target</span></div>
        <div><strong>{props.search.findings.length}</strong><span>findings</span></div>
        <div><strong>{new Date(props.search.generated_at).toLocaleString()}</strong><span>generated</span></div>
      </div>
      <div className="button-row left"><button className="primary-button" onClick={() => props.exportReport("json")}><FileDown size={18} />Export JSON</button><button className="secondary-button compact" onClick={() => props.exportReport("csv")}><Download size={18} />Export CSV</button><button className="secondary-button compact" onClick={() => props.exportReport("markdown")}><FileDown size={18} />Export Markdown</button></div>
    </section>
  );
}

function SourcesView(props: { sources: SourceCapability[]; health: SourceHealth[] }) {
  return (
    <section className="content-panel">
      <div className="source-list">
        {props.sources.map((source) => (
          <article className="source-card" key={source.id}>
            <div><h2>{source.name}</h2><p>{source.terms_note}</p></div>
            <span className={`status ${source.status}`}>{source.status.replaceAll("_", " ")}</span>
            <dl><dt>Targets</dt><dd>{source.target_types.join(", ")}</dd><dt>Returns</dt><dd>{source.data_returned.join(", ")}</dd><dt>Health</dt><dd>{props.health.find((item) => item.source_id === source.id)?.note ?? "Health loads from API."}</dd></dl>
          </article>
        ))}
      </div>
    </section>
  );
}

function AdminView(props: { contract: EngineContract | null; sources: SourceCapability[]; plans: PlanResponse[]; checklist: LaunchChecklistItem[] }) {
  return (
    <section className="admin-grid">
      <article className="content-panel">
        <div className="section-head"><h2>Launch blockers</h2><p>Items to finish before production.</p></div>
        <ul className="check-list">{(props.checklist.length ? props.checklist : []).map((item) => <li key={item.id}><strong>{item.label}</strong> - {item.status}: {item.note}</li>)}</ul>
      </article>
      <article className="content-panel">
        <div className="section-head"><h2>Engine contract</h2><p>Version {props.contract?.version ?? "offline"}</p></div>
        <div className="contract-box"><LockKeyhole size={18} /><span>{props.contract?.prohibited_capabilities.join("; ") ?? "Contract loads from the API when available."}</span></div>
      </article>
      <article className="content-panel wide">
        <div className="section-head"><h2>Source readiness</h2><p>{props.sources.length} configured slots.</p></div>
        <div className="readiness-row">{props.sources.map((source) => <span className={`status ${source.status}`} key={source.id}>{source.name}: {source.status.replaceAll("_", " ")}</span>)}</div><div className="plan-grid">{props.plans.map((plan) => <div key={plan.id}><strong>{plan.name}</strong><span>{plan.monthly_search_limit.toLocaleString()} searches/mo</span></div>)}</div>
      </article>
    </section>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(<App />);


