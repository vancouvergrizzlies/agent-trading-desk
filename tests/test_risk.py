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


if __name__ == "__main__":
    unittest.main()
