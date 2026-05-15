import unittest

from backend.src.optimizer import optimize


class OptimizerTest(unittest.TestCase):
    def test_optimizer_keeps_top_n_ranked_results(self):
        config = {
            "bankroll": {"total": 20, "allowed_units": [1, 2, 5], "exact_spend": True},
            "objective": {"profile": "balanced", "min_coverage": 0.0, "max_coverage": 1.0, "big_hit_threshold": 50},
            "search": {"method": "hybrid", "combos_to_generate": 12, "keep_top_n": 5},
            "stake_strategy": {"max_stake_per_bet": 5, "merge_same_bets": True},
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

        results = optimize(config, seed=5)

        self.assertEqual(len(results), 5)
        self.assertEqual([result["rank"] for result in results], [1, 2, 3, 4, 5])
        self.assertGreaterEqual(results[0]["score"], results[-1]["score"])
        self.assertEqual(results[0]["profile"], "balanced")
        self.assertIn("risk_reward_score", results[0]["metrics"])

    def test_optimizer_requires_existing_profile(self):
        config = {
            "bankroll": {"total": 5, "allowed_units": [1], "exact_spend": True},
            "objective": {"profile": "missing", "min_coverage": 0.0, "max_coverage": 1.0},
            "search": {"method": "grid", "combos_to_generate": 1, "keep_top_n": 1},
            "stake_strategy": {"max_stake_per_bet": 1, "merge_same_bets": True},
            "profiles": {},
        }

        with self.assertRaises(ValueError):
            optimize(config)

    def test_robust_balanced_profile_uses_pareto_candidate_pool(self):
        config = {
            "bankroll": {"total": 20, "allowed_units": [1, 2, 5], "exact_spend": True},
            "objective": {"profile": "robust_balanced", "min_coverage": 0.0, "max_coverage": 1.0, "big_hit_threshold": 30},
            "search": {"method": "hybrid", "combos_to_generate": 16, "keep_top_n": 4},
            "pareto": {"enabled": True, "candidate_pool_size": 8},
            "stake_strategy": {"max_stake_per_bet": 5, "merge_same_bets": True},
            "refinement": {"enabled": False},
            "profiles": {
                "robust_balanced": {
                    "coverage_weight": 0.35,
                    "profit_probability_weight": 0.30,
                    "avg_win_weight": 0.15,
                    "big_hit_weight": 0.10,
                    "max_profit_weight": 0.05,
                    "risk_weight": 0.20,
                    "volatility_weight": 0.20,
                }
            },
        }

        results = optimize(config, seed=6)

        self.assertEqual(len(results), 8)
        self.assertEqual(results[0]["profile"], "robust_balanced")
        self.assertIn("volatility", results[0]["score_components"])


if __name__ == "__main__":
    unittest.main()
