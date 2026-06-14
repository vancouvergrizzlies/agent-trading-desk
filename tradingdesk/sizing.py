"""Position sizing with hard caps (journal rules #23, #28, #30).

Long options: max loss == premium paid, so sizing is just "how many contracts fit
the dollar budget" plus the portfolio caps that keep any single bet survivable.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List

CONTRACT_MULTIPLIER = 100  # shares per US equity option contract


@dataclass
class SizingResult:
    contracts: int
    premium_total: float
    pct_of_account: float
    reasons: List[str]
    ok: bool


def contracts_for_budget(premium_per_contract: float, max_dollars: float,
                         multiplier: int = CONTRACT_MULTIPLIER) -> int:
    """How many whole contracts fit under a dollar budget."""
    if premium_per_contract <= 0:
        raise ValueError("premium must be positive")
    cost_each = premium_per_contract * multiplier
    return max(0, math.floor(max_dollars / cost_each))


def size_position(account_equity: float, premium_per_contract: float,
                  sleeve_cap_dollars: float, max_account_pct: float = 0.03,
                  open_premium_dollars: float = 0.0,
                  total_premium_cap_pct: float = 0.40,
                  multiplier: int = CONTRACT_MULTIPLIER) -> SizingResult:
    """Size a long-option position against the dollar sleeve cap and portfolio caps.

    - sleeve_cap_dollars: the lane's per-trade $ cap (e.g. 300 lotto, 500 conviction)
    - max_account_pct: soft per-trade risk target; flagged (not blocked) if a single
      contract exceeds it, since contract minimums force this on small accounts
    - total_premium_cap_pct: hard cap on TOTAL open premium across the book (#28)
    """
    reasons: List[str] = []
    contracts = contracts_for_budget(premium_per_contract, sleeve_cap_dollars, multiplier)
    if contracts == 0:
        return SizingResult(0, 0.0, 0.0, ["one contract exceeds the sleeve cap"], False)

    premium_total = contracts * premium_per_contract * multiplier
    pct = premium_total / account_equity if account_equity > 0 else float("inf")

    if pct > max_account_pct:
        reasons.append(
            f"single-position risk {pct:.1%} exceeds {max_account_pct:.0%} target "
            f"(contract-minimum on a small account; sleeve-capped, sized as total loss)"
        )

    total_after = open_premium_dollars + premium_total
    cap_dollars = account_equity * total_premium_cap_pct
    ok = True
    if total_after > cap_dollars:
        reasons.append(
            f"total open premium ${total_after:.0f} would exceed "
            f"{total_premium_cap_pct:.0%} cap (${cap_dollars:.0f}) — reduce or wait"
        )
        ok = False

    return SizingResult(contracts, premium_total, pct, reasons, ok)
