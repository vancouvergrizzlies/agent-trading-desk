"""Execution helpers: limit pricing with a slippage guard, idempotency keys, and
fill classification. Never cross a wide spread; never double-fire.

Pure functions — the actual order placement happens via the Robinhood MCP at the
call site; these compute the prices and decisions that placement should use.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass


def gen_ref_id() -> str:
    """Fresh idempotency key per logical order (#18). Reuse the SAME one on retry."""
    return str(uuid.uuid4())


def mid(bid: float, ask: float) -> float:
    return (bid + ask) / 2.0


def marketable_limit(bid: float, ask: float, side: str,
                     max_through_spread: float = 0.40, tick: float = 0.01) -> float:
    """Limit price that starts at mid and is willing to pay at most
    `max_through_spread` of the spread toward the far side. Never crosses fully.

    For a buy: mid + max_through_spread*(ask-mid). For a sell: mid - that.
    Rounded to `tick`.
    """
    m = mid(bid, ask)
    edge = (ask - m) * max_through_spread
    raw = m + edge if side == "buy" else m - edge
    return round(round(raw / tick) * tick, 4)


def next_walk_price(current: float, bid: float, ask: float, side: str,
                    cap: float, tick: float = 0.01) -> float:
    """Walk an unfilled limit one tick toward the market, never past `cap`."""
    nxt = current + tick if side == "buy" else current - tick
    if side == "buy":
        return min(nxt, cap)
    return max(nxt, cap)


def slippage_pct(intended: float, fill: float) -> float:
    """Signed fill slippage vs the intended limit, as a fraction (buy: + = worse)."""
    if intended <= 0:
        raise ValueError("intended price must be positive")
    return (fill - intended) / intended


@dataclass
class FillStatus:
    state: str          # 'filled' | 'partial' | 'open' | 'rejected' | 'cancelled'
    filled_qty: float
    remaining_qty: float


def classify_fill(quantity: float, cumulative_quantity: float, state: str) -> FillStatus:
    """Normalize a broker order response into a fill status the loop can branch on."""
    remaining = max(0.0, quantity - cumulative_quantity)
    if state in ("rejected", "failed"):
        return FillStatus("rejected", cumulative_quantity, remaining)
    if state in ("cancelled", "canceled"):
        return FillStatus("cancelled", cumulative_quantity, remaining)
    if cumulative_quantity >= quantity and quantity > 0:
        return FillStatus("filled", cumulative_quantity, 0.0)
    if cumulative_quantity > 0:
        return FillStatus("partial", cumulative_quantity, remaining)
    return FillStatus("open", 0.0, remaining)
