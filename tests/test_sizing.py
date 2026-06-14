import unittest

from tradingdesk import sizing


class TestSizing(unittest.TestCase):
    def test_contracts_for_budget(self):
        self.assertEqual(sizing.contracts_for_budget(0.57, 300), 5)   # 5*57=285
        self.assertEqual(sizing.contracts_for_budget(2.56, 300), 1)   # 256
        self.assertEqual(sizing.contracts_for_budget(4.00, 300), 0)   # 1 contract=400>300

    def test_size_position_lotto(self):
        r = sizing.size_position(account_equity=4857, premium_per_contract=0.52,
                                 sleeve_cap_dollars=300)
        self.assertEqual(r.contracts, 5)
        self.assertAlmostEqual(r.premium_total, 260.0)
        self.assertTrue(r.ok)                       # under the 40% portfolio cap
        self.assertTrue(any("3%" in x or "exceeds" in x for x in r.reasons))  # flags >3%

    def test_size_position_blocked_by_total_cap(self):
        r = sizing.size_position(account_equity=5000, premium_per_contract=2.56,
                                 sleeve_cap_dollars=300, open_premium_dollars=1900)
        # 1900 + 256 = 2156 > 40% of 5000 (2000) -> blocked
        self.assertFalse(r.ok)

    def test_one_contract_over_cap(self):
        r = sizing.size_position(5000, 4.00, sleeve_cap_dollars=300)
        self.assertEqual(r.contracts, 0)
        self.assertFalse(r.ok)


if __name__ == "__main__":
    unittest.main()
