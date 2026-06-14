#!/usr/bin/env python3
"""PreToolUse hook — the enforced risk gate.

Wired to place_equity_order / place_option_order, this runs on EVERY order the
agent tries to place, with no model involvement, and returns allow/deny. It is
what lets the desk trade WITHOUT per-trade human approval while still being
unable to breach its own limits: the model decides freely, this code is the
veto it cannot argue with.

Reads current account state from a JSON file the desk maintains (so it can
enforce portfolio-level limits the hook input alone doesn't carry).

Fail policy:
  - kill switch breached (drawdown/day-loss) -> DENY (fail-closed; ruin guard)
  - any unexpected error -> ALLOW + log (fail-open; a bug must never freeze
    all trading, only ruin events block)

Wire in .claude/settings.local.json:
  "hooks": {"PreToolUse": [{
     "matcher": "mcp__robinhood-trading__place_equity_order|mcp__robinhood-trading__place_option_order",
     "hooks": [{"type":"command","command":"python3 <path>/hooks/pretrade_gate.py"}]}]}
"""
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
STATE_PATH = os.environ.get("DESK_STATE", os.path.join(REPO, "desk_state.json"))
LOG_PATH = os.path.join(REPO, "gate_decisions.log")


def _decision(allow: bool, reason: str) -> dict:
    return {"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "allow" if allow else "deny",
        "permissionDecisionReason": reason,
    }}


def _log(line: str) -> None:
    try:
        with open(LOG_PATH, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass


def main() -> None:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw or "{}")
    except Exception:
        print(json.dumps(_decision(True, "unparseable hook input; fail-open")))
        return

    tool = payload.get("tool_name", "")
    if "place_equity_order" not in tool and "place_option_order" not in tool:
        print(json.dumps(_decision(True, "not an order tool")))
        return

    try:
        from tradingdesk import risk

        ti = payload.get("tool_input", {})
        # premium/notional of THIS order
        price = float(ti.get("price") or ti.get("limit_price") or 0)
        qty = float(ti.get("quantity") or 0)
        is_option = "place_option_order" in tool
        new_premium = price * qty * (100 if is_option else 1)

        st = {}
        if os.path.exists(STATE_PATH):
            with open(STATE_PATH) as f:
                st = json.load(f)

        # hard kill switch first (fail-closed)
        tripped, reasons = risk.kill_switch_tripped(
            day_pnl_pct=st.get("day_pnl_pct", 0.0),
            drawdown_from_hwm_pct=st.get("drawdown_from_hwm_pct", 0.0),
            consecutive_losses=st.get("consecutive_losses", 0),
        )
        if tripped:
            msg = "KILL SWITCH: " + "; ".join(reasons)
            _log(f"DENY {tool} {ti.get('symbol','')} :: {msg}")
            print(json.dumps(_decision(False, msg)))
            return

        # full gate (only when we have equity context; otherwise per-order only)
        if st.get("equity"):
            d = risk.gate_check(
                {"premium_total": new_premium,
                 "lane": st.get("pending_lane", "conviction"),
                 "days_to_earnings": st.get("pending_days_to_earnings")},
                st)
            if not d.approved:
                msg = "; ".join(d.reasons)
                _log(f"DENY {tool} {ti.get('symbol','')} ${new_premium:.0f} :: {msg}")
                print(json.dumps(_decision(False, msg)))
                return

        _log(f"ALLOW {tool} {ti.get('symbol','')} ${new_premium:.0f}")
        print(json.dumps(_decision(True, "passed risk gate")))
    except Exception as e:  # fail-open on bugs, never freeze trading
        _log(f"ALLOW (gate error, fail-open): {e}")
        print(json.dumps(_decision(True, f"gate error, fail-open: {e}")))


if __name__ == "__main__":
    main()
