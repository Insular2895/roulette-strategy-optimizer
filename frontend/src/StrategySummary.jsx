export default function StrategySummary({ strategy }) {
  const metrics = strategy.metrics;
  return (
    <aside className="summary-strip" aria-label="Strategy summary">
      <Metric label="Rank" value={`#${strategy.rank}`} />
      <Metric label="Score" value={metrics.score ? metrics.score.toFixed(2) : strategy.score.toFixed(2)} />
      <Metric label="Coverage" value={`${Math.round(metrics.coverage_probability * 100)}%`} />
      <Metric label="Profit" value={`${Math.round(metrics.profit_probability * 100)}%`} />
      <Metric label="Max hit" value={metrics.max_profit} />
    </aside>
  );
}

function Metric({ label, value }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
