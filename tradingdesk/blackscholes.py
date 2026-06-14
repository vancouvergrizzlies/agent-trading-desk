"""Black-Scholes-Merton option pricing and greeks (European, no dividends).

Pure stdlib. Used to value options pre-expiry when estimating reward/risk at a
price target, and to sanity-check broker-supplied greeks.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

SQRT_2PI = math.sqrt(2.0 * math.pi)


def norm_cdf(x: float) -> float:
    """Standard normal CDF via the error function."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def norm_pdf(x: float) -> float:
    """Standard normal PDF."""
    return math.exp(-0.5 * x * x) / SQRT_2PI


def _d1_d2(S: float, K: float, T: float, r: float, sigma: float):
    if T <= 0 or sigma <= 0:
        raise ValueError("T and sigma must be positive")
    vol_sqrt_t = sigma * math.sqrt(T)
    d1 = (math.log(S / K) + (r + 0.5 * sigma * sigma) * T) / vol_sqrt_t
    d2 = d1 - vol_sqrt_t
    return d1, d2


def price(S: float, K: float, T: float, r: float, sigma: float, kind: str = "call") -> float:
    """Black-Scholes price for a European call or put.

    S spot, K strike, T years to expiry, r risk-free rate, sigma annualized vol.
    At/after expiry (T<=0) returns intrinsic value.
    """
    kind = kind.lower()
    if T <= 0:
        return max(0.0, S - K) if kind == "call" else max(0.0, K - S)
    d1, d2 = _d1_d2(S, K, T, r, sigma)
    disc = math.exp(-r * T)
    if kind == "call":
        return S * norm_cdf(d1) - K * disc * norm_cdf(d2)
    if kind == "put":
        return K * disc * norm_cdf(-d2) - S * norm_cdf(-d1)
    raise ValueError("kind must be 'call' or 'put'")


@dataclass
class Greeks:
    delta: float
    gamma: float
    vega: float   # per 1.00 change in vol (divide by 100 for per 1%)
    theta: float  # per year (divide by 365 for per calendar day)


def greeks(S: float, K: float, T: float, r: float, sigma: float, kind: str = "call") -> Greeks:
    """Delta, gamma, vega, theta for a European option."""
    kind = kind.lower()
    d1, d2 = _d1_d2(S, K, T, r, sigma)
    pdf = norm_pdf(d1)
    disc = math.exp(-r * T)
    sqrt_t = math.sqrt(T)
    gamma = pdf / (S * sigma * sqrt_t)
    vega = S * pdf * sqrt_t
    if kind == "call":
        delta = norm_cdf(d1)
        theta = -S * pdf * sigma / (2 * sqrt_t) - r * K * disc * norm_cdf(d2)
    elif kind == "put":
        delta = norm_cdf(d1) - 1.0
        theta = -S * pdf * sigma / (2 * sqrt_t) + r * K * disc * norm_cdf(-d2)
    else:
        raise ValueError("kind must be 'call' or 'put'")
    return Greeks(delta=delta, gamma=gamma, vega=vega, theta=theta)
