import unittest

from tradingdesk import execution as ex


class TestExecution(unittest.TestCase):
    def test_ref_id_unique(self):
        self.assertNotEqual(ex.gen_ref_id(), ex.gen_ref_id())

    def test_mid(self):
        self.assertAlmostEqual(ex.mid(2.50, 2.62), 2.56)

    def test_marketable_limit_buy_stays_below_ask(self):
        # mid 2.56, 40% through toward ask 2.62 -> 2.56 + 0.4*0.06 = 2.584 -> 2.58
        px = ex.marketable_limit(2.50, 2.62, "buy", max_through_spread=0.40)
        self.assertLessEqual(px, 2.62)
        self.assertGreaterEqual(px, 2.56)
        self.assertAlmostEqual(px, 2.58, places=2)

    def test_marketable_limit_never_crosses_full_spread(self):
        px = ex.marketable_limit(0.40, 0.63, "buy", max_through_spread=0.40)
        self.assertLess(px, 0.63)   # the RCAT wide-spread case: don't pay the ask

    def test_walk_caps(self):
        self.assertAlmostEqual(ex.next_walk_price(2.56, 2.50, 2.62, "buy", cap=2.60), 2.57)
        self.assertAlmostEqual(ex.next_walk_price(2.60, 2.50, 2.62, "buy", cap=2.60), 2.60)  # capped

    def test_slippage(self):
        self.assertAlmostEqual(ex.slippage_pct(2.56, 2.60), 0.015625, places=6)

    def test_classify_fill(self):
        self.assertEqual(ex.classify_fill(5, 5, "filled").state, "filled")
        self.assertEqual(ex.classify_fill(5, 2, "partially_filled").state, "partial")
        self.assertEqual(ex.classify_fill(5, 0, "confirmed").state, "open")
        self.assertEqual(ex.classify_fill(5, 0, "rejected").state, "rejected")
        self.assertEqual(ex.classify_fill(5, 2, "cancelled").remaining_qty, 3)


if __name__ == "__main__":
    unittest.main()
