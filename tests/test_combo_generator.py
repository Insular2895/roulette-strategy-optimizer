import unittest

from backend.src.combo_generator import generate_combos
from backend.src.evaluator import evaluate_combo


class ComboGeneratorTest(unittest.TestCase):
    def test_random_generation_respects_bankroll_and_coverage(self):
        config = {
            "bankroll": {"total": 25, "allowed_units": [1, 2, 5], "exact_spend": True},
            "objective": {"min_coverage": 0.10, "max_coverage": 0.95},
            "search": {"method": "random", "combos_to_generate": 10},
            "stake_strategy": {"max_stake_per_bet": 5, "merge_same_bets": True},
        }

        combos = generate_combos(config, seed=42)

        self.assertEqual(len(combos), 10)
        for combo in combos:
            self.assertEqual(combo["total_staked"], 25)
            metrics = evaluate_combo(combo)["metrics"]
            self.assertGreaterEqual(metrics["coverage_probability"], 0.10)
            self.assertLessEqual(metrics["coverage_probability"], 0.95)

    def test_random_generation_is_reproducible_with_seed(self):
        config = {
            "bankroll": {"total": 10, "allowed_units": [1, 2], "exact_spend": True},
            "objective": {"min_coverage": 0.0, "max_coverage": 1.0},
            "search": {"method": "random", "combos_to_generate": 3},
            "stake_strategy": {"max_stake_per_bet": 2, "merge_same_bets": True},
        }

        self.assertEqual(generate_combos(config, seed=7), generate_combos(config, seed=7))

    def test_hybrid_generation_combines_grid_and_random(self):
        config = {
            "bankroll": {"total": 15, "allowed_units": [1, 2, 3], "exact_spend": True},
            "objective": {"min_coverage": 0.0, "max_coverage": 1.0},
            "search": {"method": "hybrid", "combos_to_generate": 6},
            "stake_strategy": {"max_stake_per_bet": 3, "merge_same_bets": True},
        }

        combos = generate_combos(config, seed=11)
        combo_ids = [combo["combo_id"] for combo in combos]

        self.assertEqual(len(combos), 6)
        self.assertTrue(any(combo_id.startswith("grid_") for combo_id in combo_ids))
        self.assertTrue(any(combo_id.startswith("random_") for combo_id in combo_ids))


if __name__ == "__main__":
    unittest.main()
