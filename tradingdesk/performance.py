"""Track-record engine — verifiable performance stats from closed trades and an
equity series. This is the credibility spine (and the X-content source): feed it
the broker's order history and it produces the honest numbers, wins AND losses.
"""
from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from typing import Dict, List, Sequence

TRADING_DAYS = 252


@dataclass
class ClosedTrade:
    symbol: str
    lane: str
    pnl: float          # realized $ P&L (net)
    entry_cost: float   # capital deployed (for return %)

    @property
    def return_pct(self) -> float:
        return self.pnl / self.entry_cost if self.entry_cost else 0.0


@dataclass
class PerfStats:
    n: int
    wins: int
    losses: int
    win_rate: float
    total_pnl: float
    avg_win: float
    avg_loss: float
    profit_factor: float   # gross wins / gross losses
    expectancy: float      # mean $ P&L per trade
    largest_win: float
    largest_loss: float


def summarize(trades: Sequence[ClosedTrade]) -> PerfStats:
    """Aggregate stats over closed trades. The honest scorecard."""
    if not trades:
        return PerfStats(0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    pnls = [t.pnl for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    gross_win = sum(wins)
    gross_loss = abs(sum(losses))
    return PerfStats(
        n=len(pnls),
        wins=len(wins),
        losses=len(losses),
        win_rate=len(wins) / len(pnls),
        total_pnl=sum(pnls),
        avg_win=(gross_win / len(wins)) if wins else 0.0,
        avg_loss=(sum(losses) / len(losses)) if losses else 0.0,
        profit_factor=(gross_win / gross_loss) if gross_loss else math.inf,
        expectancy=statistics.mean(pnls),
        largest_win=max(pnls),
        largest_loss=min(pnls),
    )


def by_lane(trades: Sequence[ClosedTrade]) -> Dict[str, PerfStats]:
    """Per-lane breakdown — which sleeves actually pay (lotto judged on $ here)."""
    lanes: Dict[str, List[ClosedTrade]] = {}
    for t in trades:
        lanes.setdefault(t.lane, []).append(t)
    return {lane: summarize(ts) for lane, ts in lanes.items()}


def max_drawdown(equity_curve: Sequence[float]) -> float:
    """Largest peak-to-trough decline as a negative fraction (e.g. -0.25)."""
    if len(equity_curve) < 2:
        return 0.0
    peak = equity_curve[0]
    worst = 0.0
    for v in equity_curve:
        peak = max(peak, v)
        if peak > 0:
            worst = min(worst, v / peak - 1.0)
    return worst


def sharpe(daily_returns: Sequence[float], risk_free_daily: float = 0.0,
           trading_days: int = TRADING_DAYS) -> float:
    """Annualized Sharpe from daily returns. 0 if no variance."""
    if len(daily_returns) < 2:
        return 0.0
    excess = [r - risk_free_daily for r in daily_returns]
    sd = statistics.stdev(excess)
    if sd == 0:
        return 0.0
    return (statistics.mean(excess) / sd) * math.sqrt(trading_days)


def alpha_vs_benchmark(account_curve: Sequence[float],
                       benchmark_curve: Sequence[float]) -> float:
    """Total-return alpha: account return minus benchmark return over the window."""
    if len(account_curve) < 2 or len(benchmark_curve) < 2:
        return 0.0
    acct = account_curve[-1] / account_curve[0] - 1.0
    bench = benchmark_curve[-1] / benchmark_curve[0] - 1.0
    return acct - bench
