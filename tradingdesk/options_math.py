"""Expected move, payoff, and reward/risk math for asymmetric option trades.

The asymmetry test (§11 step 6-7): the thesis price target must imply a payoff
multiple that beats the options-implied move. This is where 100-500%+ lives.
"""
from __future__ import annotations

from dataclasses import dataclass

from . import blackscholes as bs


def implied_move_pct(call_mid: float, put_mid: float, spot: float) -> float:
    """Options-implied move to expiry from the ATM straddle, as a fraction of spot.

    e.g. ATM call 3.00 + ATM put 2.00 on a 100 stock -> 0.05 (~5% expected move).
    """
    if spot <= 0:
        raise ValueError("spot must be positive")
    return (call_mid + put_mid) / spot


def payoff_multiple_at_expiry(strike: float, target: float, premium: float,
                              kind: str = "call") -> float:
    """Return multiple if held to expiry and the stock is at `target`.

    multiple = (intrinsic - premium) / premium. -1.0 means total loss.
    """
    if premium <= 0:
        raise ValueError("premium must be positive")
    intrinsic = max(0.0, target - strike) if kind == "call" else max(0.0, strike - target)
    return (intrinsic - premium) / premium


def projected_value_bs(strike: float, target_spot: float, premium: float,
                       days_to_expiry_at_exit: float, iv: float,
                       r: float = 0.0, kind: str = "call") -> float:
    """Estimated option value (per share) if the stock reaches target_spot with
    `days_to_expiry_at_exit` still remaining, using Black-Scholes at vol `iv`.
    """
    T = max(days_to_expiry_at_exit, 0.0) / 365.0
    return bs.price(target_spot, strike, T, r, iv, kind)


def payoff_multiple_bs(strike: float, target_spot: float, premium: float,
                       days_to_expiry_at_exit: float, iv: float,
                       r: float = 0.0, kind: str = "call") -> float:
    """Return multiple for an exit BEFORE expiry (keeps residual time value)."""
    if premium <= 0:
        raise ValueError("premium must be positive")
    value = projected_value_bs(strike, target_spot, premium, days_to_expiry_at_exit,
                               iv, r, kind)
    return (value - premium) / premium


def reward_to_risk(projected_gain: float, max_loss: float) -> float:
    """Reward/risk ratio. For long options max_loss is the premium paid."""
    if max_loss <= 0:
        raise ValueError("max_loss must be positive")
    return projected_gain / max_loss


@dataclass
class TradeScore:
    implied_move_pct: float
    target_move_pct: float
    payoff_multiple: float
    beats_implied: bool   # thesis target exceeds what options are pricing in


def score_trade(spot: float, target: float, strike: float, premium: float,
                call_mid: float, put_mid: float, kind: str = "call") -> TradeScore:
    """One-shot asymmetry check used by /options-hunter."""
    im = implied_move_pct(call_mid, put_mid, spot)
    tm = abs(target - spot) / spot
    mult = payoff_multiple_at_expiry(strike, target, premium, kind)
    return TradeScore(implied_move_pct=im, target_move_pct=tm,
                      payoff_multiple=mult, beats_implied=tm > im)
