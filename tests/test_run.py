import tempfile
import unittest
from pathlib import Path

from backend.src.run import main


class RunCliTest(unittest.TestCase):
    def test_cli_runs_small_pipeline(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            import sys

            previous_argv = sys.argv
            sys.argv = [
                "run.py",
                "--combos-to-generate",
                "6",
                "--keep-top-n",
                "2",
                "--monte-carlo-sessions",
                "3",
                "--spins-per-session",
                "4",
                "--initial-bankroll",
                "50",
                "--output-dir",
                temp_dir,
                "--seed",
                "7",
            ]
            try:
                self.assertEqual(main(), 0)
            finally:
                sys.argv = previous_argv

            output_path = Path(temp_dir)
            self.assertTrue((output_path / "best_combos.csv").exists())
            self.assertTrue((output_path / "best_combo_detail.json").exists())
            self.assertTrue((output_path / "roulette_board.html").exists())
            self.assertTrue((output_path / "monte_carlo_results.csv").exists())
            self.assertTrue((output_path / "monte_carlo_paths.html").exists())
            self.assertTrue((output_path / "report.html").exists())


if __name__ == "__main__":
    unittest.main()
