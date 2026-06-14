import unittest

from tradingdesk import recon


class TestRecon(unittest.TestCase):
    def test_under_covered_stop(self):
        # ORCL lesson: 2.354 shares, stop covers only 2
        gaps = recon.protection_gaps({"ORCL": 2.354}, {"ORCL": 2.0})
        self.assertEqual(len(gaps), 1)
        self.assertIn("under-covered", gaps[0].note)

    def test_unprotected(self):
        # SOUN lesson: held, no resting exit
        gaps = recon.protection_gaps({"SOUN": 67.0}, {})
        self.assertEqual(len(gaps), 1)
        self.assertIn("UNPROTECTED", gaps[0].note)

    def test_fully_protected_no_gap(self):
        self.assertEqual(recon.protection_gaps({"RTX": 4.0}, {"RTX": 4.0}), [])

    def test_over_covered(self):
        gaps = recon.protection_gaps({"X": 3.0}, {"X": 5.0})
        self.assertIn("over-covered", gaps[0].note)

    def test_position_drift(self):
        drifts = recon.position_drift({"AAA": 10, "BBB": 5}, {"AAA": 10, "BBB": 0})
        self.assertEqual(len(drifts), 1)
        self.assertEqual(drifts[0].symbol, "BBB")
        self.assertEqual((drifts[0].expected, drifts[0].actual), (5, 0))

    def test_no_drift(self):
        self.assertEqual(recon.position_drift({"A": 1.0}, {"A": 1.0}), [])


if __name__ == "__main__":
    unittest.main()
