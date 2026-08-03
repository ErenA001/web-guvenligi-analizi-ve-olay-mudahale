import { useCallback, useEffect, useMemo, useState } from "react";

import Sidebar from "./components/Sidebar";
import Header from "./components/Header";
import SeverityCards from "./components/SeverityCards";
import IncidentTable from "./components/IncidentTable";
import LogUpload from "./components/LogUpload";
import ChatBox from "./components/ChatBox";

import "./App.css";

const EMPTY_COUNTS = {
  LOW: 0,
  MEDIUM: 0,
  HIGH: 0,
  CRITICAL: 0,
};

function NetworkBackground() {
  return (
    <div className="network-background" aria-hidden="true">
      <div className="network-grid" />
      <div className="ambient ambient-one" />
      <div className="ambient ambient-two" />
      <div className="ambient ambient-three" />

      <svg
        className="network-map"
        viewBox="0 0 1600 900"
        preserveAspectRatio="xMidYMid slice"
      >
        <defs>
          <linearGradient id="networkStroke" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="rgba(31, 214, 255, 0.08)" />
            <stop offset="50%" stopColor="rgba(86, 118, 255, 0.38)" />
            <stop offset="100%" stopColor="rgba(111, 255, 209, 0.08)" />
          </linearGradient>
          <filter id="nodeGlow">
            <feGaussianBlur stdDeviation="4" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        <g className="network-lines" fill="none" stroke="url(#networkStroke)">
          <path d="M80 210 L260 120 L430 235 L630 125 L820 245 L1040 130 L1250 230 L1510 105" />
          <path d="M25 620 L230 500 L410 640 L625 470 L850 630 L1065 475 L1290 620 L1575 465" />
          <path d="M260 120 L230 500 M430 235 L410 640 M630 125 L625 470 M820 245 L850 630 M1040 130 L1065 475 M1250 230 L1290 620" />
          <path d="M80 210 L230 500 M430 235 L625 470 M820 245 L1065 475 M1250 230 L1575 465" />
          <path d="M260 120 L410 640 M630 125 L850 630 M1040 130 L1290 620" />
        </g>

        <g className="network-packets">
          <circle r="4"><animateMotion dur="9s" repeatCount="indefinite" path="M80 210 L260 120 L430 235 L630 125 L820 245 L1040 130 L1250 230 L1510 105" /></circle>
          <circle r="3"><animateMotion dur="12s" begin="-4s" repeatCount="indefinite" path="M25 620 L230 500 L410 640 L625 470 L850 630 L1065 475 L1290 620 L1575 465" /></circle>
          <circle r="3"><animateMotion dur="8s" begin="-2s" repeatCount="indefinite" path="M260 120 L230 500 L410 640 L625 470 L820 245" /></circle>
        </g>

        <g className="network-nodes" filter="url(#nodeGlow)">
          {[80, 260, 430, 630, 820, 1040, 1250, 1510].map((x, index) => (
            <circle key={`top-${x}`} cx={x} cy={[210, 120, 235, 125, 245, 130, 230, 105][index]} r="5" />
          ))}
          {[25, 230, 410, 625, 850, 1065, 1290, 1575].map((x, index) => (
            <circle key={`bottom-${x}`} cx={x} cy={[620, 500, 640, 470, 630, 475, 620, 465][index]} r="5" />
          ))}
        </g>
      </svg>
    </div>
  );
}

function SystemOverview({ incidents, activeLogName, loading }) {
  const overview = useMemo(() => {
    const totalRequests = incidents.reduce(
      (sum, item) => sum + Number(item.request_count || 0),
      0
    );
    const suspicious = incidents.filter(
      (item) => item.incident_type && item.incident_type !== "NORMAL"
    ).length;
    const topRisk = incidents.reduce(
      (highest, item) => Math.max(highest, Number(item.score || 0)),
      0
    );

    return { totalRequests, suspicious, topRisk };
  }, [incidents]);

  return (
    <section className="panel system-overview" id="overview">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">LIVE TELEMETRY</span>
          <h2>Network Görünümü</h2>
        </div>
        <span className="panel-live"><i /> CANLI</span>
      </div>

      <div className="telemetry-grid">
        <div className="telemetry-item">
          <span>Toplam istek</span>
          <strong>{loading ? "—" : overview.totalRequests.toLocaleString("tr-TR")}</strong>
        </div>
        <div className="telemetry-item">
          <span>İzlenen IP</span>
          <strong>{loading ? "—" : incidents.length}</strong>
        </div>
        <div className="telemetry-item">
          <span>Şüpheli kaynak</span>
          <strong>{loading ? "—" : overview.suspicious}</strong>
        </div>
        <div className="telemetry-item">
          <span>Tepe risk skoru</span>
          <strong>{loading ? "—" : overview.topRisk}</strong>
        </div>
      </div>

      <div className="active-log-row">
        <span className="terminal-prompt">$</span>
        <span>active_log</span>
        <code>{activeLogName || "logs/sample_access.log"}</code>
      </div>
    </section>
  );
}

function App() {
  const [dashboardData, setDashboardData] = useState([]);
  const [severityCounts, setSeverityCounts] = useState(EMPTY_COUNTS);
  const [activeLogName, setActiveLogName] = useState("");
  const [username, setUsername] = useState("");
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");
  const [lastUpdated, setLastUpdated] = useState(null);

  const loadDashboard = useCallback(async ({ silent = false } = {}) => {
    if (!silent) {
      setLoading(true);
    }

    try {
      const response = await fetch("/api/dashboard", {
        headers: { Accept: "application/json" },
      });

      if (response.status === 401) {
        window.location.assign("/login?next=/");
        return;
      }

      if (!response.ok) {
        throw new Error(`Dashboard API ${response.status} döndürdü.`);
      }

      const result = await response.json();

      setDashboardData(Array.isArray(result.data) ? result.data : []);
      setSeverityCounts(result.severity_counts || EMPTY_COUNTS);
      setActiveLogName(result.active_log_name || "");
      setUsername(result.username || "");
      setLastUpdated(new Date());
      setErrorMessage("");
    } catch (error) {
      console.error(error);
      setErrorMessage(
        "Dashboard verisi alınamadı. Flask servisinin çalıştığını kontrol edin."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  async function handleLogout() {
    try {
      await fetch("/logout", { method: "POST" });
    } finally {
      window.location.assign("/login");
    }
  }

  useEffect(() => {
    loadDashboard();
    const refreshTimer = window.setInterval(
      () => loadDashboard({ silent: true }),
      15000
    );

    return () => window.clearInterval(refreshTimer);
  }, [loadDashboard]);

  return (
    <div className="app-shell">
      <NetworkBackground />
      <Sidebar />

      <main className="main-content">
        <Header
          activeLogName={activeLogName}
          lastUpdated={lastUpdated}
          onRefresh={() => loadDashboard()}
          onLogout={handleLogout}
          username={username}
          loading={loading}
        />

        {errorMessage && (
          <div className="alert alert-error" role="alert">
            <span className="alert-icon">!</span>
            <span>{errorMessage}</span>
            <button type="button" onClick={() => loadDashboard()}>
              Tekrar dene
            </button>
          </div>
        )}

        <section className="hero-panel" aria-labelledby="hero-title">
          <div className="hero-copy">
            <span className="eyebrow">SECURITY OPERATIONS CENTER</span>
            <h1 id="hero-title">
              Web trafiğini <span>anlık analiz et.</span>
            </h1>
            <p>
              Log kayıtlarını incident türü, severity seviyesi ve risk skoruna
              göre sınıflandıran AI destekli operasyon paneli.
            </p>
            <div className="hero-actions">
              <a className="primary-link" href="#incidents">Incidentleri incele</a>
              <a className="secondary-link" href="#log-upload">Yeni log yükle</a>
            </div>
          </div>

          <div className="hero-visual" aria-hidden="true">
            <div className="core-ring ring-one" />
            <div className="core-ring ring-two" />
            <div className="core-ring ring-three" />
            <div className="core-shield">
              <svg viewBox="0 0 24 24">
                <path d="M12 2 20 5.5v5.8c0 5.1-3.3 9.4-8 10.7-4.7-1.3-8-5.6-8-10.7V5.5L12 2Z" />
                <path d="m8.7 12 2.1 2.1 4.7-4.8" />
              </svg>
            </div>
            <span className="orbit-dot dot-one" />
            <span className="orbit-dot dot-two" />
            <span className="orbit-dot dot-three" />
          </div>
        </section>

        <SeverityCards counts={severityCounts} />

        <div className="operations-grid">
          <LogUpload onUploadSuccess={() => loadDashboard()} />
          <SystemOverview
            incidents={dashboardData}
            activeLogName={activeLogName}
            loading={loading}
          />
        </div>

        <IncidentTable incidents={dashboardData} loading={loading} />

        <footer className="site-footer">
          <div>
            <strong>Secure AI Platform</strong>
            <span>Web Security &amp; Incident Intelligence</span>
          </div>
          <div className="footer-links">
            <a href="https://jhrex.com.tr" target="_blank" rel="noreferrer">
              jhrex.com.tr
            </a>
            <a href="https://instagram.com/jhrex" target="_blank" rel="noreferrer">
              Instagram
            </a>
            <a href="https://wa.me/447441900754" target="_blank" rel="noreferrer">
              WhatsApp
            </a>
          </div>
          <p>Developed by <strong>@JhreX</strong> · © 2026</p>
        </footer>
      </main>

      <ChatBox />
    </div>
  );
}

export default App;
