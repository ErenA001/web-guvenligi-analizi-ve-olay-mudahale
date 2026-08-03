function NavIcon({ type }) {
  const paths = {
    dashboard: (
      <>
        <rect x="3" y="3" width="7" height="7" rx="2" />
        <rect x="14" y="3" width="7" height="7" rx="2" />
        <rect x="3" y="14" width="7" height="7" rx="2" />
        <rect x="14" y="14" width="7" height="7" rx="2" />
      </>
    ),
    incidents: (
      <>
        <path d="M12 3 3.8 19h16.4L12 3Z" />
        <path d="M12 9v4M12 17h.01" />
      </>
    ),
    upload: (
      <>
        <path d="M12 16V4M7 9l5-5 5 5" />
        <path d="M4 15v4a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-4" />
      </>
    ),
    assistant: (
      <>
        <path d="M9 4h6M12 2v2" />
        <rect x="4" y="6" width="16" height="13" rx="4" />
        <path d="M8 11h.01M16 11h.01M8 15c2.5 1.4 5.5 1.4 8 0" />
      </>
    ),
  };

  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      {paths[type]}
    </svg>
  );
}

function Sidebar() {
  return (
    <aside className="sidebar">
      <a className="brand" href="#top" aria-label="Secure AI ana sayfa">
        <span className="brand-mark">S</span>
        <span className="brand-copy">
          <strong>Secure AI</strong>
          <small>Network Intelligence</small>
        </span>
      </a>

      <div className="sidebar-label">OPERATIONS</div>
      <nav aria-label="Ana navigasyon">
        <a className="active" href="#top">
          <NavIcon type="dashboard" />
          <span>Dashboard</span>
        </a>
        <a href="#incidents">
          <NavIcon type="incidents" />
          <span>Incidents</span>
        </a>
        <a href="#log-upload">
          <NavIcon type="upload" />
          <span>Log Upload</span>
        </a>
        <a href="#ai-assistant">
          <NavIcon type="assistant" />
          <span>AI Assistant</span>
        </a>
      </nav>

      <div className="sidebar-spacer" />

      <div className="system-card">
        <div className="system-card-top">
          <span className="radar-icon"><i /></span>
          <div>
            <strong>System Health</strong>
            <span>All services operational</span>
          </div>
        </div>
        <div className="health-meter"><span /></div>
        <div className="health-meta">
          <span>API</span><strong>ONLINE</strong>
        </div>
      </div>

      <div className="sidebar-socials">
        <a href="https://jhrex.com.tr" target="_blank" rel="noreferrer">Web</a>
        <a href="https://instagram.com/jhrex" target="_blank" rel="noreferrer">Instagram</a>
      </div>

      <div className="sidebar-credit">
        <span>Developed by</span>
        <strong>@JhreX</strong>
      </div>
    </aside>
  );
}

export default Sidebar;
