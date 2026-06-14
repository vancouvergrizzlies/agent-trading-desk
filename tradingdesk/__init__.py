"""tradingdesk — deterministic, tested quantitative core for the Agent Trading Desk.

The trading *decisions* are made by an LLM agent (see ../.claude/commands/*.md), but
every number it relies on — implied vol, historical vol, option pricing, expected
move, liquidity gates, position sizing — is computed by the pure, unit-tested
functions in this package. No fabricated data: prices come from a broker/market
feed at the call site and are passed in explicitly.
"""

from . import (blackscholes, volatility, options_math, liquidity, sizing,
               risk, performance, edgar)

__all__ = ["blackscholes", "volatility", "options_math", "liquidity", "sizing",
           "risk", "performance", "edgar"]
__version__ = "0.1.0"
