# Deploy: the always-on host ("run itself" + serve the dashboard)

Goal: turn this from "trades when your laptop is awake" into a box that runs the
desk loop unattended **and** serves the live dashboard. One host does both.

## Target architecture
```
 cheap always-on VM (e.g. $6–15/mo: Fly.io / DigitalOcean / EC2 t4g.nano)
   ├─ the desk loop (Claude Code session kept alive, or Agent SDK runner)
   │    every cycle: /desk → propose → pretrade_gate.py (DENY/ALLOW) → RH MCP
   ├─ pretrade_gate.py PreToolUse hook  (deterministic risk veto)
   ├─ desk_state.json  (written each cycle; what the gate + dashboard read)
   └─ dashboard/  served read-only (nginx or `python -m http.server`)
        build_dashboard.py runs each cycle → data.json → the public page updates
```

## What YOU provide (I can't provision these)
1. A VM + your cloud account (and ~$6–15/mo).
2. Robinhood MCP auth completed **on that box** (the agentic account login flow).
3. A decision on dashboard exposure: read-only public (the X-niche play) vs. private/behind-auth. **Never expose any control surface — only the read-only page.**

## What I'll build once you pick a host (the concrete artifacts)
- `runner.py` / a loop wrapper (or Agent SDK driver) that runs the cycle on a schedule.
- A `systemd` unit (or Fly/Docker config) that keeps it alive + restarts on crash.
- `desk_state.json` writer wired into the desk cycle so the gate has live state.
- nginx/static config to serve `dashboard/` (read-only).
- A hardening checklist (no inbound except the dashboard; secrets in env/keychain; the gate hook enforced; force-push & destructive cmds denied).

## Honest constraints
- **Claude Code can't open its own sessions.** The loop must be kept alive by the host (systemd/Agent SDK) — that's the whole point of moving off your laptop.
- **RH MCP auth on a headless box** is the fiddly part; budget time for it.
- **Security is real:** this box can place real trades. Lock it down — the dashboard is read-only output, never a remote control.
- This is the genuine "best autonomous agentic account" setup. It's a real (small) DevOps build, not a config flip — but every piece above already exists in this repo except the host glue.

## Interim (no VM yet)
Keep a session alive on your Mac with `caffeinate`, the gate hook wired locally, and
run `build_dashboard.py` each cycle to refresh the page you open from `dashboard/index.html`.
Fragile (laptop must stay awake) but free, and proves the whole loop before you pay for a host.
