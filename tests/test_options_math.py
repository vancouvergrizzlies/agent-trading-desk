import unittest

from tradingdesk import options_math as om


class TestOptionsMath(unittest.TestCase):
    def test_implied_move(self):
        self.assertAlmostEqual(om.implied_move_pct(3.0, 2.0, 100.0), 0.05, places=9)

    def test_payoff_multiple_at_expiry(self):
        # RCAT-style: $15 strike call, target 18, premium 0.52 wait -> use 14/18/0.57
        m = om.payoff_multiple_at_expiry(14.0, 18.0, 0.57, "call")
        self.assertAlmostEqual(m, (4.0 - 0.57) / 0.57, places=6)  # ~6.0x
        self.assertGreater(m, 5.0)

    def test_total_loss_when_otm(self):
        self.assertAlmostEqual(om.payoff_multiple_at_expiry(20, 18, 0.50, "call"), -1.0)

    def test_score_trade_beats_implied(self):
        s = om.score_trade(spot=11.18, target=18.0, strike=15.0, premium=0.52,
                           call_mid=0.9, put_mid=0.9, kind="call")
        self.assertTrue(s.beats_implied)            # 61% target move >> implied
        self.assertGreater(s.payoff_multiple, 4.0)

    def test_payoff_bs_keeps_time_value(self):
        # exiting before expiry should beat the bare-intrinsic expiry multiple
        m_bs = om.payoff_multiple_bs(15, 18, 0.52, days_to_expiry_at_exit=20,
                                     iv=1.0, kind="call")
        m_exp = om.payoff_multiple_at_expiry(15, 18, 0.52, "call")
        self.assertGreater(m_bs, m_exp)

    def test_reward_to_risk(self):
        self.assertAlmostEqual(om.reward_to_risk(900, 300), 3.0)


if __name__ == "__main__":
    unittest.main()
