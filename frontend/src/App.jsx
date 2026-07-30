import { useEffect, useState } from "react";

import Sidebar from "./components/Sidebar";
import Header from "./components/Header";
import SeverityCards from "./components/SeverityCards";
import IncidentTable from "./components/IncidentTable";
import LogUpload from "./components/LogUpload";
import ChatBox from "./components/ChatBox";

import "./App.css";

function App() {
  const [dashboardData, setDashboardData] = useState([]);
  const [severityCounts, setSeverityCounts] = useState({
    LOW: 0,
    MEDIUM: 0,
    HIGH: 0,
    CRITICAL: 0,
  });
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  async function loadDashboard() {
    try {
      const response = await fetch("/api/dashboard");
      const result = await response.json();

      setDashboardData(result.data || []);
      setSeverityCounts(
        result.severity_counts || {
          LOW: 0,
          MEDIUM: 0,
          HIGH: 0,
          CRITICAL: 0,
        }
      );
      setErrorMessage("");
    } catch (error) {
      setErrorMessage(
        "Dashboard verisi alınamadı. Flask çalışıyor mu kontrol edin."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDashboard();
  }, []);

  return (
    <div className="app">

      <Sidebar />

      <main className="main-content">

        <Header />

        {errorMessage && (
          <p className="description">{errorMessage}</p>
        )}

        <SeverityCards counts={severityCounts} />

        <div className="content-grid">

          <LogUpload onUploadSuccess={loadDashboard} />

          <ChatBox />

        </div>

        <IncidentTable
          incidents={dashboardData}
          loading={loading}
        />

      </main>

    </div>
  );
}

export default App;
