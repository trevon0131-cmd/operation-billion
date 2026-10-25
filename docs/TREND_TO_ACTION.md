# Operation Billion — Trend-to-Action Startup Laboratory (v0.6)

## What it actually does

1. The existing Opportunity Intelligence Hub gets permitted public GitHub repository metadata, Hacker News discussion metadata, and GitHub Blog RSS. Sources are rate limited and cached by its existing v0.5 engine.
2. The new Trend Engine reads those saved observations and (in `--live` mode) polls the **official Google Trends Trending now RSS export**, at most once per six hours. No scraping of standard Google search-results pages, no CAPTCHA bypasses, no logins or search-engine rank-checking.
3. It looks for relevant terms in 26 defined money-making techniques; popular tools and spikes are **weak hints, never verified buyer demand**. Old sources (>30 days) do not count as fresh matches. Unmatched news remains data, not a generated product proposal.
4. It selects ideas that the existing court already marked `NOT GUILTY` for **local work**. Its own court checks the proposed local sample again. Rejected, retired, or tampered cases do not create startup kits.
5. It creates `output/startup_kits/idea_NNNN_method/START_HERE.md` and `startup_plan.json`: exact buyer, five startup tasks, how to validate, channels and fees to review, manual account gates, who owns the next action and the 7/14-day lifecycle rule.
6. For 20 compatible methods, it uses one of the existing **original local product builders** to generate a sample and checks quality. Other methods (human user testing, microtasks, etc.) remain explicitly human-only. No fake platform accounts, publishing, sales, clicks, or revenue.
7. Every startup plan JSON is SHA-256 pinned to an append-only audit ledger. The engine deduplicates plans and refuses new work if its ledger is corrupted.

## Commands from the existing VS Code farm folder

```powershell
py -3 -m botfarm trend-scan --live --limit 5
py -3 -m botfarm trend-report
py -3 -m botfarm audit-check
```

You do not need to run those commands individually after enabling the existing v0.6 autopilot. Its loop runs opportunity research and startup-kit creation when the laptop is on, with a 6-hour Google RSS cache.

## How sales testing works

Creating an original sample is *not launching a business*. Its startup packet tells the owner what account, verification, product rights, delivery capacity and fees are needed. No public listing, customer emails, identity checks or payouts are automated. Real trials must be launched on an authorized platform and then tracked with **real** signals: views, clicks, inquiries, sales and costs. Existing v0.5 experiment records mark 7-day low engagement and 14-day failure or `UNLAUNCHED` retirement, and shift into different ideas. User-entered figures are labeled unverified until a proper authenticated seller integration is installed.

## Validated sources and constraints

- Google: https://support.google.com/trends/answer/3076011 — Trending now can export RSS. A trending news search is not product demand.
- Google: https://developers.google.com/search/docs/essentials/spam-policies — automated queries to ordinary Google search results are restricted; this integration does not scrape search results.
- GitHub: https://docs.github.com/en/rest/search/search — publicly searchable repository metadata and API rate limits; existing scouts may receive 403/429 and must back off.
- Hacker News: https://github.com/HackerNews/API — official public discussion data reference; discussions are not customer orders.
- Website monitoring candidate: https://github.com/dgtlmoon/changedetection.io — OPTIONAL separate service, not silently installed or run.

Only original farm code and public metadata are packaged. No third-party codebase is copied or executed; repository popularity is not evidence of customer willingness to pay. Seller/advertiser platform terms, fees and copyright still apply.
