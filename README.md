# Agent Trading Desk — Framework

An autonomous, options-focused trading desk run by [Claude Code](https://claude.com/claude-code) + the Robinhood MCP. This repo is the **framework** (the procedures and doctrine), not anyone's live account. Bring your own broker connection, your own journal, your own risk.

> ⚠️ **Not financial advice. Real money, real losses.** This is a high-risk, asymmetric options strategy where most individual trades are expected to lose. Use only capital you can afford to lose entirely.

## What's here
| Path | Role |
|---|---|
| `tradingdesk/` | **deterministic, unit-tested quant core** (stdlib-only, 11 modules): Black-Scholes + greeks, vol & IV/HV gate, expected-move/payoff/asymmetry math, liquidity gate, sizing, the code-enforced **risk gate** (`gate_check()` + kill switch), **execution** (slippage guard/idempotency), **reconciliation** (protection-gap/drift), a **track-record engine**, and a **SEC Form-4 insider-cluster detector** |
| `tests/` | 80 tests (known-value + a real EDGAR fixture). `python -m pytest -q` |
| `.github/workflows/ci.yml` | CI: lint (ruff) + tests on Python 3.9/3.11/3.12 |
| `.claude/commands/desk.md` | `/desk` — daily management (status / wrap / score / hunt), micro+macro sweep, playbook gates |
| `.claude/commands/intel.md` | `/intel` — primary-source catalyst hunt (EDGAR, FDA, Federal Register, transcripts) |
| `.claude/commands/options-hunter.md` | `/options-hunter` — structures asymmetric 100–500%+ option trades; never fabricates data |
| `journal-template.md` | starter "brain" — doctrine, lanes, every playbook rule, scorecard structure. Copy → your own private journal. |
| `settings.template.json` | permissions + a SessionStart snapshot hook |
| `ARCHITECTURE.md` | the LLM-agent + tested-tools design, in detail |

## Design in one line
**An LLM makes the judgment calls; a tested Python core computes every number it relies on.** The agent decides *what* to look at and *whether* to take a setup; `tradingdesk/` computes implied/historical vol, Black-Scholes value at a target, expected move, liquidity, and size — deterministically, with tests. If a number isn't from a tool, it doesn't get used. See `ARCHITECTURE.md`.

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
- The quant core is tested and the EDGAR pipeline pulls real SEC data, but **the *strategy* is unproven** — a short live track record, currently around break-even. This is an experiment with a built-in kill switch (the doctrine gate), not a proven money machine. The engineering is solid; whether the edge is real is exactly what the scorecard is built to find out.
