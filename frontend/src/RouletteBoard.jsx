import { useMemo, useState } from 'react';
import BetOverlay from './BetOverlay.jsx';
import NumberTooltip from './NumberTooltip.jsx';
import { getNumberColor } from './rouletteLayout.js';

const ROWS = Array.from({ length: 12 }, (_, index) => [3 + index * 3, 2 + index * 3, 1 + index * 3]);

export default function RouletteBoard({ strategy, outcomes }) {
  const [active, setActive] = useState(null);
  const outcomeByNumber = useMemo(() => new Map(outcomes.map((outcome) => [outcome.number, outcome])), [outcomes]);

  return (
    <section className="roulette-board-panel" aria-label="European roulette board">
      <div className="board-header">
        <div>
          <p className="eyebrow">Strategy map</p>
          <h2>Tapis roulette</h2>
        </div>
        <div className="legend">
          <span><i className="loss-heavy" /> Loss</span>
          <span><i className="profit" /> Profit</span>
          <span><i className="big-hit" /> Big hit</span>
        </div>
      </div>

      <div className="board-wrap">
        <button
          className={`number-cell zero ${toneFor(outcomeByNumber.get(0))}`}
          onMouseEnter={() => setActive(outcomeByNumber.get(0))}
          onFocus={() => setActive(outcomeByNumber.get(0))}
          onMouseLeave={() => setActive(null)}
          type="button"
        >
          0
        </button>
        <div className="number-grid">
          {ROWS.map((row) => row.map((number) => {
            const outcome = outcomeByNumber.get(number);
            return (
              <button
                key={number}
                className={`number-cell ${getNumberColor(number)} ${toneFor(outcome)}`}
                onMouseEnter={() => setActive(outcome)}
                onFocus={() => setActive(outcome)}
                onMouseLeave={() => setActive(null)}
                type="button"
              >
                <span>{number}</span>
                <small>{outcome.net_profit}</small>
              </button>
            );
          }))}
        </div>
        <BetOverlay bets={strategy.bets} />
      </div>

      <NumberTooltip outcome={active} />
    </section>
  );
}

function toneFor(outcome) {
  if (!outcome) return 'loss-light';
  if (outcome.is_big_hit) return 'hit-explosive';
  if (outcome.net_profit > 0) return 'win';
  if (outcome.net_profit < -20) return 'loss-heavy';
  return 'loss-light';
}
