import tempfile
import unittest

from backend.src.monte_carlo import run_monte_carlo
from backend.src.optimizer import optimize
from backend.src.visual_export import export_monte_carlo_html


class HtmlExportTest(unittest.TestCase):
    def test_exports_plotly_html_files(self):
        config = {
            "bankroll": {"total": 10, "allowed_units": [1, 2], "exact_spend": True},
            "objective": {"profile": "balanced", "min_coverage": 0.0, "max_coverage": 1.0, "big_hit_threshold": 30},
            "search": {"method": "hybrid", "combos_to_generate": 6, "keep_top_n": 2},
            "stake_strategy": {"max_stake_per_bet": 2, "merge_same_bets": True},
            "profiles": {
                "balanced": {
                    "coverage_weight": 0.35,
                    "profit_probability_weight": 0.20,
                    "avg_win_weight": 0.20,
                    "big_hit_weight": 0.15,
                    "max_profit_weight": 0.10,
                    "risk_weight": 0.10,
                }
            },
        }
        strategies = optimize(config, seed=3)
        simulation = run_monte_carlo(strategies, sessions=3, spins_per_session=4, initial_bankroll=50, seed=5)

        with tempfile.TemporaryDirectory() as temp_dir:
            paths = export_monte_carlo_html(simulation, temp_dir, max_paths=10)

            for path in paths.values():
                content = path.read_text(encoding="utf-8")
                self.assertIn("Plotly.newPlot", content)
                self.assertIn("plotly-2.32.0.min.js", content)


if __name__ == "__main__":
    unittest.main()
