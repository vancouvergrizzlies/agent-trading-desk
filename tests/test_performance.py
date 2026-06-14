import math
import unittest

from tradingdesk import performance as perf
from tradingdesk.performance import ClosedTrade as T


class TestPerformance(unittest.TestCase):
    def setUp(self):
        # +100, -50, +200, -30
        self.trades = [
            T("AAA", "conviction", 100.0, 500.0),
            T("BBB", "lotto", -50.0, 300.0),
            T("CCC", "conviction", 200.0, 500.0),
            T("DDD", "lotto", -30.0, 300.0),
        ]

    def test_summary(self):
        s = perf.summarize(self.trades)
        self.assertEqual(s.n, 4)
        self.assertEqual(s.wins, 2)
        self.assertEqual(s.win_rate, 0.5)
        self.assertAlmostEqual(s.total_pnl, 220.0)
        self.assertAlmostEqual(s.avg_win, 150.0)
        self.assertAlmostEqual(s.avg_loss, -40.0)
        self.assertAlmostEqual(s.profit_factor, 300.0 / 80.0)  # 3.75
        self.assertAlmostEqual(s.expectancy, 55.0)
        self.assertEqual(s.largest_win, 200.0)
        self.assertEqual(s.largest_loss, -50.0)

    def test_empty(self):
        s = perf.summarize([])
        self.assertEqual(s.n, 0)
        self.assertEqual(s.total_pnl, 0.0)

    def test_by_lane(self):
        lanes = perf.by_lane(self.trades)
        self.assertAlmostEqual(lanes["conviction"].total_pnl, 300.0)
        self.assertAlmostEqual(lanes["lotto"].total_pnl, -80.0)  # lotto judged on $

    def test_return_pct(self):
        self.assertAlmostEqual(T("X", "lotto", 600.0, 300.0).return_pct, 2.0)

    def test_max_drawdown(self):
        self.assertAlmostEqual(perf.max_drawdown([100, 120, 90, 130]), -0.25)
        self.assertAlmostEqual(perf.max_drawdown([100, 110, 121]), 0.0)

    def test_sharpe(self):
        self.assertEqual(perf.sharpe([0.01, 0.01, 0.01]), 0.0)  # no variance
        s = perf.sharpe([0.01, -0.005, 0.012, -0.002, 0.008])
        self.assertGreater(s, 0)

    def test_alpha(self):
        # account +30%, benchmark +10% -> alpha +20pts
        self.assertAlmostEqual(perf.alpha_vs_benchmark([100, 130], [100, 110]), 0.20, places=6)

    def test_profit_factor_no_losses(self):
        s = perf.summarize([T("X", "lotto", 100, 300), T("Y", "lotto", 50, 300)])
        self.assertEqual(s.profit_factor, math.inf)


if __name__ == "__main__":
    unittest.main()
