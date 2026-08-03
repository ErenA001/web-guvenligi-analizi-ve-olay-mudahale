function IncidentTable({ incidents, loading }) {
  const sortedIncidents = [...incidents].sort(
    (first, second) => Number(second.score || 0) - Number(first.score || 0)
  );

  return (
    <section className="table-box" id="incidents" aria-labelledby="incidents-title">
      <div className="panel-heading table-heading">
        <div>
          <span className="eyebrow">DETECTION FEED</span>
          <h2 id="incidents-title">Incident Akışı</h2>
        </div>
        <div className="table-summary">
          <span className="feed-pulse" />
          {loading ? "Veri alınıyor" : `${sortedIncidents.length} kayıt`}
        </div>
      </div>

      {loading && (
        <div className="table-skeleton" aria-label="Incident verileri yükleniyor">
          {[1, 2, 3, 4].map((item) => <span key={item} />)}
        </div>
      )}

      {!loading && sortedIncidents.length === 0 && (
        <div className="empty-state">
          <span className="empty-icon">✓</span>
          <h3>Gösterilecek incident bulunamadı</h3>
          <p>Yeni bir log dosyası yükleyerek analizi başlatabilirsiniz.</p>
        </div>
      )}

      {!loading && sortedIncidents.length > 0 && (
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Kaynak IP</th>
                <th>Incident türü</th>
                <th>İstek</th>
                <th>Risk skoru</th>
                <th>Severity</th>
              </tr>
            </thead>
            <tbody>
              {sortedIncidents.map((item, index) => (
                <tr key={`${item.ip}-${item.incident_type}-${index}`}>
                  <td data-label="Kaynak IP">
                    <div className="ip-cell">
                      <span className="ip-node" />
                      <code>{item.ip}</code>
                    </div>
                  </td>
                  <td data-label="Incident türü"><span className="incident-type">{item.incident_type}</span></td>
                  <td data-label="İstek">{item.request_count ?? "—"}</td>
                  <td data-label="Risk skoru">
                    <div className="score-cell">
                      <strong>{item.score ?? 0}</strong>
                      <span className="score-track"><i style={{ width: `${Math.min(Number(item.score || 0) * 2, 100)}%` }} /></span>
                    </div>
                  </td>
                  <td data-label="Severity"><span className={`badge ${String(item.severity || "LOW").toLowerCase()}`}>{item.severity}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

export default IncidentTable;
