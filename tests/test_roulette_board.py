import unittest

from backend.src.bet_types import generate_all_bets, generate_corners, generate_splits, get_payout, make_bet
from backend.src.roulette_board import get_color, get_column, get_dozen, get_numbers, is_even, is_high, is_low, is_odd


class RouletteBoardTest(unittest.TestCase):
    def test_european_numbers(self):
        self.assertEqual(get_numbers(), tuple(range(37)))

    def test_colors(self):
        self.assertEqual(get_color(0), "green")
        self.assertEqual(get_color(17), "black")
        self.assertEqual(get_color(18), "red")

    def test_dozen_and_column(self):
        self.assertIsNone(get_dozen(0))
        self.assertEqual(get_dozen(17), 2)
        self.assertEqual(get_column(17), 2)

    def test_even_money_helpers_exclude_zero(self):
        self.assertFalse(is_even(0))
        self.assertFalse(is_odd(0))
        self.assertTrue(is_low(18))
        self.assertTrue(is_high(19))


class BetTypesTest(unittest.TestCase):
    def test_payouts(self):
        self.assertEqual(get_payout("straight"), 35)
        self.assertEqual(get_payout("split"), 17)
        self.assertEqual(get_payout("corner"), 8)
        self.assertEqual(get_payout("even_money"), 1)

    def test_make_bet_serialization(self):
        bet = make_bet("split", (17, 20), stake=2)
        self.assertEqual(
            bet.to_dict(),
            {
                "bet_id": "split_17_20",
                "type": "split",
                "numbers": [17, 20],
                "stake": 2,
                "payout": 17,
            },
        )

    def test_legal_split_and_corner_generation(self):
        split_ids = {bet.bet_id for bet in generate_splits()}
        corner_ids = {bet.bet_id for bet in generate_corners()}
        self.assertIn("split_17_20", split_ids)
        self.assertIn("corner_16_17_19_20", corner_ids)

    def test_all_bets_are_generated(self):
        bets = generate_all_bets()
        self.assertEqual(len(bets), 154)
        self.assertEqual(len({bet.bet_id for bet in bets}), len(bets))


if __name__ == "__main__":
    unittest.main()
