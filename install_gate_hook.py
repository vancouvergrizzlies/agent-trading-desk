#!/usr/bin/env python3
"""One-time installer YOU run to wire the risk-gate PreToolUse hook into your
live Claude Code settings. (The AI is blocked from editing its own trade-approval
machinery — by design — so this is the human-run step.)

Run it:  python3 ~/Documents/Coding/agent-trading-desk/install_gate_hook.py

Idempotent: safe to run twice. Preserves all your existing settings/hooks.
"""
import json
import os
import sys

SETTINGS = os.path.expanduser("~/Documents/Coding/trading/.claude/settings.local.json")
GATE = "python3 \"$HOME/Documents/Coding/agent-trading-desk/hooks/pretrade_gate.py\""
MATCHER = "mcp__robinhood-trading__place_equity_order|mcp__robinhood-trading__place_option_order"

HOOK = {
    "matcher": MATCHER,
    "hooks": [{"type": "command", "command": GATE, "timeout": 15, "statusMessage": "Risk gate"}],
}

if not os.path.exists(SETTINGS):
    print(f"!! settings file not found: {SETTINGS}")
    sys.exit(1)

with open(SETTINGS) as f:
    cfg = json.load(f)

hooks = cfg.setdefault("hooks", {})
pre = hooks.setdefault("PreToolUse", [])

# idempotent: replace any existing entry with this matcher
pre = [h for h in pre if h.get("matcher") != MATCHER]
pre.append(HOOK)
hooks["PreToolUse"] = pre

with open(SETTINGS, "w") as f:
    json.dump(cfg, f, indent=2)

print("✅ Risk-gate hook installed into", SETTINGS)
print("   Every place_equity_order / place_option_order now passes through")
print("   hooks/pretrade_gate.py (deterministic allow/deny) before it can execute.")
print("   Restart your session (or run /hooks to reload) for it to take effect.")
