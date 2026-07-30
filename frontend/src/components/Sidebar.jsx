function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="logo">
        Secure AI
      </div>

      <nav>
        <a href="#">
          Dashboard
        </a>

        <a href="#">
          Incidents
        </a>

        <a href="#">
          AI Assistant
        </a>

        <a href="#">
          Logs
        </a>
      </nav>

      <div className="sidebar-status">
        <span className="online-dot"></span>
        Sistem aktif
      </div>
    </aside>
  );
}

export default Sidebar;
