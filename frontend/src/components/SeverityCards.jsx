const CARD_CONFIG = {
  LOW: {
    label: "Low",
    description: "Düşük öncelikli kayıt",
    icon: "check",
  },
  MEDIUM: {
    label: "Medium",
    description: "İzleme gerektiren kayıt",
    icon: "pulse",
  },
  HIGH: {
    label: "High",
    description: "Yüksek riskli aktivite",
    icon: "warning",
  },
  CRITICAL: {
    label: "Critical",
    description: "Acil inceleme gereken kayıt",
    icon: "shield",
  },
};

function CardIcon({ type }) {
  const content = {
    check: <path d="m5 12 4 4L19 6" />,
    pulse: <path d="M3 12h4l2-6 4 12 2-6h6" />,
    warning: <><path d="M12 3 3.8 19h16.4L12 3Z" /><path d="M12 9v4M12 17h.01" /></>,
    shield: <><path d="M12 2 20 5.5v5.8c0 5.1-3.3 9.4-8 10.7-4.7-1.3-8-5.6-8-10.7V5.5L12 2Z" /><path d="M12 8v5M12 17h.01" /></>,
  };

  return <svg viewBox="0 0 24 24" aria-hidden="true">{content[type]}</svg>;
}

function SeverityCards({ counts }) {
  const total = Object.values(counts || {}).reduce(
    (sum, value) => sum + Number(value || 0),
    0
  );

  return (
    <section className="severity-section" aria-labelledby="severity-title">
      <div className="section-heading">
        <div>
          <span className="eyebrow">RISK DISTRIBUTION</span>
          <h2 id="severity-title">Severity Özeti</h2>
        </div>
        <span className="section-meta">{total} IP kaydı değerlendirildi</span>
      </div>

      <div className="severity-grid">
        {Object.entries(CARD_CONFIG).map(([name, config]) => {
          const value = Number(counts?.[name] || 0);
          const percentage = total ? Math.round((value / total) * 100) : 0;

          return (
            <article className={`severity-card ${name.toLowerCase()}`} key={name}>
              <div className="severity-glow" />
              <div className="severity-card-top">
                <span className="severity-icon"><CardIcon type={config.icon} /></span>
                <span className="severity-code">{name}</span>
              </div>
              <div className="severity-value-row">
                <strong>{value}</strong>
                <span>{percentage}%</span>
              </div>
              <h3>{config.label} Severity</h3>
              <p>{config.description}</p>
              <div className="severity-progress" aria-hidden="true">
                <span style={{ width: `${Math.max(percentage, value ? 8 : 0)}%` }} />
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}

export default SeverityCards;
