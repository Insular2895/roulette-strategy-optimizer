export default function MonteCarloSummary({ strategy, paths }) {
  const finals = paths.filter((path) => !path.average).map((path) => path.points.at(-1).bankroll);
  const positive = finals.filter((value) => value > 100).length / finals.length;
  const avgFinal = finals.reduce((sum, value) => sum + value, 0) / finals.length;

  return (
    <section className="mc-summary" aria-label="Monte Carlo summary">
      <div>
        <p className="eyebrow">Session profile</p>
        <h2>{strategy.combo_id}</h2>
      </div>
      <div className="summary-grid">
        <Metric label="Avg final" value={avgFinal.toFixed(1)} />
        <Metric label="Positive" value={`${Math.round(positive * 100)}%`} />
        <Metric label="Sessions" value={finals.length} />
        <Metric label="Bets" value={strategy.bets.length} />
      </div>
    </section>
  );
}

function Metric({ label, value }) {
  return (
    <div className="metric compact">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
