# Operation Billion v0.9 — Final Pre-Account Upgrade

**Purpose:** turn a zero-upfront-cost research and production lab into a practical, auditable launch preparation system **before** you personally open or connect accounts. **No stock or crypto trading is present.** The $1B goal is aspirational, not an earnings forecast. **No paid AI API is required.** Some external providers charge fees after sales, impose quota limits or require eligible accounts; free software itself does not waive those rules.

## What is actually installed / runnable now

- Keep all 29 original creator/research/service specialists, 39 broad research technique playbooks, the courtroom, seven-/fourteen-day retirement rules, zero-cost tool detector, research indexes and existing local dashboard.
- Add `money_studio.py`, a **separate 16-technique operational launch-kit catalogue**. It prepares a buyer, deliverable, five concrete setup steps, no-cost validation measurements and two-week experiment review. `money-kit ... --sample` really creates a local MP4-ready video storyboard or responsive website sample for supported methods. Methods without a builder produce a truthful written kit, NOT a fictitious product.
- The bounded autopilot rotates to one **different business method each UTC day**, going through the same AI Court for local draft approval. Once a method has been retired, the separate original lifecycle chooses another specialty. No approval grants permission to email strangers or to start a marketplace listing.
- Fix topic substitution for local videos: metadata, scene script and MP4 keep your precise requested topic; if Ollama fails, the fallback is **topic-specific**, not an unrelated preset.
- Improve local Qwen3 CPU usage: local-only Ollama HTTP requests have a 300-second ceiling for single drafting jobs; short responses have a smaller token budget and Qwen3 thinking can be disabled. This is not a speed guarantee. The farm will record fallback usage honestly. The installed `qwen3:8b` remains on your computer; no model downloads are performed.
- Known tools are **references**, NOT stealth installs. See `py -3 -m botfarm partner-tools`.
- Marketplace accounts, creator channels, paid subscriptions, business identities, phone/email verification, merchant payment settings and customer outreach remain **unconnected**.

## Open-source research base and integration decisions (reviewed October 2026)

| Tool | Capability | Decision | Real limitation |
| --- | --- | --- | --- |
| [PurffleShorts](https://github.com/Chamanrajragu/purffle-shorts) | Automated Shorts, voice, captions, optional YouTube OAuth | Research/optional separately installed tool | TikTok posting relay may require paid third party; no free unlimited hosting; review repo before running |
| [MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo) | Script-to-video workflow | Optional inspiration | Some provider integrations paid; choose Ollama and authorized local/stock assets |
| [Dyad](https://github.com/dyad-sh/dyad) | Local web/app builder | Optional separate app | Core is open source; premium features separately licensed |
| [bolt.diy](https://github.com/stackblitz-labs/bolt.diy) | Browser-based website/app development with Ollama | Optional advanced tool | Node dependencies; commercial/runtime setup should be reviewed |
| [Activepieces](https://github.com/activepieces/activepieces) | App connectors, retries, routing | Future separately installed integration orchestrator | Requires configuring each account/permission |
| [n8n](https://github.com/n8n-io/n8n) | Visual automations | Reference only | Source-available Sustainable Use License, not unrestricted open source |
| [FFmpeg](https://github.com/FFmpeg/FFmpeg) | Actual local MP4 rendering | Automatically used if on PATH | Fonts/music/codec/media rights independent |
| [Ollama](https://github.com/ollama/ollama) | Local drafts with Qwen3 and others | Optional existing integration | Model weights and laptop resources required |
| [Hugo](https://github.com/gohugoio/hugo) | Fast static websites | Optional | Hosting must allow chosen business use |
| [Lighthouse](https://github.com/GoogleChrome/lighthouse) | Site speed/performance reports | Optional | A diagnostic is only real when actually run on an authorized site |
| [Crawl4AI](https://github.com/unclecode/crawl4ai) | Public-site research | Optional | Respect robots/site conditions; don't bypass blocks |
| [whisper.cpp](https://github.com/ggml-org/whisper.cpp) | Local transcription | Optional | Media-owner authorization required |
| [Piper](https://github.com/rhasspy/piper) | Local speech | Optional | Individual voice models and licenses need checking |
| [VTracer](https://github.com/visioncortex/vtracer) | Convert owned artwork to SVG | Optional | Vectorization doesn't confer copyright |
| [WeasyPrint](https://github.com/Kozea/WeasyPrint) | Printable HTML-to-PDF | Optional | Extra Windows dependencies |

Do **not** run arbitrary GitHub code in autopilot. Repository popularity is not proof of buyers or a guarantee of income. Tools marked optional are researched but **not bundled**.

## Detailed launch workflows, now in `money-paths`

1. **Original Shorts:** choose educational question → source-check → create an original clip → review for genuine value and AI disclosure → connect authorized creator channel and measure engagement.
2. **Creator video editing:** make a rights-cleared demo → define turnaround/revisions → prepare a portfolio → obtain client permission → track paid jobs.
3. **Captioning:** generate SRT sample from media you own → manually check every spoken word → package a service offer → source permissioned inquiries.
4. **Long YouTube teaching:** original script and cited facts → illustrate scenes → render → review → measure viewers and retention only after channel authorization.
5. **Small-business sites:** one fictional responsive demo → honest scope → review a supplied site with authorization → prepare outreach draft → get actual consent/interest.
6. **Landing pages:** demonstrate a simple, truthful conversion page → test mobile usability → solicit interested clients through permitted channels.
7. **Small web utilities:** produce a useful static prototype → test privacy and accessibility → review commercial hosting → measure genuine usage.
8. **Digital stickers:** original SVG and PNG → proper transparent export → relevant storefront category → track legitimate downloads/orders.
9. **Printable planners:** solve a particular practical task → make and print-test sample → list in eligible zero-listing-fee channel if permitted.
10. **Resume templates:** editable files with proofread copy → ethical marketing without guaranteed hiring claims.
11. **Newsletter layout:** opt-in business service proposal → demo template → measure confirmed client interest, never spam.
12. **Podcast clips:** get media-owner rights before any clipping or external publication.
13. **Website reviews:** only actual, documented checks; never claim a scan wasn't run.
14. **Business document templates:** verified original copy/layout → editable deliverables → account and licensing reviews.
15. **Thumbnail design services:** original channel art with no misleading images or stolen identities.
16. **Virtual assistance:** fictitious/anonymized sample → opt-in client scope; never handle customer records without permission.

These 16 *operational packages* coexist with the earlier 39 *research methods* and 29 existing *specialists*; do not add the numbers and claim 84 independent money-making businesses.

## Start using the new commands

After the v0.9 installer passes:

```powershell
py -3 -m botfarm status
py -3 -m botfarm money-paths
py -3 -m botfarm partner-tools
py -3 -m botfarm account-roadmap
py -3 -m botfarm money-kit original_shorts "Five useful money habits for college students" --sample
py -3 -m botfarm video-demo --topic "Five useful money habits for college students" --ai --render
py -3 -m botfarm money-kit website_service "Independent neighborhood cafe" --sample
py -3 -m botfarm money-report
py -3 -m botfarm audit-check
```

`video-demo` writes **5 original PNGs, a script, SRT captions, metadata, and an MP4 if FFmpeg succeeds**. Your Qwen model may produce headings if it answers within the timeout; `metadata.json` states whether it used AI or fallback. A local MP4 is **not** a finished monetized YouTube/TikTok business. It needs narration/original visuals, editorial checks, a channel, upload permissions, and real performance data.

`start_autopilot_windows.bat` / `py -3 -m botfarm autopilot --live` starts the existing bounded research loop and adds one distinct court-approved local business launch kit per UTC day. No side effects beyond local files and public research sources. Keep only one farm process running. It cannot work while the HP laptop is asleep or shut down.

## Account setup matrix (owner only)

Run `py -3 -m botfarm account-roadmap` to see the current matrix. Do NOT put bank account details, SSNs, passwords, recovery codes, sensitive identity documents or payout keys into ChatGPT or the project configuration. Enter these **directly with your chosen service**.

- **Digital storefront:** you create store, agree to rules, set payout, verify eligibility. Farm prepares products and listings, not external posts.
- **YouTube/TikTok:** you open/verify channel, authorize official integration if supported. YouTube Data API has a default free quota with limits; publication is subject to account/API audit requirements. Creator income requires eligibility and original value.
- **Client acquisition:** you create genuine business contact address and supply physical address/opt-out for commercial emails, approve each outbound integration. The farm prepares **UNSENT** drafts and evidence-linked proposals; no blasts.
- **Portfolio:** use an actually permissible host or own domain; the local HTML previews are not live websites yet. GitHub Pages is not intended as free commercial e-commerce hosting.

## Accountability

- A Court decision of **GUILTY** blocks the proposed external action; safer drafts or materially different business ideas must be separately reviewed.
- A decision of **NOT GUILTY** means only safe local work can be created. It is not a sale, account, customer, email sent, public website, or a guarantee of legal compliance.
- Review launched experiments at day 7 and 14; never call an *unlaunched* offer a market failure.
- Record verified numbers separately from any self-reported estimates. The new launch-kit ledger checks recorded metadata for tampering.
- $1B remains a motivational goal, not forecasted earnings. Software has no required cloud subscription; electricity, internet, computer depreciation, future payment-processing fees and your time are not zero-cost resources.

## Troubleshooting / verification

Run all tests: `py -3 -m unittest discover -s tests -v`. If MP4 generation is slow on CPU, try without `--ai` first. Ollama models may take up to five minutes; that is a per-request timeout, not continuous background work. The installer makes a complete backup of `zero_cost_bot_farm`, never overwrites `data/` or `output/`, and restores prior code if verification fails. It has **not been executed on your Windows laptop**; the bundled regression suite has been tested separately on Linux. Keep the older complete backup until happy with the upgrade.
