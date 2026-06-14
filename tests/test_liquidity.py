import unittest

from tradingdesk import liquidity as liq


class TestLiquidity(unittest.TestCase):
    def test_spread_pct(self):
        self.assertAlmostEqual(liq.spread_pct(2.50, 2.62), 0.12 / 2.56, places=6)

    def test_gate_pass(self):
        r = liq.liquidity_gate(open_interest=4686, volume=328, bid=2.50, ask=2.62)
        self.assertTrue(r.passed)
        self.assertEqual(r.reasons, [])
        self.assertLess(r.spread_pct, 0.05)

    def test_gate_fail_oi(self):
        r = liq.liquidity_gate(open_interest=0, volume=20, bid=2.59, ask=5.00)
        self.assertFalse(r.passed)
        self.assertTrue(any("OI" in x for x in r.reasons))

    def test_gate_fail_spread(self):
        # weekend-style wide quote: 0.33/0.80 -> ~83%
        r = liq.liquidity_gate(open_interest=2607, volume=55, bid=0.33, ask=0.80)
        self.assertFalse(r.passed)
        self.assertTrue(any("spread" in x for x in r.reasons))

    def test_lotto_relaxed_spread(self):
        r = liq.liquidity_gate(2607, 55, 0.33, 0.80, max_spread_pct=0.25)
        self.assertFalse(r.passed)  # 83% still fails even relaxed


if __name__ == "__main__":
    unittest.main()
