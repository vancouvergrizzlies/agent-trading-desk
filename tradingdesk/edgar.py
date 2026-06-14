"""SEC EDGAR Form-4 insider-cluster detector — the robust replacement for
scraping OpenInsider/Finviz HTML.

Pulls from SEC's official daily index + structured Form-4 XML. Parsing is pure
(unit-tested against a real fixture); only the `fetch_*` helpers touch the network.

SEC fair-access rules are mandatory: a descriptive User-Agent with contact email,
and <= 10 requests/second. Set a real contact via TradingDeskEDGAR(user_agent=...).
Specs verified against sec.gov (accessing-edgar-data) June 2026.
"""
from __future__ import annotations

import gzip
import time
import urllib.request
import zlib
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Dict, List, Optional

ARCHIVES = "https://www.sec.gov/Archives"
DAILY_INDEX = ARCHIVES + "/edgar/daily-index"
DEFAULT_UA = "AgentTradingDesk research contact@example.com"  # OVERRIDE with a real email


# ---------- data model ----------

@dataclass
class Owner:
    cik: str
    name: str
    is_officer: bool = False
    is_director: bool = False
    title: str = ""


@dataclass
class Txn:
    code: str                 # 'P' purchase, 'S' sale, 'A' grant/award
    shares: Optional[float]
    price: Optional[float]
    acquired_disposed: str    # 'A' or 'D'


@dataclass
class Form4:
    issuer_cik: str
    issuer_name: str
    ticker: str
    owners: List[Owner] = field(default_factory=list)
    txns: List[Txn] = field(default_factory=list)
    accession: str = ""

    def purchase_value(self) -> float:
        return sum((t.shares or 0) * (t.price or 0) for t in self.txns if t.code == "P")

    def has_purchase(self) -> bool:
        return any(t.code == "P" for t in self.txns)


@dataclass
class Cluster:
    issuer_cik: str
    issuer_name: str
    ticker: str
    distinct_buyers: int
    has_officer_buyer: bool
    total_purchase_value: float


# ---------- pure parsers (unit-tested) ----------

def daily_index_url(yyyymmdd: str) -> str:
    """master.idx URL for a date 'YYYYMMDD' (quarter folder derived from month)."""
    year = yyyymmdd[:4]
    month = int(yyyymmdd[4:6])
    qtr = (month - 1) // 3 + 1
    return f"{DAILY_INDEX}/{year}/QTR{qtr}/master.{yyyymmdd}.idx"


def parse_master_idx(text: str, form_type: str = "4") -> List[Dict[str, str]]:
    """Parse a master.idx into rows; keep only matching form type (exact)."""
    rows: List[Dict[str, str]] = []
    for line in text.splitlines():
        parts = line.split("|")
        if len(parts) != 5:
            continue
        cik, company, form, date_filed, path = (p.strip() for p in parts)
        if not cik.isdigit():          # skips header/separator lines
            continue
        if form != form_type:
            continue
        accession = path.rsplit("/", 1)[-1].replace(".txt", "")
        rows.append({"cik": cik, "company": company, "form": form,
                     "date": date_filed, "path": path, "accession": accession})
    return rows


def _text(el: Optional[ET.Element]) -> str:
    return el.text.strip() if el is not None and el.text else ""


def _value(parent: Optional[ET.Element], child: str) -> Optional[float]:
    """Read a <child><value>X</value></child> float, tolerating empty wrappers."""
    if parent is None:
        return None
    node = parent.find(child)
    if node is None:
        return None
    v = node.find("value")
    txt = _text(v) if v is not None else ""
    if not txt:
        return None
    try:
        return float(txt)
    except ValueError:
        return None


def parse_form4_xml(xml_str: str) -> Form4:
    """Parse a Form-4 ownershipDocument XML into a Form4 (issuer, owners, non-derivative txns)."""
    root = ET.fromstring(xml_str)
    issuer = root.find("issuer")
    f = Form4(
        issuer_cik=_text(issuer.find("issuerCik")) if issuer is not None else "",
        issuer_name=_text(issuer.find("issuerName")) if issuer is not None else "",
        ticker=_text(issuer.find("issuerTradingSymbol")) if issuer is not None else "",
    )
    for ro in root.findall("reportingOwner"):
        oid = ro.find("reportingOwnerId")
        rel = ro.find("reportingOwnerRelationship")
        f.owners.append(Owner(
            cik=_text(oid.find("rptOwnerCik")) if oid is not None else "",
            name=_text(oid.find("rptOwnerName")) if oid is not None else "",
            is_officer=(_text(rel.find("isOfficer")) == "1") if rel is not None else False,
            is_director=(_text(rel.find("isDirector")) == "1") if rel is not None else False,
            title=_text(rel.find("officerTitle")) if rel is not None else "",
        ))
    table = root.find("nonDerivativeTable")
    if table is not None:
        for t in table.findall("nonDerivativeTransaction"):
            coding = t.find("transactionCoding")
            code = _text(coding.find("transactionCode")) if coding is not None else ""
            amts = t.find("transactionAmounts")
            ad_node = amts.find("transactionAcquiredDisposedCode") if amts is not None else None
            ad = _text(ad_node.find("value")) if ad_node is not None else ""
            f.txns.append(Txn(
                code=code,
                shares=_value(amts, "transactionShares"),
                price=_value(amts, "transactionPricePerShare"),
                acquired_disposed=ad,
            ))
    return f


def detect_clusters(filings: List[Form4], min_insiders: int = 3,
                    require_officer: bool = False) -> List[Cluster]:
    """Cluster = >= min_insiders DISTINCT insiders (by CIK) with open-market
    purchases (code 'P') in the same issuer. Dedupes owners across filings.
    """
    by_issuer: Dict[str, Dict] = {}
    for f in filings:
        if not f.has_purchase():
            continue
        agg = by_issuer.setdefault(f.issuer_cik, {
            "name": f.issuer_name, "ticker": f.ticker,
            "buyers": set(), "officer": False, "value": 0.0,
        })
        agg["value"] += f.purchase_value()
        for o in f.owners:
            agg["buyers"].add(o.cik)
            if o.is_officer:
                agg["officer"] = True
    clusters = []
    for cik, a in by_issuer.items():
        if len(a["buyers"]) >= min_insiders and (not require_officer or a["officer"]):
            clusters.append(Cluster(cik, a["name"], a["ticker"],
                                    len(a["buyers"]), a["officer"], a["value"]))
    clusters.sort(key=lambda c: c.total_purchase_value, reverse=True)
    return clusters


# ---------- network (not unit-tested; integration only) ----------

class TradingDeskEDGAR:
    """Thin network client honoring SEC's UA + rate-limit rules."""

    def __init__(self, user_agent: str = DEFAULT_UA, max_rps: float = 8.0):
        self.ua = user_agent
        self._min_interval = 1.0 / max_rps
        self._last = 0.0

    def _get(self, url: str) -> bytes:
        wait = self._min_interval - (time.monotonic() - self._last)
        if wait > 0:
            time.sleep(wait)
        req = urllib.request.Request(url, headers={
            "User-Agent": self.ua,
            "Accept-Encoding": "gzip, deflate",
            "Host": "www.sec.gov",
        })
        with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310 (trusted host)
            data = resp.read()
            encoding = (resp.headers.get("Content-Encoding") or "").lower()
        self._last = time.monotonic()
        if encoding == "gzip":
            data = gzip.decompress(data)
        elif encoding == "deflate":
            data = zlib.decompress(data)
        return data

    def form4_filings_for_day(self, yyyymmdd: str) -> List[Dict[str, str]]:
        text = self._get(daily_index_url(yyyymmdd)).decode("latin-1")
        return parse_master_idx(text, "4")

    def cluster_buys(self, yyyymmdd: str, min_insiders: int = 3,
                     require_officer: bool = True, limit: Optional[int] = None) -> List[Cluster]:
        """Fetch a day's Form 4s and return cluster buys. `limit` caps filings
        parsed (each is a network call — be mindful of the 10 req/s rule).
        """
        index = self.form4_filings_for_day(yyyymmdd)
        if limit:
            index = index[:limit]
        forms: List[Form4] = []
        for row in index:
            try:
                folder = f"{ARCHIVES}/edgar/data/{int(row['cik'])}/{row['accession'].replace('-', '')}/"
                xml = self._get(folder + "primary_doc.xml").decode("utf-8", "replace")
                forms.append(parse_form4_xml(xml))
            except Exception:
                continue  # skip non-standard filenames / parse errors; don't crash the screen
        return detect_clusters(forms, min_insiders, require_officer)
