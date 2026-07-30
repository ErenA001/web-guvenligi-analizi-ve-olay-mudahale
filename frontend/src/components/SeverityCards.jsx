function SeverityCards({ counts }) {
  const cards = [
    { name: "LOW", value: counts.LOW || 0 },
    { name: "MEDIUM", value: counts.MEDIUM || 0 },
    { name: "HIGH", value: counts.HIGH || 0 },
    { name: "CRITICAL", value: counts.CRITICAL || 0 },
  ];

  return (
    <div className="severity-grid">
      {cards.map((card) => (
        <div
          className={`severity-card ${card.name}`}
          key={card.name}
        >
          <h3>
            {card.name}
          </h3>

          <strong>
            {card.value}
          </strong>
        </div>
      ))}
    </div>
  );
}

export default SeverityCards;
