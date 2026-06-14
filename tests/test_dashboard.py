import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "dashboard"))
import build_dashboard as bd  # noqa: E402
from tradingdesk.performance import ClosedTrade  # noqa: E402


class TestDashboard(unittest.TestCase):
    def test_build_structure(self):
        data = bd.build_dashboard_data(
            account={"equity": 5000, "day_pnl_pct": 0.01},
            positions=[{"symbol": "UUUU", "pnl_pct": 0.1}],
            closed_trades=[ClosedTrade("A", "lotto", 100, 300),
                           ClosedTrade("B", "lotto", -50, 300)],
            equity_curve=[{"date": "2026-06-06", "account": 5000, "benchmark": 5000},
                          {"date": "2026-06-10", "account": 5200, "benchmark": 5100}],
            watchlist=[{"symbol": "RCAT"}],
            decisions=[{"ts": "t", "text": "x"}],
            generated_at="now")
        self.assertEqual(data["stats"]["n"], 2)
        self.assertIn("alpha_vs_qqq", data["stats"])
        self.assertIn("max_drawdown", data["stats"])
        self.assertAlmostEqual(data["stats"]["alpha_vs_qqq"], 0.04 - 0.02, places=6)
        self.assertEqual(data["account"]["equity"], 5000)
        self.assertEqual(len(data["positions"]), 1)

    def test_empty_inputs_dont_crash(self):
        data = bd.build_dashboard_data(account={}, positions=[], closed_trades=[],
                                       equity_curve=[], watchlist=[], decisions=[],
                                       generated_at="now")
        self.assertEqual(data["stats"]["n"], 0)
        self.assertEqual(data["stats"]["max_drawdown"], 0.0)


if __name__ == "__main__":
    unittest.main()
