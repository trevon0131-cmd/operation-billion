# Operation Billion v0.9.4 — REAL AI animation workflow ($0 software)

The existing v0.9.3 fruit-story video is a sequence of hand-drawn PNG images. It is **NOT** diffusion-based AI animation. This upgrade does not pretend otherwise. This bridge is specifically designed for genuine moving video clips generated in a separate **local** AI-video backend.

## Verified GitHub research sources

- [ComfyUI](https://github.com/Comfy-Org/ComfyUI) — visual generation backend with localhost API. Free/open-source engine; some available partner models are paid; use local open-weight models only.
- [Wan 2.2](https://github.com/Wan-Video/Wan2.2) — real generative text-to-video/image-to-video models. Apache 2.0 software/model terms for eligible models; review the exact checkpoint license independently. ComfyUI-offloaded quantized workflows can target lower-VRAM GPUs, but system RAM, speed, checkpoint sizes and node versions matter. No model is bundled.
- [FramePack](https://github.com/lllyasviel/FramePack) — high-quality moving video from a reference image, but official repository specifies an NVIDIA RTX 30/40/50 series GPU with at least 6 GB VRAM. Do not install if your laptop lacks supported hardware.
- [FasterLivePortrait](https://github.com/warmshao/FasterLivePortrait) — can animate faces/head movement and accept audio-driving integrations. **IMPORTANT**: some InsightFace pretrained models are noncommercial; don't sell their outputs without resolving licenses/replacing those components.

No paid API required to operate this bridge. It will not automatically download video models or unknown GitHub code. GPU, electricity, storage, commercial media rights, and seller fees are still real constraints.

## Step 1 — Diagnose your laptop

In the original VS Code `zero_cost_bot_farm` terminal:

```powershell
py -3 -m botfarm ai-video-doctor
```

This reports *measured* NVIDIA VRAM where `nvidia-smi` is available, actual Windows physical RAM, and whether ComfyUI is responding on `127.0.0.1:8188`. If NVIDIA is not detected, that does **not** prove your laptop lacks AMD/Intel GPU; check Task Manager > Performance > GPU. Do not download massive video model weights until you know the actual GPU model, RAM and free disk space.

A CPU-only HP can compose and narrate videos with FFmpeg/Kokoro, but running a diffusion video model fast enough for repeatable viral-video generation is unlikely. There is no verified unlimited free hosted video generation service included.

## Step 2 — Generate an original approved draft and shotlist

```powershell
py -3 -m botfarm viral-studio --format fruit-story --topic "The banana who lied to a strawberry" --narrate --render
```

Copy the output `folder` path from the command, then:

```powershell
$draft = 'PASTE_FULL_OUTPUT_FOLDER_PATH_HERE'
py -3 -m botfarm ai-video-plan --folder $draft
```

Read `AI_MOTION_SHOTLIST.json` in `$draft`. It has five original, character-consistent prompts for **actual moving video**, avoiding baked text, with a shot number and suggested name such as `scene_01.mp4`.

## Step 3 — Run a compatible actual local video model

1. Download ComfyUI **Desktop** from the official ComfyUI GitHub project or the ComfyUI site. Use the variant compatible with your hardware. It is installed independently from Operation Billion.
2. Install and configure a supported Wan image-to-video or text-to-video workflow from ComfyUI's official template browser. Check that all model checkpoints are present and commercial use is permitted. Avoid automatically installing unrelated extensions from unreviewed repositories.
3. Start the local ComfyUI API on `http://127.0.0.1:8188` (most standard ComfyUI desktop installations use this localhost port). See `ai-video-doctor` for connection status.
4. Manually load your approved API-format workflow, select the video generation settings and a video **save** node that produces `.mp4` files, and export it as **API format JSON**. This cannot be substituted with ordinary UI-format JSON.
5. In the JSON, identify the numeric ID for the positive text prompt node (a `class_type` such as `CLIPTextEncode`, whose `inputs.text` is a string). All other workflow nodes, model names, video savers, duration, reference image, sampler, VAE, and seeds are still defined in YOUR workflow; this bridge changes ONLY that one text field. For consistent fruit characters, create/reuse a licensed visual reference and matching seeds across scenes when your workflow supports it.

**Important:** If your GPU is unsupported or insufficient, skip this step rather than installing several gigabytes of models that will not work.

## Step 4 — Queue real AI motion clips from your saved workflow

Replace the following example paths/IDs with real ones. The command sends data **only** to localhost ComfyUI, never to a cloud API. It does not automatically enable new models or spend money.

```powershell
py -3 -m botfarm ai-video-comfy --folder $draft --workflow 'C:\path\to\your_api_workflow.json' --text-node '6' --scene 1
```

The response contains a `prompt_id`. Monitor the ComfyUI local queue, then retrieve the completed movie:

```powershell
py -3 -m botfarm ai-video-comfy-fetch --folder $draft --scene 1 --prompt-id 'PASTE_ID_RETURNED_ABOVE'
```

Repeat for scenes 2–5. The fetch tool only accepts job IDs previously submitted from this draft, and only retrieves a bounded movie from localhost. Different ComfyUI video saver extensions vary: if the tool says no MP4/MOV/WebM found, configure a supported video-saving node and retry. You can also manually export five clips to `$draft\ai_motion_clips\scene_01.mp4` through `scene_05.mp4`.

## Step 5 — Assemble five REAL AI moving clips with Kokoro narration

Once all five reviewed clips exist, run:

```powershell
py -3 -m botfarm ai-video-assemble --folder $draft --rights-confirmed --width 540
```

This **requires five actual playable moving video files**; it cannot use the old PNG slides, and refuses to run if one is missing. It joins and crops your five videos to vertical 9:16 and, if the draft has `narration.wav`, mixes that audio. It produces `AI_MOTION_RENDER.mp4` and a provenance file. The video and narration are still local, unpublished, and have no verified earnings.

`--rights-confirmed` is your confirmation of commercial-use rights. Copyrighted characters, copied Reddit stories, other people's voices/faces and unlicensed music must not be used.

## Realistic expectations

- Free/open-source generative video is possible on suitable hardware, but it is compute-intensive and not necessarily photorealistic in every render.
- If your laptop has only integrated graphics or no useful discrete GPU, local text/image-to-video will be prohibitively slow for routine operation. Do not pretend the FFmpeg motion-graphics fallback is cinematic AI animation.
- Start with a few 4-second clips rather than asking for one perfect 60-second AI movie; 5 short clips are easier to rerender and edit.
- LivePortrait/FasterLivePortrait and standalone image-to-video checkpoints have distinct licenses and dependencies. Review the exact weights and face-detection models before selling generated media.
- AI-generated content must still be truthful, original, and compliant with YouTube/TikTok labeling and monetization rules. Publishing/accounts still require user authorization.
