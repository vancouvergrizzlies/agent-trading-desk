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

## The quantitative core (`tradingdesk/`, stdlib-only, 31 tests)
| Module | Responsibility |
|---|---|
| `blackscholes.py` | BSM price + greeks (delta/gamma/vega/theta); used to value options pre-expiry at a target |
| `volatility.py` | historical vol from prices; the IV ≤ ~1.2×HV "premium is cheap" gate |
| `options_math.py` | straddle-implied move, payoff multiple at target, reward/risk, the asymmetry test |
| `liquidity.py` | OI / volume / bid-ask-spread gate — kills illiquid chains before they eat the edge |
| `sizing.py` | contracts-for-budget + portfolio caps (per-trade %, total open premium ≤40%) |
| `edgar.py` | **SEC Form-4 cluster-buy detector** — pulls the official daily index + structured XML (replaces flaky HTML scraping); pure parsers are tested against a real fixture, network client honors SEC's UA + 10 req/s rules |

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
