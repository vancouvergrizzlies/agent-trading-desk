# Autonomous execution & the enforced gate

This desk can trade **without per-trade human approval** — and stay unable to
breach its own risk limits — because of one mechanism: a PreToolUse hook that runs
the deterministic risk gate on every order. The agent proposes freely; the hook is
the veto it cannot argue with.

## How autonomy actually works here
1. **Order tools are allowlisted** in `.claude/settings.local.json` → no permission
   prompt per trade.
2. **The agent has standing trade autonomy** (granted in the journal mandate) → it
   places orders without asking you.
3. **Every order routes through `hooks/pretrade_gate.py`** (PreToolUse) → the gate
   allows or DENIES by code. Drawdown breach, over-cap, etc. block the order
   regardless of what the model wants. This is what makes hands-off safe.

## Wiring the hook
Add to `.claude/settings.local.json`:
```json
"hooks": {
  "PreToolUse": [{
    "matcher": "mcp__robinhood-trading__place_equity_order|mcp__robinhood-trading__place_option_order",
    "hooks": [{"type": "command",
               "command": "python3 /ABSOLUTE/PATH/agent-trading-desk/hooks/pretrade_gate.py"}]
  }]
}
```

## The desk must keep `desk_state.json` current
The hook reads portfolio state the order alone can't carry. Each cycle, the desk
writes `desk_state.json` (gitignored — it has your real numbers):
```json
{"equity": 5000, "open_premium": 700, "day_pnl_pct": 0.0,
 "drawdown_from_hwm_pct": -0.02, "consecutive_losses": 0,
 "lotto_position_count": 1, "theme_position_count": 0,
 "pending_lane": "lotto", "pending_days_to_earnings": null}
```
Without it, the hook still enforces the per-order cap + kill switch on whatever
state is present; with it, it enforces the full portfolio gate.

## Fail policy
- **Kill switch breached → DENY** (fail-closed; ruin guard).
- **Any gate bug/error → ALLOW + log** (fail-open; a bug must never freeze
  trading — only ruin events block). Decisions are logged to `gate_decisions.log`.

## The hard limit honesty
Truly unattended 24/7 operation still needs an always-on host: Claude Code can't
open its own sessions, and session-bound crons only fire while a session is live
and the machine is awake. For real autonomy you either keep a session running
(`caffeinate`) or deploy the loop on a server with the broker connection. The hook
makes trading *safe* without you; it does not make the machine run itself.
