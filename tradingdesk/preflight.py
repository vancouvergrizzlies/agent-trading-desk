"""Runtime self-check — deterministic assertions that run every cycle BEFORE any
order. This is NOT an LLM asking itself "is this good?" (that rationalizes
anything). It is `assert`: if the data is stale/insane, the ledger drifted, a
signal already fired, or risk limits are breached, trading HALTS — no model
involvement, no override.

The autonomous agent supplies judgment (what to research, which trade to take);
this layer refuses to let a decision become an order when reality has gone bad.
Code asserts, tests attack, statistics decide — the model never vouches for itself.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from . import recon, risk


def _is_bad_number(x) -> bool:
    return x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x)))


@dataclass
class Check:
    name: str
    ok: bool
    detail: str = ""


@dataclass
class PreflightResult:
    checks: List[Check] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(c.ok for c in self.checks)

    @property
    def halt(self) -> bool:
        return not self.passed

    def failures(self) -> List[Check]:
        return [c for c in self.checks if not c.ok]


# ---- individual deterministic checks (each pure: returns a Check) ----

def check_quote_fresh(quote_age_s: float, max_age_s: float = 60.0) -> Check:
    ok = quote_age_s is not None and quote_age_s <= max_age_s
    return Check("quote_fresh", ok, f"age {quote_age_s}s (max {max_age_s}s)")


def check_quote_sane(bid: float, ask: float, iv: Optional[float] = None,
                     delta: Optional[float] = None) -> Check:
    if _is_bad_number(bid) or _is_bad_number(ask):
        return Check("quote_sane", False, "NaN/None bid or ask")
    if bid <= 0 or ask <= 0:
        return Check("quote_sane", False, f"non-positive bid/ask {bid}/{ask}")
    if bid > ask:
        return Check("quote_sane", False, f"crossed market bid {bid} > ask {ask}")
    if iv is not None and (_is_bad_number(iv) or iv <= 0 or iv > 5.0):
        return Check("quote_sane", False, f"implausible IV {iv}")
    if delta is not None and (_is_bad_number(delta) or abs(delta) > 1.0):
        return Check("quote_sane", False, f"implausible delta {delta}")
    return Check("quote_sane", True, "")


def check_reconciled(internal: Dict[str, float], broker: Dict[str, float]) -> Check:
    drifts = recon.position_drift(internal, broker)
    if drifts:
        d = drifts[0]
        return Check("reconciled", False, f"ledger drift e.g. {d.symbol} {d.expected}!={d.actual}")
    return Check("reconciled", True, "")


def check_risk_state(*, day_pnl_pct: float = 0.0, drawdown_from_hwm_pct: float = 0.0,
                     consecutive_losses: int = 0, open_positions: int = 0,
                     max_positions: int = 8, deployed_pct: float = 0.0,
                     max_deployed_pct: float = 0.40,
                     limits: risk.RiskLimits = risk.RiskLimits()) -> Check:
    tripped, reasons = risk.kill_switch_tripped(day_pnl_pct, drawdown_from_hwm_pct,
                                                consecutive_losses, limits)
    if tripped:
        return Check("risk_state", False, "KILL SWITCH: " + "; ".join(reasons))
    if open_positions > max_positions:
        return Check("risk_state", False, f"open positions {open_positions} > {max_positions}")
    if deployed_pct > max_deployed_pct:
        return Check("risk_state", False, f"deployed {deployed_pct:.0%} > {max_deployed_pct:.0%}")
    return Check("risk_state", True, "")


def check_not_duplicate(key: str, fired_registry) -> Check:
    ok = not fired_registry.has_fired(key)
    return Check("not_duplicate", ok, f"key {key[:8]}… already fired" if not ok else "")


def check_market_open(is_open: bool) -> Check:
    return Check("market_open", bool(is_open), "" if is_open else "market closed")


def check_not_earnings_blackout(days_to_earnings: Optional[float],
                                blackout_days: int = 0) -> Check:
    if blackout_days > 0 and days_to_earnings is not None and 0 <= days_to_earnings <= blackout_days:
        return Check("earnings_blackout", False, f"{days_to_earnings:.0f}d to print ≤ {blackout_days}d")
    return Check("earnings_blackout", True, "")


def check_order_sane(limit: float, mid: float, size: float,
                     max_dev_pct: float = 0.40, max_size: float = 1e9) -> Check:
    if _is_bad_number(limit) or _is_bad_number(mid) or _is_bad_number(size):
        return Check("order_sane", False, "NaN/None in order")
    if size <= 0 or size > max_size:
        return Check("order_sane", False, f"bad size {size}")
    if mid > 0 and abs(limit - mid) / mid > max_dev_pct:
        return Check("order_sane", False, f"limit {limit} is {abs(limit-mid)/mid:.0%} off mid {mid}")
    return Check("order_sane", True, "")


def preflight(ctx: dict) -> PreflightResult:
    """Run the standard battery from a context dict. Any missing section is skipped
    (so callers can run a subset), but whatever IS provided must pass.
    """
    checks: List[Check] = []
    if "quote_age_s" in ctx:
        checks.append(check_quote_fresh(ctx["quote_age_s"], ctx.get("max_age_s", 60.0)))
    if "bid" in ctx and "ask" in ctx:
        checks.append(check_quote_sane(ctx["bid"], ctx["ask"], ctx.get("iv"), ctx.get("delta")))
    if "internal_positions" in ctx and "broker_positions" in ctx:
        checks.append(check_reconciled(ctx["internal_positions"], ctx["broker_positions"]))
    if "risk" in ctx:
        checks.append(check_risk_state(**ctx["risk"]))
    if "idempotency_key" in ctx and "fired_registry" in ctx:
        checks.append(check_not_duplicate(ctx["idempotency_key"], ctx["fired_registry"]))
    if "market_open" in ctx:
        checks.append(check_market_open(ctx["market_open"]))
    if "days_to_earnings" in ctx:
        checks.append(check_not_earnings_blackout(ctx["days_to_earnings"], ctx.get("earnings_blackout_days", 0)))
    if "order" in ctx:
        o = ctx["order"]
        checks.append(check_order_sane(o["limit"], o["mid"], o["size"],
                                       o.get("max_dev_pct", 0.40), o.get("max_size", 1e9)))
    return PreflightResult(checks)
