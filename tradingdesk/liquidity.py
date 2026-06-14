"""Option liquidity gate (§11 step B). Thin chains eat the edge in the spread."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


def spread_pct(bid: float, ask: float) -> float:
    """Quoted spread as a fraction of mid. (0.33/0.80 -> ~0.83 = 83%, illiquid.)"""
    mid = (bid + ask) / 2.0
    if mid <= 0:
        raise ValueError("mid must be positive")
    return (ask - bid) / mid


@dataclass
class LiquidityResult:
    passed: bool
    spread_pct: float
    reasons: List[str] = field(default_factory=list)


def liquidity_gate(open_interest: int, volume: int, bid: float, ask: float,
                   min_oi: int = 100, min_volume: int = 1,
                   max_spread_pct: float = 0.10) -> LiquidityResult:
    """Pass only if OI, volume, and spread are all acceptable.

    max_spread_pct defaults to 10% (conviction); lotto sleeve may relax to ~0.25.
    """
    reasons: List[str] = []
    sp = spread_pct(bid, ask)
    if open_interest < min_oi:
        reasons.append(f"OI {open_interest} < {min_oi}")
    if volume < min_volume:
        reasons.append(f"volume {volume} < {min_volume}")
    if sp > max_spread_pct:
        reasons.append(f"spread {sp:.1%} > {max_spread_pct:.0%}")
    return LiquidityResult(passed=not reasons, spread_pct=sp, reasons=reasons)
