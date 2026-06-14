"""Reconciliation: catch protection gaps and position drift.

Built from the live lessons — a stop covering fewer shares than the position
(the ORCL 2-of-2.354 stub), and a time-stop that silently never fired (SOUN).
The desk must assert reality matches intent every session.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class ProtectionGap:
    symbol: str
    position_qty: float
    protected_qty: float
    note: str


def protection_gaps(positions: Dict[str, float],
                    protective_qty: Dict[str, float],
                    tolerance: float = 1e-6) -> List[ProtectionGap]:
    """Flag any position whose resting protective-order quantity != position size.

    positions: symbol -> shares held. protective_qty: symbol -> shares covered by a
    live stop/exit order (0 or missing = unprotected).
    """
    gaps: List[ProtectionGap] = []
    for sym, qty in positions.items():
        covered = protective_qty.get(sym, 0.0)
        if abs(qty - covered) > tolerance:
            if covered == 0:
                note = "UNPROTECTED — no resting exit order"
            elif covered < qty:
                note = f"under-covered: {qty - covered:g} shares have no stop"
            else:
                note = f"over-covered: stop qty {covered:g} exceeds position {qty:g}"
            gaps.append(ProtectionGap(sym, qty, covered, note))
    return gaps


@dataclass
class Drift:
    symbol: str
    expected: float
    actual: float


def position_drift(expected: Dict[str, float], actual: Dict[str, float],
                   tolerance: float = 1e-6) -> List[Drift]:
    """Symbols where the desk's expected position != the broker's actual position."""
    drifts: List[Drift] = []
    for sym in set(expected) | set(actual):
        e = expected.get(sym, 0.0)
        a = actual.get(sym, 0.0)
        if abs(e - a) > tolerance:
            drifts.append(Drift(sym, e, a))
    return drifts
