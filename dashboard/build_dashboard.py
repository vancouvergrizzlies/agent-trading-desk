"""Generate the dashboard's data.json from the desk's state + track record.

Composes on tradingdesk.performance (the same verified track-record engine) so the
public page can never show numbers that disagree with the scorecard. Pure builder
(`build_dashboard_data`) + a thin file IO main.
"""
from __future__ import annotations

import json
import os
import sys
from typing import Dict, List, Optional

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from tradingdesk import performance as perf  # noqa: E402
from tradingdesk.performance import ClosedTrade  # noqa: E402


def build_dashboard_data(*, account: Dict, positions: List[Dict],
                         closed_trades: List[ClosedTrade],
                         equity_curve: List[Dict],
                         watchlist: List[Dict], decisions: List[Dict],
                         generated_at: str) -> Dict:
    """Assemble the full dashboard payload. equity_curve rows: {date, account, benchmark}."""
    acct_series = [r["account"] for r in equity_curve]
    bench_series = [r["benchmark"] for r in equity_curve]
    stats = perf.summarize(closed_trades)
    lanes = {ln: vars(s) for ln, s in perf.by_lane(closed_trades).items()}
    return {
        "generated_at": generated_at,
        "account": account,
        "positions": positions,
        "equity_curve": equity_curve,
        "stats": {
            **vars(stats),
            "max_drawdown": perf.max_drawdown(acct_series),
            "alpha_vs_qqq": perf.alpha_vs_benchmark(acct_series, bench_series),
        },
        "by_lane": lanes,
        "watchlist": watchlist,
        "decisions": decisions[-20:],  # most recent
    }


def _load(path: str, default):
    return json.load(open(path)) if os.path.exists(path) else default


def main() -> None:
    """Read inputs from dashboard/inputs/ (gitignored, real) and write data.json.
    Falls back to the shipped example so the page renders out of the box.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    inp = os.path.join(here, "inputs")
    trades = [ClosedTrade(**t) for t in _load(os.path.join(inp, "closed_trades.json"), [])]
    data = build_dashboard_data(
        account=_load(os.path.join(inp, "account.json"), {}),
        positions=_load(os.path.join(inp, "positions.json"), []),
        closed_trades=trades,
        equity_curve=_load(os.path.join(inp, "equity_curve.json"), []),
        watchlist=_load(os.path.join(inp, "watchlist.json"), []),
        decisions=_load(os.path.join(inp, "decisions.json"), []),
        generated_at=os.environ.get("GEN_AT", "unknown"),
    )
    out = os.path.join(here, "data.json")
    if not os.path.exists(inp):  # no real inputs -> keep the example as data.json
        out = os.path.join(here, "data.generated.json")
    json.dump(data, open(out, "w"), indent=2)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
