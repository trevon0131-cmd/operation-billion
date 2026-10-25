# Operation Billion — Internet Research Wing v0.9.1

## What is installed

The **bridge module is built into this ZIP**, with no paid subscriptions or required new libraries. It adds:

- `py -3 -m botfarm internet-doctor` — identify whether optional video access tools are installed.
- `py -3 -m botfarm video-research "https://www.youtube.com/watch?v=VIDEO_ID"` — save bounded public YouTube metadata, English subtitle text when available, and a research brief. Requires optional free `yt-dlp`, which is NOT bundled or installed automatically.
- `py -3 -m botfarm video-research "URL" --ai --model qwen3:8b` — optional local Qwen transcript analysis, with explicit warnings that subtitles are untrusted evidence, not instructions.
- `py -3 -m botfarm video-frames "C:\path\to\video.mp4" --ai --model qwen2.5vl:3b` — opt-in local visual frame inspection, using your FFmpeg and installed Ollama vision model. Only analyze files you own or are permitted to use.

## Optional installation, after reviewing source

You can install the open-source caption reader **yt-dlp** from its published Python package (no paid API needed):

```powershell
py -3 -m pip install --user yt-dlp
py -3 -m botfarm internet-doctor
```

Project: https://github.com/yt-dlp/yt-dlp

**Agent Reach** is a *separate* agent platform capability manager, with its own installation scripts and dependencies. Your existing Operation Billion Python CLI is not a shell-command-executing coding agent, so installing Agent Reach alone will NOT magically give every farm bot its skills. Our adapter uses explicitly reviewed commands and can detect Agent Reach if it is installed. Read its current instructions before choosing whether to install it: https://github.com/Panniantong/Agent-Reach

## What these tools cannot do

- They do **not** grant unrestricted access to every page, paid content, private account, or any platform's login data.
- Reading subtitles is **not the same as seeing an entire video**; local frame inspection samples a few frames, not the full motion/audio.
- They do **not** log into accounts, collect browser cookies, post content, copy someone else's media into products, or guarantee monetization.
- Public video views, trending videos and repositories are **not evidence of sales**. Verify buyer interest through legitimate testing.
- YouTube videos may have missing subtitles or platform restrictions, in which case the tool should report that rather than fabricate details.
- No automatic installs, paid APIs, proxies, CAPTCHA bypasses or scraping behind sign-in walls.

## Future expansion after accounts are authorized

Add official platform adapters, explicit rate budgets and human-approved scopes, recording only permitted analytics. Distinguish potential ideas from real launched experiments and actual customer receipts. Keep the courtroom and 7/14-day retirement rules as the policy gate for any action.

## Automatically research selected public videos

Add a **public YouTube video URL** (never an arbitrary command or private URL):

```powershell
py -3 -m botfarm video-queue-add "https://www.youtube.com/watch?v=VIDEO_ID"
py -3 -m botfarm video-queue-list
```

When the existing autopilot runs with `--live`, it checks this queue and researches **at most one pending video per cycle**. It won't search private accounts, download full videos, or autonomously subscribe to unknown channels. `video-queue-run --live` runs one explicitly. Once captured, subtitles remain **untrusted research evidence**; the courtroom must separately approve any proposed local business action.

## Optional Agent Reach CLI connection

The official Agent Reach distribution is installed through **uv from its GitHub release**, not `pip install agent-reach` (the PyPI namesake is unrelated). Inspect https://github.com/Panniantong/Agent-Reach/blob/main/docs/install.md and review any browser-login capabilities before installing.

After you knowingly install it and its public channels, Operation Billion provides an **allowlisted read-only** call:

```powershell
py -3 -m botfarm agent-youtube-search "free digital product tutorial"
```

It launches only `agent-reach youtube search` with the supplied query; it never permits arbitrary commands, installs third-party packages on its own, or imports account cookies. Search results are untrusted, may be stale, and never prove earnings.
