# Dashboard — local, bring-your-own-data

A self-contained read-only page: Agent-vs-QQQ % curve, positions, track-record
stats, watchlist with live charts, and the agent's decision feed. It's a **tool** —
your real data never goes in the repo; you supply your own `data.json` locally.

## Run it (30 seconds)
```bash
cd dashboard
python3 -m http.server 8137
# open http://127.0.0.1:8137
```
Out of the box it renders `data.example.json` (fake numbers) so you can see the layout.

## Use your own data
Two ways:

**A. Quick — hand-edit:**
```bash
cp data.example.json data.json     # data.json is gitignored — stays local
# edit data.json with your real account/positions/curve
```
The page polls `data.json` every 30 min (and on refresh).

**B. Generate it from inputs** (what the agent does each cycle):
```bash
mkdir -p inputs
# write inputs/account.json, positions.json, closed_trades.json,
# equity_curve.json, watchlist.json, decisions.json  (see build_dashboard.py)
python3 build_dashboard.py          # -> writes data.json
```
`build_dashboard.py` reuses `tradingdesk.performance` so the stats can never
disagree with the scorecard.

## Privacy
- `data.json`, `data.generated.json`, and `inputs/` are **gitignored** — your real
  positions never get committed or pushed.
- Only `index.html`, `build_dashboard.py`, and `data.example.json` (fake) are shared.
- The server binds to `127.0.0.1` — local only, not your network or the internet.

## Hosting (optional, later)
Static, so GitHub Pages / Netlify / any static host works — **but Pages is public
and serves only committed files.** If you ever host it, generate a **public-mode**
`data.json` first (% returns + curve + tickers, no dollar amounts / share counts /
account size). Until then: keep it local. It's safe as-is.
