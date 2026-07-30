function IncidentTable({ incidents, loading }) {
  return (
    <div className="table-box">
      <h2>
        Incident Listesi
      </h2>

      {loading && (
        <p className="description">Yükleniyor...</p>
      )}

      {!loading && incidents.length === 0 && (
        <p className="description">
          Gösterilecek incident bulunamadı.
        </p>
      )}

      {!loading && incidents.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>IP</th>
              <th>Tür</th>
              <th>Score</th>
              <th>Severity</th>
            </tr>
          </thead>

          <tbody>
            {incidents.map((item) => (
              <tr key={item.ip}>
                <td>{item.ip}</td>
                <td>{item.incident_type}</td>
                <td>{item.score}</td>

                <td>
                  <span
                    className={`badge ${item.severity}`}
                  >
                    {item.severity}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default IncidentTable;
