#!/usr/bin/env python3
"""PreToolUse hook — the enforced risk gate.

Wired to place_equity_order / place_option_order, this runs on EVERY order the
agent tries to place, with no model involvement. The agent proposes freely; this
code is the veto it cannot argue with — so the desk can trade without per-trade
human approval while staying unable to breach its own limits.

Blocking protocol (per Claude Code PreToolUse):
  - exit 2  -> BLOCK the tool call (stderr shown to the model)
  - exit 0  -> allow (stdout/stderr not shown)
We ALSO emit the JSON permissionDecision for the richer protocol; exit code is
the authoritative blocker.

Fail policy:
  - kill switch / cap breached -> exit 2 (fail-closed; ruin guard)
  - any unexpected error       -> exit 0 (fail-open; a bug must never freeze all
    trading — only genuine ruin events block)
"""
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
STATE_PATH = os.environ.get("DESK_STATE", os.path.join(REPO, "desk_state.json"))
LOG_PATH = os.path.join(REPO, "gate_decisions.log")


def _log(line: str) -> None:
    try:
        with open(LOG_PATH, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass


def allow(reason: str) -> None:
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "allow",
        "permissionDecisionReason": reason}}))
    sys.exit(0)


def deny(reason: str, tool: str = "", sym: str = "") -> None:
    _log(f"DENY {tool} {sym} :: {reason}")
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason}}))
    sys.stderr.write(f"RISK GATE BLOCKED: {reason}\n")  # shown to the model on exit 2
    sys.exit(2)


def main() -> None:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except Exception:
        allow("unparseable hook input; fail-open")

    tool = payload.get("tool_name", "")
    if "place_equity_order" not in tool and "place_option_order" not in tool:
        allow("not an order tool")

    try:
        from tradingdesk import risk

        ti = payload.get("tool_input", {})
        sym = ti.get("symbol", "")
        price = float(ti.get("price") or ti.get("limit_price") or 0)
        qty = float(ti.get("quantity") or 0)
        is_option = "place_option_order" in tool
        new_premium = price * qty * (100 if is_option else 1)

        st = {}
        if os.path.exists(STATE_PATH):
            with open(STATE_PATH) as f:
                st = json.load(f)

        tripped, reasons = risk.kill_switch_tripped(
            day_pnl_pct=st.get("day_pnl_pct", 0.0),
            drawdown_from_hwm_pct=st.get("drawdown_from_hwm_pct", 0.0),
            consecutive_losses=st.get("consecutive_losses", 0))
        if tripped:
            deny("KILL SWITCH: " + "; ".join(reasons), tool, sym)

        if st.get("equity"):
            d = risk.gate_check(
                {"premium_total": new_premium,
                 "lane": st.get("pending_lane", "conviction"),
                 "days_to_earnings": st.get("pending_days_to_earnings")},
                st)
            if not d.approved:
                deny("; ".join(d.reasons), tool, sym)

        _log(f"ALLOW {tool} {sym} ${new_premium:.0f}")
        allow("passed risk gate")
    except SystemExit:
        raise
    except Exception as e:  # fail-open on bugs, never freeze trading
        _log(f"ALLOW (gate error, fail-open): {e}")
        allow(f"gate error, fail-open: {e}")


if __name__ == "__main__":
    main()
