import unittest

from backend.src.evaluator import evaluate_combo


class EvaluatorTest(unittest.TestCase):
    def test_evaluates_known_stack_on_number_17(self):
        combo = {
            "combo_id": "example_17",
            "bets": [
                {"bet_id": "straight_17", "type": "straight", "numbers": [17], "stake": 3, "payout": 35},
                {"bet_id": "split_17_20", "type": "split", "numbers": [17, 20], "stake": 2, "payout": 17},
                {"bet_id": "corner_16_17_19_20", "type": "corner", "numbers": [16, 17, 19, 20], "stake": 5, "payout": 8},
                {"bet_id": "dozen_2", "type": "dozen", "numbers": list(range(13, 25)), "stake": 10, "payout": 2},
            ],
        }

        result = evaluate_combo(combo, big_hit_threshold=100)
        outcome_17 = next(outcome for outcome in result["outcomes"] if outcome["number"] == 17)

        self.assertEqual(result["metrics"]["total_staked"], 20)
        self.assertEqual(outcome_17["gross_return"], 219)
        self.assertEqual(outcome_17["net_profit"], 199)
        self.assertTrue(outcome_17["is_big_hit"])
        self.assertEqual(len(outcome_17["winning_bets"]), 4)
        self.assertIn("stacked winning bets", outcome_17["explanation"])

    def test_uncovered_number_loses_total_stake(self):
        combo = {
            "combo_id": "one_number",
            "bets": [{"type": "straight", "numbers": [17], "stake": 1}],
        }

        result = evaluate_combo(combo)
        outcome_1 = next(outcome for outcome in result["outcomes"] if outcome["number"] == 1)

        self.assertEqual(outcome_1["gross_return"], 0)
        self.assertEqual(outcome_1["net_profit"], -1)
        self.assertFalse(outcome_1["is_covered"])

    def test_expected_value_is_negative_for_one_straight_bet(self):
        combo = {
            "combo_id": "straight_17",
            "bets": [{"type": "straight", "numbers": [17], "stake": 1}],
        }

        result = evaluate_combo(combo)

        self.assertAlmostEqual(result["metrics"]["expected_value"], -1 / 37)
        self.assertEqual(result["metrics"]["coverage_probability"], 1 / 37)


if __name__ == "__main__":
    unittest.main()
