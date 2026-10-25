# Researched GitHub building blocks — accurate integration status

This bot farm does **not** claim that simply cloning dozens of repositories creates a reliable business. Below are source projects found during research and the **actual** relationship to this build. All links are to maintainers' repositories. Review each project's LICENSE and security advisories before installing.

| Public repository | Potential role in bigger bot farm | Integration status in this ZIP |
|---|---|---|
| [Panniantong/Agent-Reach](https://github.com/Panniantong/Agent-Reach) | Read-only public social/video/GitHub research channels (platform limitations, optional upstream CLIs) | **Not installed**; `doctor` detects local CLI; no third-party accounts accessed |
| [ollama/ollama](https://github.com/ollama/ollama) | Run local models with no hosted inference fees | **Optional functional adapter** using localhost Ollama `/api/generate` for bounded idea brainstorming; model must be separately installed |
| [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph) | Durable multi-step workflow graphs | **Architectural inspiration**, not installed; our small standard-library scheduler is implemented independently |
| [microsoft/autogen](https://github.com/microsoft/autogen) | Agent role discussion and consensus patterns | **Architectural inspiration**, not installed; our roles are deterministic policy reviewers, not separate LLMs |
| [open-multi-agent/open-multi-agent](https://github.com/open-multi-agent/open-multi-agent) | Multijudge review and disagreement / revision | **Architectural inspiration** only; no library code copied or dependency included |
| [browser-use/browser-use](https://github.com/browser-use/browser-use) | Supervised UI research and preview support | **Future opt-in connector**; NOT installed; no CAPTCHA bypass or unauthorized platform operations |
| [microsoft/playwright-python](https://github.com/microsoft/playwright-python) | Browser QA of product previews and local dashboard | **Future test-only optional connector**, NOT installed |
| [GitHub public Search API](https://docs.github.com/en/rest/search/search) | Current public repository research | **Implemented** in `research.py`, opt-in `--live`; subject to rate limits |
| [Hacker News search via Algolia](https://hn.algolia.com/api) | Weak public chatter signals | **Implemented** in `research.py`, opt-in `--live` |

**Real court vs. AI theater:** Five separate jury reviews and four witness reports run as rule-based functions, which makes them auditable and deterministic. They are *not* five independently-running trained AI minds. The optional model only suggests text. The judge always blocks unauthorized spending, marketplace publication, unlicensed assets, inventory without proof, unsolicited messages, and invented earnings.

**Licensing:** No code from the above GitHub repositories is copied into the ZIP. External software licenses, dependencies and marketplaces must be reviewed before any installation or future integration. The original bot-farm code is MIT licensed separately. The project is not sponsored by or affiliated with the listed maintainers.

**Other possible sources, not installed:** Public job boards with permitted API/feeds; commission marketplaces; open bug-bounty platforms with legitimate payouts and authorizations; digital marketplace official merchant APIs; data sources where their license explicitly allows commercial reuse. Actual earnings would still depend on eligibility, skill, fees, demand and completion. Avoid scraped credentials, mass outreach and unlicensed content.

## v0.5 Opportunity Intelligence Hub (integrated vs. evaluated)

**Actually integrated (Python-standard-library implementation; no external project code copied):** public [GitHub Search REST API](https://docs.github.com/en/rest/search/search) metadata queries, public [Hacker News Algolia](https://hn.algolia.com/) search results, and the official [GitHub Blog RSS](https://github.blog/feed/). Saved as cited weak research signals, never as verified sales. All three sources use bounded responses and rate-limited refreshes.

**Researched, *not automatically installed***: [Crawl4AI](https://github.com/unclecode/crawl4ai) (self-hostable Markdown extraction; Apache-2.0), [Trafilatura](https://github.com/adbar/trafilatura) (text/feed extraction; Apache-2.0), [RSSHub](https://github.com/DIYgod/RSSHub) (self-hosted RSS aggregation; AGPL-3.0). These may be connected separately after license/security and laptop-capacity review. Commercial SaaS endpoints may carry charges; no API keys are included.

The Hub discovers tools/topics relevant to 26 manually reviewed income methods and saves unclassified headlines for further investigation; it does not execute downloaded programs, purchase inventory, accept payments, or claim demand without verified evidence. Trading excluded.
