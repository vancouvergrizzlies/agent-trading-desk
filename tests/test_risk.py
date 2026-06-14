import unittest

from tradingdesk import risk


class TestRisk(unittest.TestCase):
    def base(self, **kw):
        args = dict(equity=5000, open_premium=0, new_premium=260, lane="lotto")
        args.update(kw)
        return risk.check_new_trade(**args)

    def test_clean_trade_approved(self):
        d = self.base()
        self.assertTrue(d.approved)
        self.assertEqual(d.reasons, [])

    def test_lotto_cap(self):
        self.assertFalse(self.base(new_premium=350).approved)  # > 300 lotto cap

    def test_conviction_cap_higher(self):
        self.assertTrue(self.base(lane="conviction", new_premium=450).approved)
        self.assertFalse(self.base(lane="conviction", new_premium=600).approved)

    def test_total_premium_cap(self):
        d = self.base(open_premium=1800, new_premium=300)  # 2100 > 40% of 5000
        self.assertFalse(d.approved)
        self.assertTrue(any("total open premium" in r for r in d.reasons))

    def test_theme_cap(self):
        self.assertFalse(self.base(theme_position_count=2).approved)

    def test_lotto_slots_full(self):
        self.assertFalse(self.base(lotto_position_count=3).approved)

    def test_circuit_breakers(self):
        self.assertFalse(self.base(day_pnl_pct=-0.05).approved)
        self.assertFalse(self.base(drawdown_from_hwm_pct=-0.09).approved)
        self.assertFalse(self.base(consecutive_losses=3).approved)

    def test_small_account_warning(self):
        d = self.base(new_premium=260)   # 5.2% of 5000 > 3%
        self.assertTrue(d.approved)
        self.assertTrue(d.warnings)      # flagged but allowed

    def test_earnings_blackout(self):
        # buying premium 1 day before a print, 2-day blackout -> blocked (#20)
        d = self.base(days_to_earnings=1, earnings_blackout_days=2)
        self.assertFalse(d.approved)
        self.assertTrue(any("earnings" in r for r in d.reasons))
        # post-crush entry (blackout off) is fine
        self.assertTrue(self.base(days_to_earnings=1, earnings_blackout_days=0).approved)

    def test_kill_switch_standalone(self):
        tripped, reasons = risk.kill_switch_tripped(drawdown_from_hwm_pct=-0.09)
        self.assertTrue(tripped)
        self.assertFalse(risk.kill_switch_tripped(day_pnl_pct=-0.01)[0])

    def test_gate_check_unified_door(self):
        proposed = {"premium_total": 260, "lane": "lotto"}
        state = {"equity": 5000, "open_premium": 440}
        self.assertTrue(risk.gate_check(proposed, state).approved)
        # same trade after the kill switch tripped -> blocked
        state_halt = dict(state, drawdown_from_hwm_pct=-0.09)
        self.assertFalse(risk.gate_check(proposed, state_halt).approved)

    def test_aggression_is_preserved(self):
        # the gate must APPROVE the full aggressive book: 3 lottos + conviction,
        # right up to the 40% cap — it caps ruin, not ambition.
        proposed = {"premium_total": 300, "lane": "lotto"}
        state = {"equity": 5000, "open_premium": 1600, "lotto_position_count": 2}
        d = risk.gate_check(proposed, state)  # 1900/5000 = 38% < 40%
        self.assertTrue(d.approved)


if __name__ == "__main__":
    unittest.main()
