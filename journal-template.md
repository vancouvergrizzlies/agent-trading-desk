# 🤖 Agent Trading Journal — TEMPLATE

> Copy to `~/Desktop/Trading-Journal.md` (private, gitignored) and fill in your own state. This is the desk's brain: strategy, rules, scorecard. Every session reads §0 + §9d first.
> **Read protocol:** each session reads **§0 STATE + §9d playbook**; full read only when §0 is stale or in score/hunt mode. §6/§8/§9 are append-only; §0 is overwritten each session.

---

## 0. STATE — overwritten every session (history lives in §6/§8/§9)
**SYNCED:** <timestamp>. **STALE-IF:** older than last market session → full re-sync before any action.
- **Equity / cash (settled vs unsettled) / HWM:** <fill>
- **POSITIONS:** table of ticker · qty · cost · last · P&L · stop(order id) · target · signal-tag
- **RESTING ORDERS:** ids + what session they protect (GTC = 9:30–16:00 ET only)
- **NEXT CATALYSTS:** dated events + the tradeable read on each
- **ORDERS OF THE DAY:** the pre-committed, numeric decision cards for the next session

## 1. Account & Mandate
- **Account:** `<your agentic_allowed account #>` — the ONLY account the desk trades. Never touch others.
- **Capital / buying power:** <fill> (cash account → size off SETTLED cash, T+1)
- **Scope:** stocks + single-leg options (Level 2). Set your risk appetite here.

## 2. Strategy — doctrine
**Edge thesis:** a small retail account can't out-compute institutions in liquid mega-caps. Edge lives where they aren't (sub-$5B names, dated catalysts) and in discipline. Honest EV ~25–35%/yr; the lottery sleeve swings for more. Asymmetry everywhere: capped downside (premium/stop), open upside.

**Lanes (ranked):**
1. **Insider-cluster microcaps** — ≥3 open-market insiders incl. C-suite, sub-$2B, recent. Primary engine.
2. **Small-cap catalyst anticipation** — policy/FDA/regulatory dates, quiet-period expiries, in <$5B names.
3. **PEAD / post-earnings drift** — confirmation tilt only (dead outside microcaps).
4. **Options = risk-shaping + the aggression instrument** — long calls/puts; defined risk; see §11.
5. **🎰 Lottery sleeve** — bounded, 5–10x targets, total-loss-sized; see #30.

**Circuit breakers (pre-committed):** single-day −X% → no new entries; −Y% from HWM → flatten sleeve + halt + notify, resume needs explicit ok; N consecutive losses → halt + half-size.
**Doctrine gate:** at ~15–20 closed trades, if hit-rate AND alpha-vs-benchmark both fail → halve sizing / change strategy. Pre-commit it so neither outcome is negotiated in the moment.

## 3. Capabilities & limits (honest)
CAN: quotes, positions, orders, place/cancel stock + single-leg option orders, read option chains/IV/greeks, web research, scheduled crons (session-bound), cloud routine (research/notify only). CANNOT: react intraday between checks, see transaction-level options flow / dark pools, trade multi-leg spreads or crypto via MCP, rely on memory for live data (always verify).

## 4. Automation architecture
Event-driven: opening a session triggers the desk (SessionStart hook flags "pending"). Cloud routine = daily research + Slack triage ("nothing actionable" vs "open a session"). Crons execute pre-committed cards with staleness gates + idempotency. Broker GTC orders = the 24/7 protection layer. **Time-stops need a live session** (no broker order type for "sell on date X").

## 6. Trade Log (append-only)
| # | Date | Ticker | Side | Qty/$ | Price | Signal tag | Thesis | Stop | Target | Status | Result |
|---|------|--------|------|-------|-------|-----------|--------|------|--------|--------|--------|

## 8. Decision Log (append-only) — dated notes with the *why* behind every action.

## 9. Learning Loop (the edge engine)
- **9a. Per-trade post-mortem** (every close): thesis right? plan followed? lesson → §9d. Increment §9c.
- **9b. Prediction scorecard** (pre-register BEFORE outcome): date · prediction · conf% · due · scoring-rule · result.
- **9c. Signal scorecard** (per-close): trades / win% / cumulative-$ per signal tag. Lotto judged on **cumulative $, not win rate**.
- **9d. Playbook — rules.** Status tags: [STANDING] binding · [HYP n=x] tiebreaker until validated · [VALIDATED] · [KILLED].
  - **#1** Don't buy high-beta into a macro print; timing is part of the edge.
  - **#3** Smart-money disclosures lag → confirm, never originate a late chase.
  - **#4** Don't blind-copy fund positions; take the idea, size it your way.
  - **#5** Respect the GTC stop; overrides logged with reason.
  - **#7** Before calling anything a "dislocation," check WHY it's down (YTD, last earnings, guidance, contracts). Fundamental break = falling knife.
  - **#8** Lottery sleeve ≤ set % at cost; un-stopped positions count full value at risk; every un-stopped position gets a written manual-exit rule; no refill the week a sleeve name is cut.
  - **#9** Watch breadth, not just the index.
  - **#10** Anchor theses on STRUCTURAL catalysts (budgets/contracts/secular), not headlines — headlines reverse overnight.
  - **#12** A 10x needs an underpriced earnings supercycle (EPS↑ × P/E↑), any cap — hunt early, don't chase late.
  - **#13** Obvious supercycle = priced in. Still-early test: price lagging fundamentals AND margins expanding.
  - **#14** PRE-CATALYST SCREEN every session: earnings calendar + macro/FDA/policy ∩ themes ∩ fresh insider clusters → tiny pre-position only with thesis + edge.
  - **#15** Cash account: size off SETTLED cash (T+1); 3 good-faith violations = 90-day restriction.
  - **#16** SWAP procedure for partial exits (no OCO): pre-write replacement stop → cancel → sell → re-stop → verify; never end a session between cancel and re-stop.
  - **#17** Circuit breakers (§2) checked at step 0 every session.
  - **#18** Every order gets a fresh `uuidgen` ref_id (reuse on retry); reconcile positions+orders before any planned tranche.
  - **#19** GTC stops/TPs protect 9:30–16:00 ET only; overnight/pre-market exits = whole-share limit in extended/all-day hours; fractional = regular hours only. Pull the chain (straddle implied move + skew) before holding through any binary.
  - **#20** OPTIONS doctrine: risk-shaping tool, not an edge source. 3 uses: (1) deep-ITM stock substitution, (2) defined-risk on gap-prone names, (3) post-IV-crush catalyst drift. Bans: <14 DTE; buying into/through earnings/FDA/FOMC; <0.30-delta lottery (except the sleeve); spread >10% of mid; averaging down; >set% of account in open premium.
  - **#21** INSIDER-CLUSTER lane: daily OpenInsider cluster screen; require ≥1 C-suite, not gapped >5%, prefer flat-to-up since the insiders' trade; entry day 2–3 post-filing, limit only; time-stop ~30 trading days; half off at +15%; hard stop −12%. Shares, not options (microcap option spreads exceed the edge).
  - **#22** Congress: BUY disclosures = confirmation only (relevant committee, ≥threshold, small cap); 2+ member SELLS in a held name = exit prompt. Admin disclosures = dead signal.
  - **#23** CONCENTRATED CONVICTION book: 3–5 positions. A+ setups sized up; express as a 0.55–0.70-delta 60–90 DTE call at ~⅓ stock capital when the chain is liquid, else shares.
  - **#26** Tax: wash-sale block (no re-entry into a name sold at a loss for 30 days); track realized P&L; let losers offset winners.
  - **#27** Shadow book: log every REJECTED setup + the gate that killed it; weekly, check rejects' forward returns to calibrate the gates.
  - **#28** Correlation cap: max 2 positions per theme; total open premium ≤ set% of equity.
  - **#29** Bear doctrine: when mostly cash, CASH IS THE PUT — don't buy index/macro puts. Recession expression = TLT calls on CONFIRMED data. No new entries into FOMC/mega-IPO pricing days.
  - **#30** LOTTERY sub-sleeve: up to 3 concurrent, capped $ each, sized as certain total loss, **target 5–10x**. Gates: named catalyst + path to a big move (not "it's volatile"); not parabolic (#13); NO insider selling into the move; logged to §9b first. **Judged on cumulative $, never hit rate.** Lane review at N tries or −$cap.
  - **#31** IPO QUIET-PERIOD lane: track recent IPOs; quiet period ends ~IPO+25–40d = analyst-initiation catalyst. Works best on names near/below IPO price (depressed → initiations surprise); skip the already-run ones.
- **9e. Review checklist** (weekly/monthly): score due predictions, update §9c, benchmark vs SPY/QQQ, distill ONE rule change, archive stale analysis.
- **9f. Benchmark ledger:** one row/session — account vs a frozen QQQ-equivalent from inception. The honesty meter.

## 11. OPTIONS ENTRY CHECKLIST (run before every option buy)
A. **Volatility gate** — IV ≤ ~1.2× 30-day HV (compute HV from price history); enter post-earnings day 2–3 (after IV crush), never into a print.
B. **Liquidity gate** — strike OI ≥ 100, has volume, spread ≤ ~10% of mid; thin chain → shares or skip.
C. **Contract** — 60–90 DTE (≥3 weeks past the catalyst); delta 0.55–0.70 (≥0.70 for stock substitution).
D. **Execution** — limit at mid, walk one tick, never >40% through the spread; no market orders on options.
E. **Exits** — 21 DTE = out; +100% = sell half, ride the rest; thesis break = out; never hold through the next earnings.

## 12. IMPROVEMENT BACKLOG — self-directed: advance ≥1 item every session (data pipelines, calendars, new lanes to research). The desk should be measurably better after each session.
