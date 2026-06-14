import math
import unittest

from tradingdesk import volatility as vol


class TestVolatility(unittest.TestCase):
    def test_known_annualized_vol(self):
        # returns [+1%, -1%, +1%, -1%] built exactly via exp()
        rets = [0.01, -0.01, 0.01, -0.01]
        prices = [100.0]
        for r in rets:
            prices.append(prices[-1] * math.exp(r))
        hv = vol.historical_vol(prices, window=30)
        # sample stdev of returns * sqrt(252)
        self.assertAlmostEqual(hv, 0.0115470 * math.sqrt(252), delta=1e-4)

    def test_iv_hv_ratio_and_gate(self):
        self.assertAlmostEqual(vol.iv_hv_ratio(0.90, 0.90), 1.0, places=9)
        self.assertTrue(vol.vol_gate(0.90, 0.92))            # IV < HV -> cheap
        self.assertTrue(vol.vol_gate(1.10, 1.00))            # ratio 1.1 <= 1.2
        self.assertFalse(vol.vol_gate(1.50, 1.00))           # ratio 1.5 > 1.2

    def test_window_trims(self):
        prices = [100 * (1.001 ** i) for i in range(60)]
        self.assertGreater(vol.historical_vol(prices, window=30), 0)

    def test_errors(self):
        with self.assertRaises(ValueError):
            vol.log_returns([100.0])
        with self.assertRaises(ValueError):
            vol.iv_hv_ratio(0.5, 0.0)


if __name__ == "__main__":
    unittest.main()
