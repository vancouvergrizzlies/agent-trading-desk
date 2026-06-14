# Agent Trading Desk — Framework

An autonomous, options-focused trading desk run by [Claude Code](https://claude.com/claude-code) + the Robinhood MCP. This repo is the **framework** (the procedures and doctrine), not anyone's live account. Bring your own broker connection, your own journal, your own risk.

> ⚠️ **Not financial advice. Real money, real losses.** This is a high-risk, asymmetric options strategy where most individual trades are expected to lose. Use only capital you can afford to lose entirely.

## What's here
| File | Role |
|---|---|
| `.claude/commands/desk.md` | `/desk` — daily management routine (status / wrap / score / hunt), comprehensive micro+macro sweep, the playbook gates |
| `.claude/commands/intel.md` | `/intel` — primary-source catalyst hunt (EDGAR, FDA, Federal Register, transcripts) |
| `.claude/commands/options-hunter.md` | `/options-hunter` — structures asymmetric 100–500%+ option trades; never fabricates data |
| `journal-template.md` | starter "brain" — the doctrine, the lanes, every playbook rule, the scorecard structure. Copy → your own private journal. |
| `settings.template.json` | permissions + a SessionStart snapshot hook (genericize paths/account) |

## Architecture (how it actually runs)
1. **The journal is the brain.** A single markdown file holds: live state (§0), mandate (§1), strategy doctrine (§2), the playbook rules (§9d), the options checklist (§11), and the scorecard (§9b/c/f). Every session reads it first. **It is private — keep it out of git.**
2. **Skills are the procedures.** `/desk` manages, `/intel` finds catalysts, `/options-hunter` structures the trade. They read the journal for state and the account number — nothing personal is hardcoded.
3. **The edge thesis:** a $5k retail account can't out-compute Citadel in liquid mega-caps. Edge lives where the big players aren't — sub-$5B names with dated catalysts (insider clusters, FDA/PDUFA, policy dates, quiet-period expiries) and in *discipline* (pre-committed rules, capped downside via long options). Realistic target ~25–35%/yr; the lottery sleeve swings for more.
4. **Risk is structural, not hopeful:** every position's max loss is written down before entry (premium or stop). Circuit breakers halt the operation on drawdown. The scorecard judges lanes on cumulative dollars, and a doctrine gate forces the whole strategy to change (or stop) if it isn't working after ~15–20 trades.

## Setup (your own instance)
1. Install Claude Code; connect the **robinhood-trading MCP** with *your* account.
2. `cp journal-template.md ~/Desktop/Trading-Journal.md` and fill in §1 with **your** `agentic_allowed` account number, capital, and mandate. **This file stays private (gitignored).**
3. `cp settings.template.json .claude/settings.local.json`; set your permission allowlist + the snapshot-hook path.
4. Run `/desk` to start a session. `/intel` and `/options-hunter` when hunting.
5. (Optional) Set up scheduled crons / a cloud routine for automation — these are per-machine and per-account; build your own.

## Collaborating
The skills + template are the shared framework — edit them, PR them, improve the doctrine together. **Never commit a real journal, real positions, account numbers, or API tokens** — `.gitignore` blocks the obvious ones; double-check before pushing.

## Honest limitations
- Claude can't open its own sessions or watch the tape intraday — it's a scheduled/batch operator, not a day-trader.
- The Robinhood MCP places **single-leg** options only (long calls/puts/LEAPS); spreads are manual in-app.
- Time-stops (sell on date X) need a live session — no broker order type covers them.
- This framework has a *short* live track record. It is an experiment with a built-in kill switch, not a proven money machine.
