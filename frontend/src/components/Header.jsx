function RefreshIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M20 11a8.1 8.1 0 0 0-15.5-2M4 4v5h5M4 13a8.1 8.1 0 0 0 15.5 2M20 20v-5h-5" />
    </svg>
  );
}

function Header({ activeLogName, lastUpdated, onRefresh, onLogout, username, loading }) {
  const timeLabel = lastUpdated
    ? lastUpdated.toLocaleTimeString("tr-TR", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      })
    : "--:--:--";

  return (
    <header className="topbar">
      <div className="mobile-brand">
        <span className="brand-mark small">S</span>
        <div>
          <strong>Secure AI</strong>
          <span>Network Monitor</span>
        </div>
      </div>

      <div className="topbar-context">
        <span className="breadcrumb">SOC / DASHBOARD</span>
        <span className="topbar-divider" />
        <span className="active-file" title={activeLogName || "Aktif log"}>
          {activeLogName || "sample_access.log"}
        </span>
      </div>

      <div className="topbar-actions">
        <div className="sync-status">
          <span className="sync-dot" />
          <div>
            <strong>Sistem çevrimiçi</strong>
            <span>Son senkronizasyon {timeLabel}</span>
          </div>
        </div>
        <div className="user-session" title="Aktif kullanıcı">
          <span>{(username || "U").slice(0, 1).toUpperCase()}</span>
          <strong>{username || "kullanıcı"}</strong>
        </div>
        <button
          className="icon-button refresh-button"
          type="button"
          onClick={onRefresh}
          disabled={loading}
          aria-label="Dashboard verilerini yenile"
          title="Yenile"
        >
          <RefreshIcon />
        </button>
        <button
          className="logout-button"
          type="button"
          onClick={onLogout}
          aria-label="Oturumu kapat"
          title="Çıkış yap"
        >
          Çıkış
        </button>
      </div>
    </header>
  );
}

export default Header;
