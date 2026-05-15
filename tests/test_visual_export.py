import csv
import json
import tempfile
import unittest
from pathlib import Path

from backend.src.optimizer import optimize
from backend.src.visual_export import BEST_COMBOS_COLUMNS, NUMBER_OUTCOMES_COLUMNS, export_outputs


class VisualExportTest(unittest.TestCase):
    def test_exports_best_combo_files(self):
        config = {
            "bankroll": {"total": 12, "allowed_units": [1, 2, 3], "exact_spend": True},
            "objective": {"profile": "balanced", "min_coverage": 0.0, "max_coverage": 1.0, "big_hit_threshold": 40},
            "search": {"method": "hybrid", "combos_to_generate": 8, "keep_top_n": 3},
            "stake_strategy": {"max_stake_per_bet": 3, "merge_same_bets": True},
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
        results = optimize(config, seed=9)

        with tempfile.TemporaryDirectory() as temp_dir:
            paths = export_outputs(results, temp_dir)

            self.assertTrue(paths["best_combos"].exists())
            self.assertTrue(paths["best_combo_detail"].exists())
            self.assertTrue(paths["number_outcomes"].exists())

            with paths["best_combos"].open("r", encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                self.assertEqual(reader.fieldnames, BEST_COMBOS_COLUMNS)
                self.assertEqual(len(list(reader)), 3)

            detail = json.loads(paths["best_combo_detail"].read_text(encoding="utf-8"))
            self.assertEqual(detail["rank"], 1)
            self.assertIn("outcomes", detail)

            with Path(paths["number_outcomes"]).open("r", encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                self.assertEqual(reader.fieldnames, NUMBER_OUTCOMES_COLUMNS)
                self.assertEqual(len(list(reader)), 3 * 37)


if __name__ == "__main__":
    unittest.main()
