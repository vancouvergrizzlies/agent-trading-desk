"""Code-enforced pre-trade risk gate.

The journal's risk rules (#28 caps, #29 FOMC/bear, #30 lotto, §2 circuit breakers)
as *executable* checks. The agent must call check_new_trade() and get approval
before placing — guardrails that can't be rationalized away in a prompt.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class RiskLimits:
    max_total_premium_pct: float = 0.40   # total open premium ceiling vs equity (#28)
    lotto_cap: float = 300.0              # per-trade $ cap, lotto sleeve (#30)
    conviction_cap: float = 500.0         # per-trade $ cap, conviction (#23)
    max_per_theme: int = 2               # correlation cap (#28)
    max_lotto_positions: int = 3         # lotto slots (#30)
    day_loss_halt_pct: float = -0.04     # single-day equity halt (§2)
    hwm_drawdown_halt_pct: float = -0.08  # drawdown-from-high-water halt (§2)
    consecutive_loss_halt: int = 3       # cooling-off after N straight losses (§2)


@dataclass
class RiskDecision:
    approved: bool
    reasons: List[str] = field(default_factory=list)   # why it was blocked
    warnings: List[str] = field(default_factory=list)   # allowed-but-flagged


def check_new_trade(*, equity: float, open_premium: float, new_premium: float,
                    lane: str, theme_position_count: int = 0,
                    lotto_position_count: int = 0, day_pnl_pct: float = 0.0,
                    drawdown_from_hwm_pct: float = 0.0, consecutive_losses: int = 0,
                    limits: RiskLimits = RiskLimits()) -> RiskDecision:
    """Approve or block a proposed new option position. lane in {'lotto','conviction'}.

    pnl/drawdown args are signed fractions (e.g. -0.05 = down 5%).
    """
    reasons: List[str] = []
    warnings: List[str] = []

    # --- hard circuit breakers (§2) ---
    if day_pnl_pct <= limits.day_loss_halt_pct:
        reasons.append(f"circuit breaker: day P&L {day_pnl_pct:.1%} ≤ {limits.day_loss_halt_pct:.0%}")
    if drawdown_from_hwm_pct <= limits.hwm_drawdown_halt_pct:
        reasons.append(f"circuit breaker: drawdown {drawdown_from_hwm_pct:.1%} ≤ {limits.hwm_drawdown_halt_pct:.0%} from HWM")
    if consecutive_losses >= limits.consecutive_loss_halt:
        reasons.append(f"circuit breaker: {consecutive_losses} consecutive losses ≥ {limits.consecutive_loss_halt}")

    # --- sleeve per-trade cap ---
    cap = limits.lotto_cap if lane == "lotto" else limits.conviction_cap
    if new_premium > cap:
        reasons.append(f"premium ${new_premium:.0f} exceeds {lane} cap ${cap:.0f}")

    # --- portfolio heat (#28) ---
    if equity <= 0:
        reasons.append("equity must be positive")
    elif open_premium + new_premium > equity * limits.max_total_premium_pct:
        reasons.append(
            f"total open premium ${open_premium + new_premium:.0f} exceeds "
            f"{limits.max_total_premium_pct:.0%} of equity (${equity * limits.max_total_premium_pct:.0f})"
        )

    # --- correlation cap (#28) ---
    if theme_position_count >= limits.max_per_theme:
        reasons.append(f"theme already has {theme_position_count} positions (cap {limits.max_per_theme})")

    # --- lotto slot cap (#30) ---
    if lane == "lotto" and lotto_position_count >= limits.max_lotto_positions:
        reasons.append(f"lotto slots full ({lotto_position_count}/{limits.max_lotto_positions})")

    # --- soft warning: single-trade heat ---
    if equity > 0 and new_premium > equity * 0.03:
        warnings.append(
            f"single-trade risk {new_premium / equity:.1%} > 3% (contract-minimum on a small "
            f"account; sized as total loss)"
        )

    return RiskDecision(approved=not reasons, reasons=reasons, warnings=warnings)
