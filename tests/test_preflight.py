"""Adversarial preflight tests: each feeds a BROKEN condition and proves trading
halts. A passing test here = a stale quote / NaN / drift / double-fire / drawdown
provably cannot produce an order. That is the real proof of quality.
"""
import math
import unittest

from tradingdesk import preflight as pf
from tradingdesk.execution import FiredKeyRegistry


def clean_ctx():
    reg = FiredKeyRegistry()
    return {
        "quote_age_s": 3, "max_age_s": 60,
        "bid": 2.50, "ask": 2.62, "iv": 0.92, "delta": 0.29,
        "internal_positions": {"RCAT": 5}, "broker_positions": {"RCAT": 5},
        "risk": {"day_pnl_pct": 0.0, "drawdown_from_hwm_pct": -0.01,
                 "open_positions": 3, "deployed_pct": 0.30},
        "idempotency_key": "abc123", "fired_registry": reg,
        "market_open": True,
        "days_to_earnings": 20, "earnings_blackout_days": 2,
        "order": {"limit": 2.58, "mid": 2.56, "size": 5},
    }


class TestPreflightHappyPath(unittest.TestCase):
    def test_clean_state_passes(self):
        r = pf.preflight(clean_ctx())
        self.assertTrue(r.passed, [f.detail for f in r.failures()])
        self.assertFalse(r.halt)


class TestPreflightAttacks(unittest.TestCase):
    """Try to break it — every one must HALT."""

    def assertHalts(self, ctx, check_name):
        r = pf.preflight(ctx)
        self.assertTrue(r.halt, f"expected halt on {check_name}")
        self.assertIn(check_name, [c.name for c in r.failures()])

    def test_stale_quote_halts(self):
        c = clean_ctx(); c["quote_age_s"] = 600
        self.assertHalts(c, "quote_fresh")

    def test_nan_greek_halts(self):
        c = clean_ctx(); c["delta"] = float("nan")
        self.assertHalts(c, "quote_sane")

    def test_crossed_market_halts(self):
        c = clean_ctx(); c["bid"], c["ask"] = 2.70, 2.60
        self.assertHalts(c, "quote_sane")

    def test_insane_iv_halts(self):
        c = clean_ctx(); c["iv"] = 12.0
        self.assertHalts(c, "quote_sane")

    def test_ledger_drift_halts(self):
        c = clean_ctx(); c["broker_positions"] = {"RCAT": 2}  # MCP says 2, we think 5
        self.assertHalts(c, "reconciled")

    def test_drawdown_kill_switch_halts(self):
        c = clean_ctx(); c["risk"]["drawdown_from_hwm_pct"] = -0.09
        self.assertHalts(c, "risk_state")

    def test_day_loss_kill_switch_halts(self):
        c = clean_ctx(); c["risk"]["day_pnl_pct"] = -0.05
        self.assertHalts(c, "risk_state")

    def test_over_deployed_halts(self):
        c = clean_ctx(); c["risk"]["deployed_pct"] = 0.55
        self.assertHalts(c, "risk_state")

    def test_duplicate_signal_halts(self):
        c = clean_ctx()
        c["fired_registry"].mark("abc123")   # this signal already fired an order
        self.assertHalts(c, "not_duplicate")

    def test_market_closed_halts(self):
        c = clean_ctx(); c["market_open"] = False
        self.assertHalts(c, "market_open")

    def test_earnings_blackout_halts(self):
        c = clean_ctx(); c["days_to_earnings"] = 1
        self.assertHalts(c, "earnings_blackout")

    def test_order_far_from_mid_halts(self):
        c = clean_ctx(); c["order"] = {"limit": 5.00, "mid": 2.56, "size": 5}
        self.assertHalts(c, "order_sane")

    def test_zero_size_halts(self):
        c = clean_ctx(); c["order"] = {"limit": 2.58, "mid": 2.56, "size": 0}
        self.assertHalts(c, "order_sane")


class TestFiredKeyRegistry(unittest.TestCase):
    def test_marks_and_detects(self):
        reg = FiredKeyRegistry()
        self.assertFalse(reg.has_fired("k1"))
        reg.mark("k1")
        self.assertTrue(reg.has_fired("k1"))

    def test_persists_to_file(self):
        import tempfile, os
        path = os.path.join(tempfile.mkdtemp(), "fired.txt")
        FiredKeyRegistry(path).mark("kX")
        self.assertTrue(FiredKeyRegistry(path).has_fired("kX"))  # survives reload


if __name__ == "__main__":
    unittest.main()
