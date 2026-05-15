import csv
import tempfile
import unittest

from backend.src.monte_carlo import run_monte_carlo
from backend.src.optimizer import optimize
from backend.src.visual_export import MONTE_CARLO_PATHS_COLUMNS, MONTE_CARLO_RESULTS_COLUMNS, export_monte_carlo


def make_config():
    return {
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


class MonteCarloTest(unittest.TestCase):
    def test_monte_carlo_generates_results_and_paths(self):
        strategies = optimize(make_config(), seed=3)
        simulation = run_monte_carlo(strategies, sessions=5, spins_per_session=10, initial_bankroll=100, seed=4)

        self.assertEqual(len(simulation["results"]), 2)
        self.assertEqual(len(simulation["paths"]), 2 * 5 * 10)
        result = simulation["results"][0]
        self.assertEqual(result["sessions"], 5)
        self.assertEqual(result["spins_per_session"], 10)
        self.assertGreaterEqual(result["probability_profit"], 0.0)
        self.assertLessEqual(result["probability_profit"], 1.0)

    def test_monte_carlo_is_reproducible_with_seed(self):
        strategies = optimize(make_config(), seed=3)

        first = run_monte_carlo(strategies, sessions=3, spins_per_session=5, initial_bankroll=50, seed=8)
        second = run_monte_carlo(strategies, sessions=3, spins_per_session=5, initial_bankroll=50, seed=8)

        self.assertEqual(first, second)

    def test_monte_carlo_exports_csv_files(self):
        strategies = optimize(make_config(), seed=3)
        simulation = run_monte_carlo(strategies, sessions=3, spins_per_session=4, initial_bankroll=50, seed=8)

        with tempfile.TemporaryDirectory() as temp_dir:
            paths = export_monte_carlo(simulation, temp_dir)

            with paths["monte_carlo_results"].open("r", encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                self.assertEqual(reader.fieldnames, MONTE_CARLO_RESULTS_COLUMNS)
                self.assertEqual(len(list(reader)), 2)

            with paths["monte_carlo_paths"].open("r", encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                self.assertEqual(reader.fieldnames, MONTE_CARLO_PATHS_COLUMNS)
                self.assertEqual(len(list(reader)), 2 * 3 * 4)


if __name__ == "__main__":
    unittest.main()
