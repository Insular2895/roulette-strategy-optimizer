import { WHEEL_ORDER, getNumberColor } from './rouletteLayout.js';

export default function RouletteWheel({ outcomes }) {
  const outcomeByNumber = new Map(outcomes.map((outcome) => [outcome.number, outcome]));

  return (
    <section className="wheel-panel" aria-label="Roulette wheel">
      <div>
        <p className="eyebrow">Wheel view</p>
        <h2>Roue europeenne</h2>
      </div>
      <div className="wheel">
        {WHEEL_ORDER.map((number, index) => {
          const angle = (360 / WHEEL_ORDER.length) * index;
          const outcome = outcomeByNumber.get(number);
          return (
            <span
              key={number}
              className={`wheel-number ${getNumberColor(number)} ${outcome?.is_big_hit ? 'wheel-hit' : ''}`}
              style={{ transform: `rotate(${angle}deg) translateY(-138px) rotate(${-angle}deg)` }}
              title={`${number}: ${outcome?.net_profit ?? 0}`}
            >
              {number}
            </span>
          );
        })}
        <div className="wheel-core">
          <strong>{strategyLabel(outcomes)}</strong>
          <span>max net</span>
        </div>
      </div>
    </section>
  );
}

function strategyLabel(outcomes) {
  return Math.max(...outcomes.map((outcome) => outcome.net_profit));
}
