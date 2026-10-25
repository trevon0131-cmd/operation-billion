# Opportunity Intelligence Hub — v0.5

## What it actually does

The original 29 specialists remain in place. The new **Opportunity Intelligence Hub** is an additional research wing with **26 distinct, curated zero-upfront research methods**, spanning creator work, digital downloads, web services, remote tutoring, software prototypes, freelance delivery, stock media, research participation, human microtasks, newsletters, and more. These are **not** 26 new intelligent executor agents, 26 seller connections, or proven earners. The lab creates local experiment briefs, not external sales.

The live scouts use three bounded public metadata feeds, without passwords or API charges:

* [GitHub public repository search](https://docs.github.com/en/rest/search/search) — fixed server-side queries, short metadata and project links, respecting public API rate limits. Repository popularity is not evidence of earnings.
* [Hacker News search powered by Algolia](https://hn.algolia.com/) — public discussion titles and links to HN, not endorsements.
* [GitHub Blog RSS](https://github.blog/feed/) — software news and capability ideas. The code processes only headlines and official blog links; it does not copy or republish article text.

Scouts rotate their query focus and maintain a **six-hour refresh cache**. Network timeouts and failures are stored as failures; they never become fake trends. The app does not follow unknown web addresses, evade CAPTCHAs, download and run GitHub projects, or break site terms.

Open-source projects worth considering *later*, separately and after license/security review: [Crawl4AI](https://github.com/unclecode/crawl4ai) (self-hosted browser research, browser installation required), [Trafilatura](https://github.com/adbar/trafilatura) (clean content extraction, Apache-2.0), [RSSHub](https://github.com/DIYgod/RSSHub) (self-hosted RSS aggregator, AGPL-3.0). They are **researched options, not installed dependencies**. The included scouts run with Python's standard library only.

## Automatic cycle

1. Read cached or updated fixed public sources if `--live`.
2. Save each new public-source observation with a unique fingerprint and separate tamper-evident SQLite audit.
3. Match the source to an eligible **research technique**. If no technique fits, put the signal in an *unclassified research queue* rather than executing unfamiliar code.
4. Send each local plan to the existing **AI-style deterministic court**, which can allow local planning only. Any proposal that requests money, publishing, unauthorized outreach, misuse of intellectual property, or misleading claims is rejected by existing hard-stop rules.
5. Create a local `VALIDATION_BRIEF.md` with: source provenance; one original possible deliverable; intended customer; a no-upfront validation action; platform prerequisites; realistic cost/fees caveats; and the 7/14-day measurements.
6. After a real launch is **reported by the user**, count 7 days / 100+ reported views / 0 clicks for an early review, or 14 days without positive net outcome for retirement. **Never** assume missing data indicates no demand. Unlaunched plans time out separately at 14 days.
7. Retired techniques are not automatically recycled. The next plan rotates toward another available income method. If all 26 are used up and research yields no safely implementable new method, the farm pauses instead of making up new capabilities.
8. A positive net outcome stays active only as **user-reported / unverified** until a real seller account provides authenticated data through a future permissioned connector.

## Commands

From your existing bot-farm folder in VS Code PowerShell:

```powershell
py -3 -m botfarm opportunity-scan --live
py -3 -m botfarm opportunity-list
py -3 -m botfarm opportunity-review
explorer .\output\opportunity_research
```

The normal `start_windows.bat` or `py -3 -m botfarm autopilot --live` runs the opportunity scans in the regular autonomous cycle. Public research requires your computer to be on and connected. Local-only planning continues without internet:

```powershell
py -3 -m botfarm opportunity-scan
```

After **you** actually publish an approved, correctly described item:

```powershell
py -3 -m botfarm opportunity-launch 1 https://your-actual-listing-url
py -3 -m botfarm opportunity-record 1 view --quantity 100
py -3 -m botfarm opportunity-record 1 click --quantity 2
py -3 -m botfarm opportunity-record 1 sale --quantity 1 --gross 4.00 --fee 0.75
py -3 -m botfarm opportunity-review
```

Do not record imaginary transactions. All metrics entered with these commands are **user-reported and unverified**. No seller account has been connected.

## What is stored

* `data/opportunity_lab.sqlite3` — source observations, court-reviewed ideas, lifecycle status and hashed audit records.
* `data/opportunity_last_online.json` — last public scout refresh result and non-sensitive errors.
* `output/opportunity_research/RESEARCH_LIBRARY.md` — research index, 26 technique templates, and unclassified new signals.
* `output/opportunity_research/idea_####_*/VALIDATION_BRIEF.md` — per-hypothesis original test plan.

The installer deliberately excludes ALL `data/` and `output/` folders. Previous bot-farm history stays in the original project.

## Hard boundaries

No trading, crypto, stock or investment bots. No self-rewriting code; no automatic ad-spend, purchases, domain registration, accounts, ID checks, payout setup, social posting, merchant uploads, direct messages, spam, browser evasion, or impersonating humans in paid tasks. An account connected later can enable *only* authorized permitted actions. Research is not the same as real customer demand or revenue. Software may cost $0, while hardware, hosting, store commissions, fulfillment, taxes and time do not.
