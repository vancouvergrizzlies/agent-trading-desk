# Architecture

This is an **LLM-orchestrated trading desk with a deterministic, tested quantitative core** — not a pile of prompts, and not a black-box "AI picks stocks" toy. The split is deliberate:

```
            ┌─────────────────────────────────────────────┐
            │  LLM agent (Claude Code)  — judgment layer   │
            │  skills: /desk  /intel  /options-hunter      │
            │  reads doctrine + state from the journal      │
            └───────────────┬─────────────────────────────┘
                            │ calls
        ┌───────────────────┼───────────────────────────────┐
        │                   │                                │
┌───────▼────────┐ ┌────────▼─────────┐          ┌───────────▼──────────┐
│ tradingdesk/    │ │ Robinhood MCP    │          │ Journal (private md) │
│ (tested code)   │ │ (live quotes,    │          │ §0 state · §2 doctrine│
│ blackscholes    │ │  chains, orders) │          │ §9d rules · §9 score │
│ volatility      │ └──────────────────┘          └──────────────────────┘
│ options_math    │
│ liquidity       │   ← every NUMBER the agent trusts is computed here,
│ sizing          │     from data passed in explicitly. No fabrication.
│ edgar (Form 4)  │
└─────────────────┘
```

## Why this split
- **LLMs are good at judgment, bad at arithmetic and prone to confabulating data.** So the LLM decides *what* to look at and *whether* a setup is worth taking, but the quantitative facts — implied vs historical vol, Black-Scholes value at a price target, expected move, liquidity, position size — come from `tradingdesk/`, which is pure, deterministic, and unit-tested. If a number isn't from a tool, it doesn't get used (the data-integrity rule in `/options-hunter`).
- **Risk is structural, not vibes.** Sizing caps, the IV/HV gate, the liquidity gate, and the payoff/asymmetry math are code with tests, so they behave the same every run.

## The decision loop (how the modules compose — one system, not a pile)
```
 data/edgar (signals)  →  options_math + volatility + liquidity (is the setup good?)
        →  sizing (how big)  →  risk.gate_check() ← THE SINGLE DOOR every order passes
        →  preflight (assert data fresh/sane, reconciled, not duplicate, risk OK) ← HALTS on any failure
        →  execution (limit price, slippage guard, idempotent fill)
        →  [Robinhood MCP places it]
        →  recon (did reality match intent? protection gaps?)
        →  performance (score it; feed the track record back to strategy)
```
Every proposed order funnels through **one** function — `risk.gate_check()` — which a
PreToolUse hook can enforce so the model literally cannot place an order that breaches
the limits. That single chokepoint is what keeps this coherent instead of sprawling.

## The quantitative core (`tradingdesk/`, stdlib-only, 64 tests)
| Module | Responsibility |
|---|---|
| `blackscholes.py` | BSM price + greeks; value options pre-expiry at a target |
| `volatility.py` | historical vol; the IV ≤ ~1.2×HV "premium is cheap" gate |
| `options_math.py` | straddle-implied move, payoff multiple at target, reward/risk, the asymmetry test |
| `liquidity.py` | OI / volume / spread gate — kills illiquid chains before they eat the edge |
| `sizing.py` | contracts-for-budget + portfolio caps |
| `risk.py` | **the gate** — `gate_check()` single door + kill switch + earnings blackout; deliberately aggressive limits, enforces ruin-prevention only |
| `execution.py` | limit pricing with slippage guard, idempotency keys, fill classification — never cross a wide spread, never double-fire |
| `recon.py` | protection-gap + position-drift detection (the ORCL-stub / SOUN-missed-stop lessons, in code) |
| `preflight.py` | **runtime self-check** — deterministic assertions run every cycle before any order (data freshness/sanity, reconciliation, duplicate guard, kill switch, earnings blackout, order sanity); HALTS on failure. NOT an LLM introspecting — `assert`, not "is this good?". An adversarial test suite proves each broken condition halts trading. |
| `performance.py` | track-record engine: win rate, profit factor, expectancy, drawdown, Sharpe, alpha, per-lane |
| `edgar.py` | **SEC Form-4 cluster-buy detector** — official daily index + structured XML (replaces flaky scraping); UA + 10 req/s compliant |

## The agent layer (`.claude/commands/`)
- `/desk` — daily management: sync, comprehensive macro+micro sweep, the pre-catalyst screen, manage per the playbook, write state.
- `/intel` — primary-source catalyst hunt (EDGAR, FDA, Federal Register, transcripts).
- `/options-hunter` — structures asymmetric 100–500%+ trades using the quant core; never fabricates prices.

## State (`journal-template.md` → your private journal)
The journal is the agent's memory and source of truth: live positions (§0), strategy doctrine (§2), 25+ codified playbook rules (§9d), the options checklist (§11), and a pre-registered prediction/PnL scorecard (§9). It stays **out of git** — only the template ships.

## Honesty by design
- `edgar.py` separates pure parsing (tested) from network I/O (not faked in tests).
- The hunter labels every figure VERIFIED vs ASSUMPTION.
- The README and journal lead with limitations and a short, unproven live track record. The system has a built-in doctrine kill-switch: if the scorecard shows no edge after ~15–20 trades, the strategy changes or stops.

## Run the tests
```bash
python -m pytest -q          # or: python -m unittest discover -s tests
```
