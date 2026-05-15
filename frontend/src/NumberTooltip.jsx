export default function NumberTooltip({ outcome }) {
  if (!outcome) {
    return <div className="tooltip-placeholder">Survolez un numero pour voir le detail du gain net.</div>;
  }

  return (
    <div className="number-tooltip">
      <strong>Numero {outcome.number}</strong>
      <span>Gross return: {outcome.gross_return}</span>
      <span>Net profit: {outcome.net_profit}</span>
      <span>{outcome.winning_bets.length} winning bets</span>
      <p>{outcome.explanation}</p>
    </div>
  );
}
