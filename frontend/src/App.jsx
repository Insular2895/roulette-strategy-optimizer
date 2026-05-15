import RouletteBoard from './RouletteBoard.jsx';
import RouletteWheel from './RouletteWheel.jsx';
import StrategySummary from './StrategySummary.jsx';
import MonteCarloChart from './MonteCarloChart.jsx';
import MonteCarloSummary from './MonteCarloSummary.jsx';
import strategy from './data/best_combo_detail.json';
import { buildOutcomes, buildMonteCarloPaths } from './dataModel.js';

export default function App() {
  const outcomes = strategy.outcomes?.length ? strategy.outcomes : buildOutcomes(strategy);
  const paths = buildMonteCarloPaths(outcomes, strategy.metrics.total_staked);

  return (
    <main className="app-shell">
      <section className="top-strip">
        <div>
          <p className="eyebrow">European roulette analytics</p>
          <h1>Roulette Strategy Optimizer</h1>
        </div>
        <StrategySummary strategy={strategy} />
      </section>

      <section className="workspace">
        <RouletteBoard strategy={strategy} outcomes={outcomes} />
        <RouletteWheel outcomes={outcomes} />
      </section>

      <section className="analytics">
        <MonteCarloChart paths={paths} />
        <MonteCarloSummary strategy={strategy} paths={paths} />
      </section>
    </main>
  );
}
