import math
import unittest

from tradingdesk import blackscholes as bs


class TestBlackScholes(unittest.TestCase):
    def test_norm_cdf_known_values(self):
        self.assertAlmostEqual(bs.norm_cdf(0.0), 0.5, places=10)
        self.assertAlmostEqual(bs.norm_cdf(0.1), 0.539827837, places=6)

    def test_atm_call_textbook(self):
        # S=K=100, T=1, r=0, sigma=0.2 -> ~7.9656 (classic ATM result)
        c = bs.price(100, 100, 1.0, 0.0, 0.20, "call")
        self.assertAlmostEqual(c, 7.9656, delta=0.01)

    def test_put_call_parity(self):
        S, K, T, r, sig = 100, 95, 0.5, 0.03, 0.25
        c = bs.price(S, K, T, r, sig, "call")
        p = bs.price(S, K, T, r, sig, "put")
        # C - P == S - K e^{-rT}
        self.assertAlmostEqual(c - p, S - K * math.exp(-r * T), places=8)

    def test_intrinsic_at_expiry(self):
        self.assertAlmostEqual(bs.price(120, 100, 0, 0.0, 0.2, "call"), 20.0)
        self.assertAlmostEqual(bs.price(80, 100, 0, 0.0, 0.2, "put"), 20.0)
        self.assertAlmostEqual(bs.price(80, 100, 0, 0.0, 0.2, "call"), 0.0)

    def test_atm_call_delta(self):
        g = bs.greeks(100, 100, 1.0, 0.0, 0.20, "call")
        self.assertAlmostEqual(g.delta, 0.539827837, places=4)
        self.assertGreater(g.gamma, 0)
        self.assertGreater(g.vega, 0)
        self.assertLess(g.theta, 0)

    def test_put_delta_is_call_delta_minus_one(self):
        cd = bs.greeks(100, 100, 1.0, 0.0, 0.20, "call").delta
        pd = bs.greeks(100, 100, 1.0, 0.0, 0.20, "put").delta
        self.assertAlmostEqual(pd, cd - 1.0, places=8)


if __name__ == "__main__":
    unittest.main()
