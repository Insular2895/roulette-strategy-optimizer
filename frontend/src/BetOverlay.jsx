export default function BetOverlay({ bets }) {
  return (
    <div className="bet-overlay" aria-label="Placed bets">
      {bets.slice(0, 10).map((bet, index) => (
        <span
          key={`${bet.bet_id}-${index}`}
          className={`chip chip-${index % 5}`}
          title={`${bet.stake} on ${bet.type}: ${bet.numbers.join('-')}`}
        >
          {bet.stake}
        </span>
      ))}
    </div>
  );
}
