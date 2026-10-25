# Operation Billion v0.8 — verified $0-upfront Free AI & Software Map

Last reviewed October 2026. Scope: software and public API choices that do **not require paid subscriptions or paid API keys** in their free/local configuration. Do not confuse $0 software subscription with $0 electricity, unlimited cloud computing, zero marketplace processing fees, or guaranteed sales. All tool recommendations are **choices**, not bundled installed applications. A Windows laptop with 512 GB storage may still have insufficient **RAM/GPU** for image/video diffusion. Check `free-doctor` before selecting a heavy tool.

## Software that the existing bot farm can use right now

* Core: Python standard library, SQLite, built-in image/website/document/sticker creators, Google Trends official RSS, public GitHub search, Hacker News public research. **Working and inside this ZIP**.
* Videos: original PNG scenes, script, timed subtitles, optional FFmpeg MP4. The default sample is image slides, not cinematic generative AI video. Real speech generation is not built into v0.8. FFmpeg itself can be installed free to enable actual MP4 output.
* Websites: responsive static HTML/CSS demonstration projects. Browsers can open them offline, but they are not hosted or handed over to paying customers.
* Court: prosecutor, defense, evidence, five jurors and judge; only approved local, zero-spend operations run. It is rule-based by default; Ollama language-model brainstorming is optional and not a substitute for security rules.

## Audited free-software options (not automatically installed)

| Need | Official project / source | $0 capability | Important limitation |
|---|---|---|---|
| Local text AI | [Ollama](https://github.com/ollama/ollama) | Download and run a small **separately licensed** model with no paid API | RAM/CPU speed varies; models and commercial terms differ |
| Local voice | [Kokoro](https://github.com/hexgrad/kokoro) and [Kokoro-82M weights](https://huggingface.co/hexgrad/Kokoro-82M) | Offline TTS; published weights Apache-2.0 | Requires local runtime and model download; dependencies need review |
| Lighter voice | [Piper](https://github.com/rhasspy/piper) | Offline speech output | Voice licenses vary; some are not commercial-compatible |
| Transcription | [whisper.cpp](https://github.com/ggml-org/whisper.cpp) | CPU-friendly local speech recognition with smaller weights | Requires a separately acquired model and proper rights to source audio |
| Video editing/encoding | [FFmpeg](https://github.com/FFmpeg/FFmpeg) | Offline MP4 encoding and editing | LGPL/GPL and codec configurations differ; no stock footage included |
| Video GUI | [Kdenlive](https://github.com/KDE/kdenlive) or [Shotcut](https://github.com/mltframework/shotcut) | Manual no-cost video editing | Still needs original or license-cleared media |
| Audio cleanup | [Audacity](https://github.com/audacity/audacity) | Record, edit, clean sounds | Does not grant music or voice rights |
| Screen recordings | [OBS Studio](https://github.com/obsproject/obs-studio) | Create authentic tutorials/demo footage | Record only permitted screens, people and material |
| Image diffusion | [ComfyUI](https://github.com/Comfy-Org/ComfyUI) | Free self-hosted pipelines, local API | Many models need strong GPU; check **model license** separately; not a default CPU tool |
| SVG assets | [Inkscape](https://inkscape.org), [VTracer](https://github.com/visioncortex/vtracer) | Original vector designs and conversion | Vectorization doesn't erase copyright |
| Static websites | [Hugo](https://github.com/gohugoio/hugo) | Free fast local static HTML site generator | Public hosting is a separate account and terms |
| Website diagnostics | [Lighthouse](https://github.com/GoogleChrome/lighthouse) | Free Chrome DevTools performance/accessibility audits | Rate-limit and respect the site; verify claims before commercial proposal |
| Authorized UI tests | [Playwright](https://github.com/microsoft/playwright-python) | Free testing of your pages and authorized interfaces | Never bypass login/security/payment checks or terms |
| Public web research | [Crawl4AI](https://github.com/unclecode/crawl4ai) | Browser-based local research formatting | Site robots, permissions, rate limits and copyrights apply |
| Self-hosted research | [SearXNG](https://github.com/searxng/searxng) | Free self-hosted metasearch engine (AGPL-3.0) | Server/install costs, upstream sources' terms, no anti-bot evasion |
| PDF/digital planners | [WeasyPrint](https://github.com/Kozea/WeasyPrint) | Offline HTML-to-PDF; Windows deps | Review font and design licenses |
| Word/PowerPoint | [python-docx](https://github.com/python-openxml/python-docx), [python-pptx](https://github.com/scanny/python-pptx) | Original editable templates | Optional installs, customer compatibility testing |

**Free but not always $0 for selling:** Ko-fi has no monthly or listing fees for its shop, but takes 5% from shop sales (plus payment processing). Do not call this zero *transaction* cost. Seller signup, payout identity, and account verification must be completed by the user. YouTube and TikTok accounts can be created without buying an AI subscription, but direct API publishing requires separate approved applications, scopes and user authorization. YouTube monetization is subject to originality and program requirements; many videos make $0.

## The Free Tool Finder now in the bot farm

`py -3 -m botfarm free-tools --need videos` lists suitable curated tools, current local availability and caveats.

`py -3 -m botfarm free-doctor` checks existing binaries. This is detection only; it cannot prove a model or voice file was downloaded or commercially licensed.

`py -3 -m botfarm free-plan videos "How to choose a budget" --build` produces a five-step plan and court-reviewed local video sample. For websites: `py -3 -m botfarm free-plan websites "independent tutor" --build`. For audio, services, documents and other jobs it creates a plan but **does not pretend** it has a builder or a customer.

`py -3 -m botfarm free-scout --live` performs at most three **fixed GitHub repository metadata queries** and caches successful scans for 24 hours. There is no login, cloud billing, auto-cloning, pip installing, running code, model download or credential transmission. Every newly discovered repo is an **unreviewed candidate** pending manual license, dependencies, hardware, maintenance and safety review. Source rankings do not predict revenue. Read saved candidates with `py -3 -m botfarm free-findings`.

`py -3 -m botfarm audit-check` verifies court, research and free-tool evidence hash chains. A suspected edit halts future scouting.

## Practical $0-upfront creator workflow

1. Research recurring demand and audience questions with Google Trends RSS, public GitHub/HN discussions and **legitimate human verification**. Never infer buying intent from search spikes alone.
2. Select `videos` or `content` playbook. Let the court reject copyright and spending violations. Create the original script and draft assets.
3. Optional: use a **license-checked** local Ollama model for original narration/script proposals, Kokoro/Piper for voice, and FFmpeg for MP4. These are free locally after separately obtaining approved models. Without them, remain in slide/caption mode; don't falsely label it AI motion video.
4. Human owner creates a YouTube/TikTok account, reviews AI-labeling and originality policy, and authorizes any upload only through the platform's supported method. TikTok direct publishing requires app audit and authorized user scope; the bot farm has **no** connected posting adapter.
5. Record actual published URL and genuine audience metrics. Seven-day attention checks and 14-day learn-or-pivot decisions should be used cautiously; a small early audience is not definitive evidence of failure.

## Practical $0-upfront small-business website workflow

1. Find a business through a permitted public business directory or its own website. Do not mass-extract Google Maps listings, sell scraped customer data or circumvent sites' anti-bot restrictions.
2. Create **fictional demonstration** HTML/CSS with built-in Website Factory; optionally improve with local Ollama/Hugo. Audit only permitted URLs with Lighthouse.
3. Prepare a truthful individual service proposal and **unsent** email. In the US CAN-SPAM applies to commercial B2B email; owner must provide honest header, postal contact, ad identification and opt-out handling as applicable.
4. You open your own legitimate seller/contact accounts; actual customers must agree to scope and terms. Don't impersonate a customer, promise results, publish their branding without consent, or send blasts to harvested addresses.
5. Choose a host permitting the intended commercial use. **GitHub Pages cannot be treated as free commercial e-commerce hosting** under its official restrictions. Test hosting terms and custom domain costs separately.

## Costs that cannot honestly be promised away

Electricity, time, internet, storage, payment processing, domain registration if a customer insists on a custom domain, and platform/service-account compliance are real. This project enforces **$0 upfront tools and APIs by default**; it does not claim that every transaction is free, that every AI model is allowed for resale, or that every business model can be completely automated.

## Genuine sources (official documentation)

- https://github.com/ollama/ollama
- https://huggingface.co/hexgrad/Kokoro-82M
- https://github.com/FFmpeg/FFmpeg/blob/master/LICENSE.md
- https://github.com/Comfy-Org/ComfyUI
- https://github.com/ggml-org/whisper.cpp
- https://github.com/GoogleChrome/lighthouse
- https://github.com/searxng/searxng
- https://support.google.com/trends/answer/3076011
- https://docs.github.com/en/rest/search/search
- https://developers.tiktok.com/docs/en/content-posting-api-get-started
- https://developers.tiktok.com/docs/en/content-posting-api-get-started-upload-content
- https://developers.google.com/youtube/data/getting-started
- https://ko-fi.com/shop
- https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits
