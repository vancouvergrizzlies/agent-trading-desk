"""Historical volatility and the IV-vs-HV value gate (journal rule #11/§11 step A).

The desk only buys premium that is cheap relative to how much the stock actually
moves: prefer implied vol <= ~1.2x historical vol.
"""
from __future__ import annotations

import math
import statistics
from typing import List, Sequence

TRADING_DAYS = 252


def log_returns(prices: Sequence[float]) -> List[float]:
    """Daily log returns from a price series (oldest -> newest)."""
    if len(prices) < 2:
        raise ValueError("need >= 2 prices")
    return [math.log(prices[i] / prices[i - 1]) for i in range(1, len(prices))]


def annualized_vol(returns: Sequence[float], trading_days: int = TRADING_DAYS) -> float:
    """Annualized volatility from a sequence of daily log returns (sample stdev)."""
    if len(returns) < 2:
        raise ValueError("need >= 2 returns")
    return statistics.stdev(returns) * math.sqrt(trading_days)


def historical_vol(prices: Sequence[float], window: int = 30,
                   trading_days: int = TRADING_DAYS) -> float:
    """Annualized historical vol over the last `window` daily returns."""
    rets = log_returns(prices)
    if window and len(rets) > window:
        rets = rets[-window:]
    return annualized_vol(rets, trading_days)


def iv_hv_ratio(implied_vol: float, hist_vol: float) -> float:
    """implied / historical. >1 means options are pricing more move than realized."""
    if hist_vol <= 0:
        raise ValueError("hist_vol must be positive")
    return implied_vol / hist_vol


def vol_gate(implied_vol: float, hist_vol: float, max_ratio: float = 1.2) -> bool:
    """True when premium is fair-or-cheap (IV/HV <= max_ratio). §11 step A."""
    return iv_hv_ratio(implied_vol, hist_vol) <= max_ratio
