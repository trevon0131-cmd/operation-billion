# Operation Billion v0.9.3 — Original Creator Lab (free, local-first)

This update is cumulative over v0.9.2. The previous 29 specialists, court, 39 research methods,
Trend/Internet Hub, startup playbooks, audited database, video finisher, seller drafts and
7/14-day business experiment lifecycle are preserved. It does **not** connect accounts,
upload content, send email, or prove revenue. Trading stays excluded.

## What this version actually creates

Five original formats, each with five coherent scene images, an original story/script,
SRT captions, metadata, the court's written verdict and a human-review checklist:

- `fruit-story` — original cartoon fruit characters with changing poses, dialogue and story beats
- `fictional-reddit` — original fictional first-person narration in a Reddit-style reader layout; **not a scraped Reddit post**
- `quick-quiz` — trivia, audience prompts, countdown and answer/explanation outline
- `micro-drama` — short fictional storytelling with a hook and reveal
- `tips` — original mini-lesson / educational explanation

Generated visuals are local Python drawings. **They are not photorealistic diffusion video** and the fruit
character mouths are *illustrations*, not frame-perfect audio lip sync. The scene art does not require a GPU,
paid AI API or third-party images. `--ai` uses your local Ollama (`qwen3:8b`) with fallback clearly recorded.
`--narrate` optionally uses the already-installed `kokoro-onnx` and weights in your separate `.voice-env`.
`--render` uses your installed FFmpeg to export MP4, with narration-aligned duration so it doesn't cut off a
longer recording at 15 seconds. The accompanying SRT is timed to the overall video, not individually forced
aligned to every spoken word.

## Try it in the existing VS Code project

```powershell
py -3 -m botfarm viral-formats
py -3 -m botfarm viral-studio --format fruit-story --topic "The banana who lied to a strawberry" --render
py -3 -m botfarm viral-studio --format fictional-reddit --topic "The strange note under my apartment door" --ai --narrate --render
py -3 -m botfarm viral-studio --format quick-quiz --topic "Common mistakes with college budgets" --narrate --render
```

Narration is optional. If the Kokoro engine isn't ready, remove `--narrate` instead of blindly reinstalling
Python. If your Qwen CPU model is slow, remove `--ai`: original curated scripts still render.

Output files go under `output/viral_studio/<format>/<id>/`. Open `preview.mp4`, `scenes.json`, `captions.srt`,
`metadata.json` and `PUBLISHING_CHECKLIST.txt` to evaluate each draft.

The existing continuous `autopilot --live` loop can create **one** additional new-style local draft per day,
rotating through formats. It uses a curated topic, which is *not* falsely claimed to be trending.
Your separate `trend-scan --live` and public video research tools still provide research and evidence.
To produce a trend-specific video, pass a topic you've validated into `viral-studio --topic`.

## Free/open-source research references

- https://github.com/elebumm/RedditVideoMakerBot — inspiration for the audio/caption/editing pattern;
  reading or reposting other people's stories requires appropriate rights.
- https://github.com/gyoridavid/short-video-maker — open-source TTS/captions/video pipeline;
  produces edited shorts, *not* fully generative moving-image footage.
- https://github.com/thewh1teagle/kokoro-onnx — separate optional local speech engine;
  verify weight and voice licenses for commercial use.
- https://github.com/lukerbs/pytoon — animation/lip-sync pattern for future advanced projects;
  not installed or executed.
- https://github.com/FFmpeg/FFmpeg — free rendering/transitions.

Please note: local installed software can be free, while platform eligibility, royalties, CPU/electricity,
hardware and seller fees still exist. YouTube and TikTok do not promise monetization; posting AI or
mass-produced material does not itself qualify for payouts. Do not use someone else's Reddit posts, videos,
copyrighted songs/gameplay or real person's face/voice without required rights. Label realistic synthetic
media according to destination platform rules, and don't create false firsthand testimonials.

## Real-world validation (7/14-day discipline)

1. Research a credible niche question and make an original story/quiz/tutorial video draft.
2. Let the court record a NOT GUILTY local draft verdict, then inspect artwork, narration and caption timing.
3. Owner authorizes account setup, uploads and complies with platform rules manually or through a separately
   authenticated authorized integration.
4. Capture real views, watch-time/completion, profile clicks, enquiries, and any legitimate sales;
   don't confuse estimates or private drafts with verified audience engagement.
5. Rework the hook, audience or format based on evidence; retire tested underperforming methods under existing
   7/14-day rules and choose a **different** method rather than endless cosmetic duplicates.

No automatic account login, publication, bulk cold email, paid API access or revenue report is included.
