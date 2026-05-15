import unittest

from backend.src.optimizer import optimize


class StakeRefinerTest(unittest.TestCase):
    def test_refinement_adds_optimization_ratio_and_keeps_bankroll(self):
        config = {
            "bankroll": {"total": 20, "allowed_units": [1, 2, 5], "exact_spend": True},
            "objective": {"profile": "balanced", "min_coverage": 0.0, "max_coverage": 1.0, "big_hit_threshold": 30},
            "search": {"method": "hybrid", "combos_to_generate": 12, "keep_top_n": 3},
            "stake_strategy": {"max_stake_per_bet": 5, "merge_same_bets": True},
            "refinement": {"enabled": True, "top_n": 2, "variants_per_strategy": 30, "min_stake_per_bet": 0, "max_stake_per_bet": 10},
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

        results = optimize(config, seed=12)

        self.assertEqual(len(results), 3)
        self.assertIn("optimization_ratio", results[0]["metrics"])
        self.assertEqual(results[0]["total_staked"] if "total_staked" in results[0] else results[0]["metrics"]["total_staked"], 20)
        self.assertGreaterEqual(results[0]["metrics"]["optimization_ratio"], results[-1]["metrics"]["optimization_ratio"])


if __name__ == "__main__":
    unittest.main()
