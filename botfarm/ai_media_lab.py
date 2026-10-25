"""Operation Billion: free/local video finishing and transparent AI media research.

No paid APIs, marketplace publishing, implicit model installation, arbitrary code
execution, or network-dependent video generation. Only owner-approved drafts.
Optional owner-supplied media needs explicit commercial-use rights confirmation.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from .creator_website_wing import safe_text
from .workshop import atomic_text

RESEARCH_CATALOG = (
    {
        'name': 'zebbern/no-cost-ai',
        'url': 'https://github.com/zebbern/no-cost-ai',
        'kind': 'directory_not_an_AI_model',
        'use': 'Discover free media, chat, voice and API candidates',
        'gate': 'Verify actual price, authentication, output commercial rights, API access and rates before any use',
        'status': 'referenced_not_installed',
    },
    {
        'name': '12britz/awesome-free-models',
        'url': 'https://github.com/12britz/awesome-free-models',
        'kind': 'directory_not_an_AI_model',
        'use': 'Compare open-weight image/video models, free API tiers and local runtimes',
        'gate': 'Discard expiring trials, pay-as-you-go services and noncommercial-only media models',
        'status': 'referenced_not_installed',
    },
    {
        'name': 'Anil-matcha/Open-Generative-AI',
        'url': 'https://github.com/Anil-matcha/Open-Generative-AI',
        'kind': 'creative_studio_source',
        'use': 'Inspect workflow/interface patterns and local model support',
        'gate': 'Many advertised model actions depend on Muapi.ai and an API key; open-source interface DOES NOT mean free model inference',
        'status': 'referenced_not_installed',
    },
    {
        'name': 'ComfyUI',
        'url': 'https://github.com/Comfy-Org/ComfyUI',
        'kind': 'optional_local_generator',
        'use': 'Generate your own properly licensed AI stills/videos to import into this finishing pipeline',
        'gate': 'Check available GPU/RAM and checkpoint licensing, do not auto-download multi-GB models',
        'status': 'optional_external',
    },
    {
        'name': 'WanGP',
        'url': 'https://github.com/deepbeepmeep/Wan2GP',
        'kind': 'optional_local_generator',
        'use': 'Research low-VRAM paths to local diffusion/video, if hardware supports them',
        'gate': 'Community-license constraints and separate model licenses; some configurations still need a capable GPU',
        'status': 'optional_external',
    },
    {
        'name': 'LTX Desktop',
        'url': 'https://github.com/Lightricks/LTX-Desktop',
        'kind': 'optional_gpu_intensive_generator',
        'use': 'Higher-quality locally generated footage on powerful supported hardware',
        'gate': 'Official Windows recommendations include high NVIDIA VRAM and RAM; not promised to work on this HP laptop',
        'status': 'optional_external',
    },
    {
        'name': 'Piper current project',
        'url': 'https://github.com/OHF-Voice/piper1-gpl',
        'kind': 'optional_local_voice',
        'use': 'Generate narration locally using a separately installed and verified voice model',
        'gate': 'Review every voice model card and commercial-use rights; GPL source and model licenses differ',
        'status': 'optional_external',
    },
)


def report():
    return {
        'catalogued_sources': RESEARCH_CATALOG,
        'free_local_ready': {'ffmpeg': bool(shutil.which('ffmpeg')), 'python_builtin_finisher': True},
        'conditions': {
            'any_paid_api_called': False,
            'third_party_code_installed': False,
            'model_downloaded': False,
            'selling_account_connected': False,
            'automatic_publish': False,
            'AI_generated_footage_built_in': False,
            'quality_upgrade': 'CPU-friendly moving shots, fades and owner-supplied licensed narration or AI imagery',
        },
    }


def _sha256(path: Path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(65536), b''):
            h.update(block)
    return h.hexdigest()


def _run(args, timeout=180):
    proc = subprocess.run(args, stdin=subprocess.DEVNULL, capture_output=True, text=True,
                          timeout=timeout, check=False)
    if proc.returncode:
        raise RuntimeError('Local FFmpeg failed: ' + (proc.stderr or '')[-700:])


def _court_folder(folder: Path):
    folder = Path(folder).expanduser().resolve()
    if not folder.is_dir() or not (folder/'metadata.json').is_file():
        raise ValueError('Select an existing Operation Billion video draft folder with metadata.json')
    meta = json.loads((folder/'metadata.json').read_text(encoding='utf-8'))
    if meta.get('format') not in ('short', 'youtube') or meta.get('publishing') != 'OWNER REVIEW REQUIRED':
        raise ValueError('Only unpublished, owner-review-required video drafts may be polished')
    if not all((folder/f'scene_{i:02d}.png').is_file() for i in range(1,6)):
        raise ValueError('This draft must contain five original scene images')
    return folder, meta


def _validate_png(path: Path):
    if not path.is_file() or path.stat().st_size > 25_000_000:
        raise ValueError('Missing or oversized source PNG (maximum 25 MB per scene)')
    with path.open('rb') as stream:
        if stream.read(8) != b'\x89PNG\r\n\x1a\n':
            raise ValueError('Only actual PNG images may be imported')


def polish(folder, audio=None, images=None, rights_confirmed=False, width=540, fps=18):
    """Create a MOVING, faded MP4 from existing court-reviewed local draft.

    Optional external images/audio are user-supplied, with explicit permission.
    Originals and audit tables remain unchanged. Offline FFmpeg only.
    """
    ffmpeg = shutil.which('ffmpeg')
    if not ffmpeg:
        raise RuntimeError('FFmpeg is not installed or not on PATH; no MP4 created')
    folder, original_metadata = _court_folder(Path(folder))
    if width not in (270,540,720) or fps not in (12,18,24):
        raise ValueError('Use width 270, 540 or 720 and fps 12, 18 or 24')
    if audio or images:
        if not rights_confirmed:
            raise ValueError('Confirm you have commercial rights to optional images/audio using --rights-confirmed')
    if audio:
        audio = Path(audio).expanduser().resolve()
        if not audio.is_file() or audio.suffix.lower() not in ('.wav','.mp3','.m4a') or audio.stat().st_size>80_000_000:
            raise ValueError('Narration must be a local WAV, MP3, or M4A below 80 MB')
    if images:
        images = Path(images).expanduser().resolve()
        if not images.is_dir():
            raise ValueError('Optional AI image directory does not exist')
    portrait = original_metadata['format'] == 'short'
    w, h = (width, round(width*16/9)) if portrait else (round(width*16/9), width)
    if w % 2: w += 1
    if h % 2: h += 1
    duration = 3
    frame_count = duration * fps
    output_dir = folder/'polished'
    output_dir.mkdir(exist_ok=True)
    result_path = output_dir/'preview_polished.mp4'
    imported=[]
    sources=[]
    for i in range(1,6):
        input_path = (images/f'scene_{i:02d}.png') if images else (folder/f'scene_{i:02d}.png')
        _validate_png(input_path)
        sources.append(input_path)
        imported.append({'scene': i, 'source':str(input_path), 'sha256':_sha256(input_path)})
    # Temporary video clips live beside the output so ffmpeg concat can safely use relative paths.
    with tempfile.TemporaryDirectory(prefix='media_',dir=output_dir) as temp:
        temp_dir=Path(temp)
        clips=[]
        for i, source in enumerate(sources):
            clip=temp_dir/f'part_{i:02d}.mp4'
            direction=(1 if i%2==0 else -1)
            z='min(zoom+0.00075,1.10)' if direction==1 else 'max(zoom-0.00075,1.0)'
            # Begin zoom-out shots at 1.10 using in=1.10; alternate movement to avoid identical shots.
            zoom_args="z='"+z+"':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d="+str(frame_count)+':s='+str(w)+'x'+str(h)+':fps='+str(fps)
            vf=(f'scale={w+40}:{h+40},'+ ('zoompan=' + zoom_args) +
                f',fade=t=in:st=0:d=0.25,fade=t=out:st=2.7:d=0.3,format=yuv420p')
            cmd=[ffmpeg,'-hide_banner','-nostdin','-loglevel','error','-y',
                 '-loop','1','-framerate',str(fps),'-i',str(source),'-t',str(duration),
                 '-vf',vf,'-c:v','libx264','-preset','veryfast','-crf','24',
                 '-pix_fmt','yuv420p','-an',str(clip)]
            _run(cmd,timeout=180)
            clips.append(clip)
        concat=temp_dir/'concat.txt'
        concat.write_text(''.join(f"file 'part_{i:02d}.mp4'\n" for i in range(5)),encoding='utf-8')
        silent=temp_dir/'silent.mp4'
        _run([ffmpeg,'-hide_banner','-nostdin','-loglevel','error','-y','-f','concat','-safe','1',
              '-i',str(concat),'-c','copy',str(silent)],timeout=90)
        if audio:
            _run([ffmpeg,'-hide_banner','-nostdin','-loglevel','error','-y','-i',str(silent),
                  '-i',str(audio),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac',
                  '-af','loudnorm,apad','-t','15','-movflags','+faststart',str(result_path)],timeout=120)
        else:
            shutil.copy2(silent,result_path)
    if not result_path.is_file() or result_path.stat().st_size<3000:
        raise RuntimeError('Video creation did not produce a usable MP4')
    evidence={
        'created_utc':datetime.now(timezone.utc).isoformat(),
        'source_video_metadata_sha256':_sha256(folder/'metadata.json'),
        'source_images':imported,
        'source_narration_sha256':_sha256(audio) if audio else None,
        'rights_confirmed_by_owner_for_imported_media':bool(rights_confirmed) if audio or images else None,
        'render':{'format':'MP4','width':w,'height':h,'fps':fps,'duration_seconds':15,
                  'camera_motion':True,'fades':True,'narration_included':bool(audio)},
        'video_sha256':_sha256(result_path),
        'video_file':str(result_path),
        'generative_video_model_executed':False,
        'published':False,
        'platform_analytics_connected':False,
        'verified_income':0,
    }
    atomic_text(output_dir/'provenance.json',json.dumps(evidence,indent=2))
    atomic_text(output_dir/'CHECK_BEFORE_PUBLICATION.txt',
        'Review factual accuracy, captions, original media and voice licensing, platform rights, accessibility, visual quality and AI-media disclosure obligations.\n'
        'Do NOT publish automatically. Preview is NOT a proven profitable or AI-video-generation result.\n')
    return {'video':str(result_path),'bytes':result_path.stat().st_size,'motion':True,
            'voice_added':bool(audio),'ai_visuals_imported':bool(images),
            'published':False,'verified_sales':0,'provenance':str(output_dir/'provenance.json')}


def latest_draft(home):
    base=Path(home)/'output'/'expansion_wing'
    candidates=[]
    for kind in ('short','youtube'):
        root=base/kind
        if root.is_dir():
            for p in root.iterdir():
                if p.is_dir() and (p/'metadata.json').is_file():
                    candidates.append(p)
    if not candidates:
        raise ValueError('No video drafts yet. Run: py -3 -m botfarm video-demo --topic "Your topic" --ai')
    return max(candidates,key=lambda p:(p/'metadata.json').stat().st_mtime)
