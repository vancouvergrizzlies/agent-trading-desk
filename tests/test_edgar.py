import unittest

from tradingdesk import edgar

# Real Form-4 fixture (BOS Better Online Solutions, CIK 1005516, a 'P' buy filed 2026-06-12)
FIXTURE = """<?xml version="1.0"?>
<ownershipDocument>
  <issuer>
    <issuerCik>0001005516</issuerCik>
    <issuerName>BOS BETTER ONLINE SOLUTIONS LTD</issuerName>
    <issuerTradingSymbol>BOSC</issuerTradingSymbol>
  </issuer>
  <reportingOwner>
    <reportingOwnerId><rptOwnerCik>0002135904</rptOwnerCik><rptOwnerName>Cohen Eyal</rptOwnerName></reportingOwnerId>
    <reportingOwnerRelationship><isDirector>1</isDirector><isOfficer>1</isOfficer><officerTitle>CEO</officerTitle></reportingOwnerRelationship>
  </reportingOwner>
  <nonDerivativeTable>
    <nonDerivativeTransaction>
      <transactionCoding><transactionCode>P</transactionCode></transactionCoding>
      <transactionAmounts>
        <transactionShares><value>1000</value></transactionShares>
        <transactionPricePerShare><value>4.29</value></transactionPricePerShare>
        <transactionAcquiredDisposedCode><value>A</value></transactionAcquiredDisposedCode>
      </transactionAmounts>
    </nonDerivativeTransaction>
  </nonDerivativeTable>
</ownershipDocument>"""

MASTER_IDX = """Description:           Daily Index
Last Data Received:    Jun 12, 2026

CIK|Company Name|Form Type|Date Filed|File Name
--------------------------------------------------------------------------------
1000230|OPTICAL CABLE CORP|4|20260612|edgar/data/1000230/0001437749-26-020486.txt
1234567|SOME BIGCO|10-K|20260612|edgar/data/1234567/0001234567-26-000001.txt
1005516|BOS BETTER ONLINE SOLUTIONS LTD|4|20260612|edgar/data/1005516/0002135904-26-000005.txt
"""


class TestEdgarParsing(unittest.TestCase):
    def test_daily_index_url(self):
        url = edgar.daily_index_url("20260612")
        self.assertIn("/2026/QTR2/master.20260612.idx", url)

    def test_parse_master_idx_filters_form4(self):
        rows = edgar.parse_master_idx(MASTER_IDX, "4")
        self.assertEqual(len(rows), 2)                       # the 10-K is excluded
        self.assertEqual(rows[0]["accession"], "0001437749-26-020486")

    def test_parse_form4_xml(self):
        f = edgar.parse_form4_xml(FIXTURE)
        self.assertEqual(f.issuer_cik, "0001005516")
        self.assertEqual(f.ticker, "BOSC")
        self.assertEqual(len(f.owners), 1)
        self.assertTrue(f.owners[0].is_officer)
        self.assertEqual(f.owners[0].title, "CEO")
        self.assertTrue(f.has_purchase())
        self.assertAlmostEqual(f.purchase_value(), 1000 * 4.29)

    def test_detect_clusters(self):
        # synthesize 3 distinct insiders buying issuer "999", 1 buying issuer "111"
        def f(issuer, owner):
            return edgar.Form4(
                issuer_cik=issuer, issuer_name="ACME " + issuer, ticker="ACME",
                owners=[edgar.Owner(cik=owner, name=owner, is_officer=(owner == "o1"))],
                txns=[edgar.Txn(code="P", shares=100, price=10.0, acquired_disposed="A")],
            )
        forms = [f("999", "o1"), f("999", "o2"), f("999", "o3"), f("111", "x1")]
        clusters = edgar.detect_clusters(forms, min_insiders=3)
        self.assertEqual(len(clusters), 1)
        self.assertEqual(clusters[0].issuer_cik, "999")
        self.assertEqual(clusters[0].distinct_buyers, 3)
        self.assertTrue(clusters[0].has_officer_buyer)

    def test_cluster_dedupes_owner(self):
        # same owner filing twice should NOT count as 2 insiders
        def f(owner):
            return edgar.Form4("999", "ACME", "ACME",
                               owners=[edgar.Owner(cik=owner, name=owner)],
                               txns=[edgar.Txn("P", 100, 10.0, "A")])
        forms = [f("o1"), f("o1"), f("o2")]
        self.assertEqual(edgar.detect_clusters(forms, min_insiders=3), [])

    def test_sales_not_a_cluster(self):
        f = edgar.Form4("999", "ACME", "ACME",
                        owners=[edgar.Owner("o1", "o1")],
                        txns=[edgar.Txn("S", 100, 10.0, "D")])
        self.assertEqual(edgar.detect_clusters([f, f, f], min_insiders=3), [])


if __name__ == "__main__":
    unittest.main()
