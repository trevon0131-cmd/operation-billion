"""Opt-in, zero-purchase Hugging Face Gradio Space bridge for Operation Billion.

Standalone interface: py -m botfarm.cloud_video_hub doctor|inspect|render
Does not automatically log in, post media, buy inference credits or bypass quotas.
Supports one *reviewed* short image-to-video request daily across this machine.
Requires a running Hugging Face Space on shared ZeroGPU, not billable hardware.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

MAX_MP4_BYTES = 350_000_000
MAX_REFERENCE_BYTES = 20_000_000
SPACE_RE = re.compile(r"^[a-zA-Z0-9][\w.-]{0,80}/[a-zA-Z0-9][\w.-]{0,80}$")


def space_id(value):
    if not isinstance(value, str) or not SPACE_RE.fullmatch(value):
        raise ValueError('Supply a Hugging Face Space as owner/space-name, not a URL')
    return value


def read_space_metadata(space, *, opener=None):
    """Read official Hub metadata (only huggingface.co, never arbitrary URLs)."""
    space = space_id(space)
    url = 'https://huggingface.co/api/spaces/' + space
    fetch = opener or urllib.request.urlopen
    req = urllib.request.Request(url, headers={'User-Agent':'OperationBillion-CloudVideo/1.0'})
    try:
        with fetch(req, timeout=10) as rsp:
            data = json.load(rsp)
    except (OSError, ValueError, urllib.error.HTTPError) as exc:
        raise RuntimeError('Could not inspect official Hugging Face Space metadata') from exc
    if not isinstance(data, dict):
        raise RuntimeError('Invalid Hugging Face Space metadata')
    runtime = data.get('runtime') or {}
    if not isinstance(runtime, dict): runtime={}
    hardware = runtime.get('hardware') or {}
    if not isinstance(hardware, dict): hardware={}
    current = str(hardware.get('current') or '')
    stage = str(runtime.get('stage') or '')
    # Provider metadata is advisory; only known shared ZeroGPU identifiers are accepted.
    zerogpu = current.lower().startswith(('zero-', 'zerogpu')) or current.lower() == 'zero'
    return {'space':space,'hardware':current or 'UNKNOWN','stage':stage or 'UNKNOWN',
            'zero_gpu_verified':zerogpu, 'official_url':'https://huggingface.co/spaces/'+space}


def doctor(space=None):
    package=False
    try:
        import gradio_client  # noqa: F401
        package=True
    except ImportError: pass
    checks={'service':'Hugging Face public Gradio Space','python_client_available':package,
            'hf_token_present':bool(os.environ.get('HF_TOKEN')), 'ffprobe_available':bool(shutil.which('ffprobe')),
            'cost_policy':'ZeroGPU shared only; 1 submission per UTC day; no billable Inference Providers',
            'publishing_enabled':False,'automatic_account_creation':False}
    if space: checks['space']=read_space_metadata(space)
    return checks


def draft(path):
    path=Path(path).expanduser().resolve()
    if not path.is_dir(): raise ValueError('Draft folder does not exist')
    scenesfile=path/'scenes.json'; metafile=path/'metadata.json'
    if not scenesfile.is_file() or not metafile.is_file():
        raise ValueError('Expected an existing Operation Billion viral_studio draft with scenes.json and metadata.json')
    metadata=json.loads(metafile.read_text(encoding='utf-8'))
    if metadata.get('court_verdict')!='NOT GUILTY' or metadata.get('published') is not False:
        raise PermissionError('The existing court must approve an unpublished local draft')
    shots=json.loads(scenesfile.read_text(encoding='utf-8'))
    if not isinstance(shots,list) or len(shots)!=5 or any(not isinstance(s,str) for s in shots):
        raise ValueError('Five original scene scripts required')
    motionfile=path/'AI_MOTION_SHOTLIST.json'
    if not motionfile.is_file():
        from .ai_video_bridge import plan
        plan(path)
    motion=json.loads(motionfile.read_text(encoding='utf-8'))
    if not isinstance(motion,dict) or len(motion.get('shots',[]))!=5:
        raise ValueError('Five AI motion shotlist entries required')
    return path, motion


def _reserve(dataroot, space, scene, now=None):
    """One submission/day machine-wide. Durable reservation also prevents racing workers.

    An interrupted run keeps the reservation; no automatic retry that could consume quota.
    """
    when=now or datetime.now(timezone.utc)
    day=when.strftime('%Y-%m-%d')
    dataroot=Path(dataroot); dataroot.mkdir(parents=True,exist_ok=True)
    marker=dataroot/('hf_zerogpu_attempt_'+day+'.json')
    payload={'day_utc':day,'space':space,'scene':scene,'state':'reserved',
             'meaning':'submission attempted; do not retry automatically',
             'user_cost_authorization':'no purchases allowed'}
    try:
        with marker.open('x',encoding='utf-8') as f:
            json.dump(payload,f,indent=2)
    except FileExistsError as exc:
        raise RuntimeError('Daily free-video attempt already reserved. Do not bypass usage limits.') from exc
    return marker


def _local_video(candidate):
    if isinstance(candidate, (list,tuple)) and candidate:
        return _local_video(candidate[0])
    if isinstance(candidate, dict):
        for field in ('path','video','name'):
            if field in candidate: return _local_video(candidate[field])
    if not isinstance(candidate,str): raise RuntimeError('Generator did not return a local video file path')
    path=Path(candidate).expanduser().resolve()
    if not path.is_file() or path.suffix.lower() not in ('.mp4','.webm','.mov'):
        raise RuntimeError('Generator did not return a local playable video file')
    if path.stat().st_size<5000 or path.stat().st_size>MAX_MP4_BYTES:
        raise RuntimeError('Video output failed size validation')
    return path


def _validate_video(path):
    ffprobe=shutil.which('ffprobe')
    if not ffprobe: raise RuntimeError('ffprobe is required to validate generated motion')
    try:
        r=subprocess.run([ffprobe,'-v','error','-select_streams','v:0','-show_entries',
                          'stream=codec_type','-of','default=noprint_wrappers=1:nokey=1',str(path)],
                         text=True,capture_output=True,timeout=20)
    except (OSError,subprocess.TimeoutExpired) as exc:
        raise RuntimeError('Could not inspect generated video') from exc
    if r.returncode!=0 or 'video' not in r.stdout:
        raise RuntimeError('Returned file is not a valid video')


def inspect(space):
    meta=read_space_metadata(space)
    if not meta['zero_gpu_verified']:
        return {'space':meta,'api_inspection_skipped':True,
                'reason':'Not verified as shared ZeroGPU: no calls or billable inference permitted.'}
    try:
        from gradio_client import Client
    except ImportError as exc:
        raise RuntimeError('Install the optional free gradio_client package first') from exc
    token=os.environ.get('HF_TOKEN')
    client=Client(space, token=token or None)
    return {'space':meta,'api_information':client.view_api(print_info=False),
            'generation_run':False, 'published':False}


def render(folder,space,reference_image,scene=1,api_name='/generate_video',
           confirm_free=False,confirm_rights=False,confirm_submit=False,
           workdir=None,client_factory=None):
    if not all((confirm_free,confirm_rights,confirm_submit)):
        raise PermissionError('Requires --confirm-free --confirm-rights --submit: owner approval for ONE free attempt')
    if not isinstance(scene,int) or scene not in range(1,6): raise ValueError('Scene must be 1..5')
    if not api_name.startswith('/') or len(api_name)>90 or not re.fullmatch(r'/[a-zA-Z0-9_/-]+',api_name):
        raise ValueError('Invalid Gradio API endpoint')
    space=space_id(space)
    token=os.environ.get('HF_TOKEN')
    if not token:
        raise RuntimeError('Set HF_TOKEN locally via Windows environment or current PowerShell session; do not send it in chat')
    meta=read_space_metadata(space)
    if not meta['zero_gpu_verified'] or meta['stage'].upper()!='RUNNING':
        raise RuntimeError('Official Space metadata does not confirm RUNNING shared ZeroGPU. Refusing billable/unknown backends.')
    folder,shotlist=draft(folder)
    image=Path(reference_image).expanduser().resolve()
    if not image.is_file() or image.suffix.lower() not in ('.png','.jpg','.jpeg','.webp') or image.stat().st_size>MAX_REFERENCE_BYTES:
        raise ValueError('Supply an original reference image under 20 MB')
    if not shutil.which('ffprobe'):raise RuntimeError('Install FFmpeg ffprobe first')
    try:
        from gradio_client import Client, handle_file
    except ImportError as exc:
        if client_factory is None:
            raise RuntimeError('Install the optional free gradio_client in your existing voice environment') from exc
        Client=None;handle_file=lambda p:p
    # Reserve before calling API, preventing accidental high-frequency jobs and duplicate workers.
    dataroot=Path(workdir) if workdir is not None else next((p/'data' for p in folder.parents if (p/'botfarm').is_dir()), folder/'data')
    marker=_reserve(dataroot,space,scene)
    output=None
    try:
        factory=client_factory or Client
        client=factory(space,token=token)
        prompt=shotlist['shots'][scene-1]['prompt']
        # Six-input image-to-video Gradio interface. Sites may change schemas: run inspect first.
        # WAN777_VERIFIED_16_INPUT_ADAPTER
        # This exact Space's public app.py declares 16 Gradio inputs in this order.
        # Original 6-input adapter remains available for other compatible Spaces.
        if space == 'kulkas2pintu/wan777':
            if api_name != '/generate_video':
                raise ValueError('For wan777, use only /generate_video')
            # One owner-authorized, 2-second, 4-step video; never a paid API.
            # The existing RUNNING ZeroGPU / rights / court / daily limit checks remain in force.
            job = client.submit(
                handle_file(str(image)),  # input_image
                None,                     # last_image (optional)
                prompt,                   # original approved scene motion prompt
                4,                        # inference steps
                'blurry, deformed, static frame, unreadable details, duplicate characters',
                2.0,                      # clip length in seconds
                1.0, 1.0,                # guidance scales
                42, False,               # fixed seed, no randomization
                5,                        # video quality
                'UniPCMultistep',         # scheduler
                3.0,                     # flow shift
                16,                       # output FPS option
                True,                     # return viewable video
                False,                    # safe mode: off for lower resource reservation
                api_name='/generate_video',
            )
            result = job.result()
        else:
            result=client.predict(handle_file(str(image)),prompt,3.0,4,42,True,api_name=api_name)
        local=_local_video(result)
        _validate_video(local)
        dest=folder/'ai_motion_clips';dest.mkdir(exist_ok=True)
        final=dest/f'scene_{scene:02d}.mp4'
        if final.exists(): raise FileExistsError('Do not silently overwrite previously reviewed footage')
        tmp=dest/f'.scene_{scene:02d}.tmp.mp4'
        shutil.copyfile(local,tmp)
        tmp.replace(final)
        output={'scene':scene,'video':str(final),'bytes':final.stat().st_size,
                'sha256':hashlib.sha256(final.read_bytes()).hexdigest(),
                'provider':'Hugging Face public Gradio Space','space':space,
                'commercial_rights':'owner reviewed; verify the model/Space terms for actual use',
                'published':False,'verified_sales':0}
        (dest/f'scene_{scene:02d}.provenance.json').write_text(json.dumps(output,indent=2),encoding='utf-8')
        return output
    finally:
        # Keep the reservation even on failure: a request may have consumed remote quota.
        # Avoid deleting/retrying automatically.
        if output:
            try:
                state=json.loads(marker.read_text(encoding='utf-8'));state['state']='generated';
                marker.write_text(json.dumps(state,indent=2),encoding='utf-8')
            except (OSError,ValueError):pass


def main(argv=None):
    parser=argparse.ArgumentParser(description='Operation Billion cloud AI video connector (shared ZeroGPU only; no payments)')
    subs=parser.add_subparsers(dest='command',required=True)
    d=subs.add_parser('doctor');d.add_argument('--space')
    ins=subs.add_parser('inspect');ins.add_argument('--space',required=True)
    r=subs.add_parser('render');r.add_argument('--space',required=True);r.add_argument('--folder',required=True)
    r.add_argument('--image',required=True);r.add_argument('--scene',type=int,default=1);r.add_argument('--api-name',default='/generate_video')
    r.add_argument('--confirm-free',action='store_true');r.add_argument('--confirm-rights',action='store_true');r.add_argument('--submit',action='store_true')
    args=parser.parse_args(argv)
    try:
        if args.command=='doctor':result=doctor(args.space)
        elif args.command=='inspect':result=inspect(args.space)
        else:result=render(args.folder,args.space,args.image,scene=args.scene,api_name=args.api_name,
                           confirm_free=args.confirm_free,confirm_rights=args.confirm_rights,confirm_submit=args.submit)
        print(json.dumps(result,indent=2,default=str));return 0
    except Exception as exc:
        print('Cloud video request blocked or failed: '+str(exc),file=sys.stderr)
        return 1

if __name__=='__main__':
    raise SystemExit(main())
