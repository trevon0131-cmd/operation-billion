# Operation Billion: Free AI video sources and CPU video finishing

**This update is a local, no-subscription creative assistant, not an unlimited free cloud video generation account.** Its built-in motion finisher renders an original 15-second MP4 with per-scene motion, fades, and optional owner-provided licensed images and narration. It does not independently create photorealistic moving people or scenes. FFmpeg must be installed on the PC; the user has already confirmed it works on Windows.

## Three GitHub sources submitted by the owner

1. https://github.com/zebbern/no-cost-ai — **curated directory**, not downloadable video AI. Examine its image/video entries for local execution, no-credit-card usage, commercial rights, API support, and current availability. Free hosted quotas can end.
2. https://github.com/12britz/awesome-free-models — **curated directory** of open-weight models, free tiers, and APIs. Some models have noncommercial licenses, inadequate RAM/VRAM requirements, or temporary trial credits. No URL automatically becomes executable.
3. https://github.com/Anil-matcha/Open-Generative-AI — **open-source creative studio frontend**. It advertises many models, but its default Muapi.ai backend requires an API key; the interface being free does not make Sora/Veo/Kling inference free. Local backends (sd.cpp/Wan2GP) require separate compatible model downloads and hardware.

## Paths to better media without paid APIs

- **CPU today:** Ollama for original scripts + Operation Billion bitmap scenes + FFmpeg motion/fades. The results are motion graphics, not full cinematic AI footage.
- **With separately installed local image models:** generate *licensed* original image backgrounds or scenes in ComfyUI, sd.cpp or another authorized program, then import PNG stills with `--images` and `--rights-confirmed`. These are inputs only; this update never installs or triggers the heavy models.
- **With separately installed licensed local voice models:** generate your own WAV/MP3 in Piper or Kokoro and import with `--narration` and `--rights-confirmed`. Check the voice model license separately from the app license. The old `rhasspy/piper` project is archived; the maintained codebase is `https://github.com/OHF-Voice/piper1-gpl`.
- **With an appropriate dedicated GPU:** review WanGP and LTX Desktop. Windows local LTX video may require high VRAM and RAM; do not promise this works on a laptop merely because it has 512 GB of storage.
- **For existing permitted clips:** freely available editors include Kdenlive, Shotcut, FFmpeg. Stock images/video licenses require separate verification; do not assume everything labelled free permits resale.

## Using the new tools in your existing VS Code folder

To research supported paths and requirements:

```powershell
py -3 -m botfarm media-doctor
```

To make a local court-approved sample on a **specific** topic:

```powershell
py -3 -m botfarm video-demo --topic "How to save for college" --ai
```

To render the newest video using local FFmpeg with camera movement and fades:

```powershell
py -3 -m botfarm video-polish
```

The resulting video lives in `output/expansion_wing/short/<draft-id>/polished/preview_polished.mp4`. It always remains **unpublished**.

To import five licensed original AI images from a folder, name them `scene_01.png` through `scene_05.png` and use:

```powershell
py -3 -m botfarm video-polish --images "C:\YourOriginalAIImages" --rights-confirmed
```

To mix an original or licensed voice recording in:

```powershell
py -3 -m botfarm video-polish --narration "C:\YourFiles\my_narration.wav" --rights-confirmed
```

For a low-power laptop, `--width 270` reduces rendering workload. `--width 720` improves rendering resolution at higher CPU cost. All rendering is finite and offline, and this feature preserves the original scene PNGs and existing database history.

## Rules

- No random cloning, executing, or installing GitHub code.
- No hidden calls to paid APIs or automatic subscription signup.
- No publication, outreach, account access, or payment setup.
- Imported audio/images require an affirmative commercial-rights confirmation; never impersonate someone or clone a voice without authorization.
- Never fabricate trends, sales, income, view counts, or endorsements.
- Check fact accuracy, repeated-video quality, media rights, AI disclosure, and platform monetization requirements before any external action.
- If a model is not suitable for the hardware or requires payment, **mark it unavailable rather than claiming it is installed**.
