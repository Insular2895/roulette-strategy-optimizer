export default function MonteCarloChart({ paths }) {
  const width = 720;
  const height = 300;
  const padding = 28;
  const flat = paths.flatMap((path) => path.points);
  const maxSpin = Math.max(...flat.map((point) => point.spin));
  const minBankroll = Math.min(...flat.map((point) => point.bankroll));
  const maxBankroll = Math.max(...flat.map((point) => point.bankroll));

  const scaleX = (spin) => padding + (spin / maxSpin) * (width - padding * 2);
  const scaleY = (bankroll) => height - padding - ((bankroll - minBankroll) / (maxBankroll - minBankroll || 1)) * (height - padding * 2);

  return (
    <section className="chart-panel" aria-label="Monte Carlo paths">
      <div>
        <p className="eyebrow">Monte Carlo</p>
        <h2>Trajectoires bankroll</h2>
      </div>
      <svg viewBox={`0 0 ${width} ${height}`} role="img">
        <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} className="axis" />
        <line x1={padding} y1={padding} x2={padding} y2={height - padding} className="axis" />
        {paths.map((path) => (
          <polyline
            key={path.id}
            className={path.average ? 'path-average' : 'path-line'}
            points={path.points.map((point) => `${scaleX(point.spin)},${scaleY(point.bankroll)}`).join(' ')}
          />
        ))}
      </svg>
    </section>
  );
}
