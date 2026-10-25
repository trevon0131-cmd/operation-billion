"""Optional real-motion AI video bridge. Never silently substitutes slides for diffusion video.

Use local ComfyUI to render genuine image/video-model frames via an owner-supplied
API-format workflow, or import five owner-reviewed video clips. No model, external
binary or paid service is downloaded or run by this module.
"""
from __future__ import annotations

import ctypes
import hashlib
import json
import re
import shutil
import subprocess
import time
import urllib.parse
import urllib.request
from pathlib import Path

VIDEO_EXTS = {'.mp4','.mov','.webm','.mkv'}
MAX_CLIP_BYTES = 350_000_000
MAX_WORKFLOW_BYTES = 1_000_000

TOOLS = [
    {'name':'ComfyUI','url':'https://github.com/Comfy-Org/ComfyUI','use':'Local video-model backend; supports API-format workflows','status':'not_bundled'},
    {'name':'Wan 2.2','url':'https://github.com/Wan-Video/Wan2.2','use':'Real text-to-video and image-to-video diffusion (GPU required for practical use)','status':'not_bundled'},
    {'name':'FramePack','url':'https://github.com/lllyasviel/FramePack','use':'Long image-conditioned AI motion; NVIDIA RTX 30/40/50, >= 6GB VRAM','status':'not_bundled'},
    {'name':'FasterLivePortrait','url':'https://github.com/warmshao/FasterLivePortrait','use':'Face and audio-driven animation; check model, detection and commercial licenses','status':'not_bundled'},
]

def _run(cmd, limit=10):
    try:
        p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,encoding='utf-8',errors='replace',timeout=limit,check=False)
        return p.stdout.strip() if p.returncode==0 else ''
    except (OSError,subprocess.TimeoutExpired):
        return ''


def hardware():
    """Return measured resources; do not guess from storage size or CPU Ollama logs."""
    result={'gpu_detected':False,'gpu':[],'system_ram_gb':None,'ffmpeg':bool(shutil.which('ffmpeg')),
            'ffprobe':bool(shutil.which('ffprobe')),'comfyui_url':'http://127.0.0.1:8188',
            'real_ai_video_model_installed':'NOT_VERIFIED','original_fruit_video_generator':'NOT_BUILT_IN',
            'paid_api_required':False,'model_auto_installed':False}
    if hasattr(ctypes,'windll'):
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_=[('dwLength',ctypes.c_ulong),('dwMemoryLoad',ctypes.c_ulong),('ullTotalPhys',ctypes.c_ulonglong),('ullAvailPhys',ctypes.c_ulonglong),('ullTotalPageFile',ctypes.c_ulonglong),('ullAvailPageFile',ctypes.c_ulonglong),('ullTotalVirtual',ctypes.c_ulonglong),('ullAvailVirtual',ctypes.c_ulonglong),('ullAvailExtendedVirtual',ctypes.c_ulonglong)]
        try:
            m=MEMORYSTATUSEX();m.dwLength=ctypes.sizeof(m)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)):
                result['system_ram_gb']=round(m.ullTotalPhys/1024**3,1)
        except Exception:pass
    raw=_run(['nvidia-smi','--query-gpu=name,memory.total','--format=csv,noheader,nounits'])
    for line in raw.splitlines()[:8]:
        pieces=line.rsplit(',',1)
        if len(pieces)==2 and pieces[1].strip().isdigit():
            item={'name':pieces[0].strip(),'vram_mb':int(pieces[1].strip()),'source':'nvidia-smi'}
            result['gpu'].append(item)
    result['gpu_detected']=bool(result['gpu'])
    if not result['gpu']:
        result['note']='NVIDIA GPU not detected by nvidia-smi; may be Intel/AMD or missing drivers. GPU capability is UNKNOWN, not necessarily absent.'
    else:
        vram=max(x['vram_mb'] for x in result['gpu'])
        if vram>=8192:
            result['recommended_next']='Try a supported quantized Wan2.2 ComfyUI workflow after checking RAM, model license and disk use.'
        elif vram>=6144:
            result['recommended_next']='Check official FramePack NVIDIA requirements or quantized low-VRAM workflows; expect slow renders.'
        else:
            result['recommended_next']='Heavy diffusion video likely impractical locally; do not automatically install massive model weights.'
    return result


def _folder(path):
    path=Path(path).expanduser().resolve()
    if not path.is_dir() or not (path/'scenes.json').is_file() or not (path/'metadata.json').is_file():
        raise ValueError('Choose an EXISTING viral_studio output folder with scenes.json and metadata.json')
    meta=json.loads((path/'metadata.json').read_text(encoding='utf-8'))
    if meta.get('court_verdict')!='NOT GUILTY' or meta.get('published') is not False:
        raise PermissionError('Video must be an approved, unpublished local draft')
    scenes=json.loads((path/'scenes.json').read_text(encoding='utf-8'))
    if not isinstance(scenes,list) or len(scenes)!=5 or any(not isinstance(s,str) for s in scenes):
        raise ValueError('Five saved scene lines are required')
    return path,meta,scenes


def plan(folder):
    folder,meta,scenes=_folder(folder)
    topic=meta.get('topic','original short story')
    fruit=meta.get('format')=='fruit-story'
    continuity=(
        'same original anthropomorphic strawberry with tiny green leaves and expressive eyes, '
        'same tall smiling yellow banana, same round orange character; bright cinematic 3D animation; '
        'coherent character shapes and costumes, no logos, no trademarks'
        if fruit else 'consistent original characters, cinematic composition, no brands or copyrighted likenesses'
    )
    shots=[]
    for index,scene in enumerate(scenes,1):
        mood=['suspenseful hook','character entrance','surprising action','emotional reveal','satisfying resolution'][index-1]
        shots.append({'scene':index,'line':scene,'prompt':(
            f'Vertical 9:16 original animated short, {continuity}. Scene {index}: {scene} '
            f'Mood: {mood}. Characters move their heads, blink, walk and interact naturally. '
            'Smooth physically coherent motion, expressive faces, camera tracking, cinematic lighting, '
            'high-quality detailed environment, 24 fps, no subtitles or text baked into footage.'),
            'negative_prompt':'static image, slideshow, frozen pose, melted faces, extra limbs, watermark, low quality, text artifacts',
            'recommended_seconds':4,'generation':'requires installed real AI video model, not part of the ZIP',
            'expected_file':f'scene_{index:02d}.mp4'})
    data={'topic':topic,'format':meta.get('format'),'source_folder':str(folder),'character_consistency':continuity,
          'shots':shots,'backend_choices':TOOLS,'source':'existing court-approved original local draft',
          'work_remaining':['Use an actual local video model to generate five distinct moving clips',
                            'Review commercial rights and footage originality','Assemble with existing Kokoro narration'],
          'no_video_generation_claimed':True,'no_external_publishing':True}
    target=folder/'AI_MOTION_SHOTLIST.json'
    target.write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8')
    (folder/'AI_VIDEO_README.txt').write_text(
        'These are PROMPTS, not rendered AI video. Install a suitable licensed video model independently.\n'
        'Use a consistent reference image/seed for the fruit cast across all scenes.\n'
        'Save 5 genuine moving clips in ai_motion_clips as scene_01.mp4 through scene_05.mp4.\n'
        'Run python -m botfarm ai-video-assemble --folder "<draft folder>" --rights-confirmed.\n'
        'If you have a locally running ComfyUI, export your workflow in API format and use ai-video-comfy for each shot.\n'
        'Do not call this feature an AI generated video until actual moving footage has been produced.\n',encoding='utf-8')
    return {'shotlist':str(target),'shots':len(shots),'real_motion_created':False,'model_auto_installed':False,
            'next':'Generate five actual clips with ComfyUI/Wan or FramePack; then run ai-video-assemble.'}


def _duration(path):
    out=_run(['ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',str(path)],limit=15)
    try:
        n=float(out)
        return n if 0.1 <= n <= 1200 else 0
    except ValueError:return 0


def _clips(folder, clip_dir):
    folder=Path(folder).resolve();clip_dir=Path(clip_dir).resolve()
    paths=[]
    if not clip_dir.is_dir():raise FileNotFoundError(f'Clip folder is missing: {clip_dir}')
    for i in range(1,6):
        found=[clip_dir/f'scene_{i:02d}{s}' for s in sorted(VIDEO_EXTS) if (clip_dir/f'scene_{i:02d}{s}').is_file()]
        if len(found)!=1:raise ValueError(f'Expected ONE genuine motion clip named scene_{i:02d}.mp4/.mov/.mkv/.webm')
        p=found[0]
        if p.stat().st_size>MAX_CLIP_BYTES:raise ValueError('Motion clip exceeds 350MB safety bound')
        if _duration(p)==0:raise ValueError(f'Clip is not a playable video: {p.name}')
        paths.append(p)
    return paths


def assemble(folder,clips=None,rights_confirmed=False,width=540):
    folder,meta,scenes=_folder(folder)
    if not rights_confirmed:raise PermissionError('Confirm you have rights for ALL imported footage with --rights-confirmed')
    if width not in (360,540,720):raise ValueError('Unsupported width')
    if not (shutil.which('ffmpeg') and shutil.which('ffprobe')):raise RuntimeError('FFmpeg and ffprobe required')
    clip_dir=Path(clips).expanduser().resolve() if clips else (folder/'ai_motion_clips')
    paths=_clips(folder,clip_dir)
    audio=folder/'narration.wav';has_audio=audio.is_file() and _duration(audio)>0
    total=max(20,(_duration(audio)+0.6) if has_audio else 20)
    scene_sec=total/5
    out=folder/'AI_MOTION_RENDER.mp4'
    args=[shutil.which('ffmpeg'),'-hide_banner','-nostdin','-loglevel','error','-y']
    for p in paths:
        args+=['-stream_loop','-1','-i',str(p)]
    if has_audio:args+=['-i',str(audio)]
    filters=[]
    height=width*16//9
    for i in range(5):
        filters.append(f'[{i}:v]fps=24,scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},setsar=1,trim=duration={scene_sec:.3f},setpts=PTS-STARTPTS,format=yuv420p[v{i}]')
    filters.append(''.join(f'[v{i}]' for i in range(5))+'concat=n=5:v=1:a=0[vout]')
    args+=['-filter_complex',';'.join(filters),'-map','[vout]']
    if has_audio:args+=['-map','5:a:0','-af','apad','-c:a','aac','-b:a','128k']
    args+=['-t',f'{total:.3f}','-c:v','libx264','-preset','veryfast','-crf','23','-pix_fmt','yuv420p','-movflags','+faststart',str(out)]
    try:
        p=subprocess.run(args,stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=240)
    except subprocess.TimeoutExpired as exc:raise RuntimeError('FFmpeg clip assembly took too long') from exc
    if p.returncode or not out.is_file() or out.stat().st_size<4000:
        raise RuntimeError('Could not assemble AI motion clips: '+p.stderr[-1000:])
    hashes={x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in paths}
    prov={'assembled_from_owner_supplied_video':True,'ai_origin_not_independently_verified':True,
          'real_motion_video_files':hashes,'source_draft':str(folder),'rights_confirmed_by_user':rights_confirmed,
          'narration_included':has_audio,'publishing':False,'recorded_sales':0,'output':str(out)}
    (folder/'AI_MOTION_PROVENANCE.json').write_text(json.dumps(prov,indent=2),encoding='utf-8')
    return {'rendered':True,'video':str(out),'seconds':round(total,2),'bytes':out.stat().st_size,
            'voice_added':has_audio,'real_motion_clips_used':5,'published':False,'verified_sales':0}


def comfy_status():
    try:
        with urllib.request.urlopen('http://127.0.0.1:8188/system_stats',timeout=2) as rsp:
            data=json.load(rsp)
        return {'running':True,'endpoint':'http://127.0.0.1:8188','stats':data}
    except (OSError,ValueError):
        return {'running':False,'endpoint':'http://127.0.0.1:8188','hint':'Start your locally installed ComfyUI first; no paid API needed.'}


def comfy_queue(folder,workflow,node_id,scene=1):
    """Queue ONE owner-reviewed ComfyUI API workflow locally, replacing selected text prompt.
    The workflow must contain all downloaded model nodes and a video saver configured by the owner.
    Submission cannot claim that diffusion actually finished rendering.
    """
    folder,meta,scenes=_folder(folder)
    if not 1<=scene<=5:raise ValueError('Scene index must be 1..5')
    src=Path(workflow).expanduser().resolve()
    if not src.is_file() or src.stat().st_size>MAX_WORKFLOW_BYTES:
        raise ValueError('Supply a reviewed ComfyUI workflow JSON file under 1MB (API format)')
    content=json.loads(src.read_text(encoding='utf-8'))
    if not isinstance(content,dict) or not isinstance(content.get(str(node_id)),dict):
        raise ValueError('Node ID not found in API-format workflow')
    node=content[str(node_id)].get('inputs')
    if not isinstance(node,dict) or not isinstance(node.get('text'),str):
        raise ValueError('Selected ComfyUI prompt node must have an inputs.text field')
    shotlist=json.loads((folder/'AI_MOTION_SHOTLIST.json').read_text(encoding='utf-8')) if (folder/'AI_MOTION_SHOTLIST.json').exists() else None
    if shotlist is None:
        plan(folder);shotlist=json.loads((folder/'AI_MOTION_SHOTLIST.json').read_text(encoding='utf-8'))
    node['text']=shotlist['shots'][scene-1]['prompt']
    payload=json.dumps({'prompt':content,'client_id':'operation_billion_local'}).encode('utf-8')
    request=urllib.request.Request('http://127.0.0.1:8188/prompt',data=payload,headers={'Content-Type':'application/json'},method='POST')
    try:
        with urllib.request.urlopen(request,timeout=15) as rsp:reply=json.loads(rsp.read(50_000))
    except (OSError,ValueError) as exc:
        raise RuntimeError('Local ComfyUI rejected workflow; check running server, installed models and API-format export: '+str(exc)[:260]) from exc
    if not isinstance(reply,dict) or not isinstance(reply.get('prompt_id'),str):
        raise RuntimeError('ComfyUI did not return a prompt_id')
    logfile=folder/'COMFYUI_QUEUED_JOBS.jsonl'
    with logfile.open('a',encoding='utf-8') as f:
        f.write(json.dumps({'scene':scene,'prompt_id':reply['prompt_id'],'workflow':src.name})+'\n')
    return {'submitted':True,'scene':scene,'prompt_id':reply['prompt_id'],
            'generation_finished':False,'no_model_downloaded':True,'publishing':False,
            'next':'Monitor ComfyUI queue, review generated video, export scene_%02d.mp4 into ai_motion_clips.'%scene}


def comfy_fetch(folder,scene,prompt_id):
    """Fetch a finished movie ONLY from a local ComfyUI job (no remote model APIs)."""
    folder,_,_=_folder(folder)
    if not 1 <= scene <= 5:raise ValueError('Scene must be 1..5')
    if not re.fullmatch('[A-Za-z0-9-]{8,100}',prompt_id):raise ValueError('Invalid ComfyUI prompt ID')
    journal=folder/'COMFYUI_QUEUED_JOBS.jsonl'
    if not journal.is_file():raise ValueError('No owner-queued ComfyUI jobs for this draft')
    allowed=False
    for line in journal.read_text(encoding='utf-8').splitlines():
        try:
            job=json.loads(line)
            if job.get('scene')==scene and job.get('prompt_id')==prompt_id:allowed=True
        except ValueError:continue
    if not allowed:raise PermissionError('This prompt ID was not queued by this draft and scene')
    base='http://127.0.0.1:8188'
    try:
        with urllib.request.urlopen(base+'/history/'+prompt_id,timeout=10) as response:
            history=json.loads(response.read(2_000_000))
    except (OSError,ValueError) as exc:raise RuntimeError('Cannot read local ComfyUI job status') from exc
    job=history.get(prompt_id,{}) if isinstance(history,dict) else {}
    if not isinstance(job,dict) or not job.get('outputs'):
        return {'ready':False,'message':'ComfyUI job is unfinished or has no saved output'}
    video=None
    for item in job['outputs'].values():
        if not isinstance(item,dict):continue
        for key in ('videos','gifs','images'):
            for asset in item.get(key,[]):
                if isinstance(asset,dict) and Path(asset.get('filename','')).suffix.lower() in VIDEO_EXTS:
                    video=asset;break
            if video:break
        if video:break
    if video is None:return {'ready':False,'message':'No MP4/MOV/WebM output found. Configure a video saver node in ComfyUI.'}
    name=video.get('filename','')
    sub=video.get('subfolder','')
    kind=video.get('type','output')
    if not isinstance(name,str) or len(name)>255 or '/' in name or '\\' in name or name in ('.','..'):
        raise ValueError('Unsafe output filename from ComfyUI')
    if not isinstance(sub,str) or '..' in sub or len(sub)>200 or '\\' in sub:raise ValueError('Unsafe output folder')
    if kind not in ('output','temp'):raise ValueError('Unapproved ComfyUI result type')
    qs=urllib.parse.urlencode({'filename':name,'subfolder':sub,'type':kind})
    outdir=folder/'ai_motion_clips';outdir.mkdir(exist_ok=True)
    ext=Path(name).suffix.lower()
    out=outdir/f'scene_{scene:02d}{ext}'
    tmp=out.with_suffix(out.suffix+'.part')
    size=0
    try:
        with urllib.request.urlopen(base+'/view?'+qs,timeout=45) as source, tmp.open('wb') as target:
            while True:
                chunk=source.read(256*1024)
                if not chunk:break
                size+=len(chunk)
                if size>MAX_CLIP_BYTES:raise ValueError('Generated clip exceeds 350MB')
                target.write(chunk)
        if size<2048:raise ValueError('ComfyUI result is too small to be a valid movie')
        tmp.replace(out)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise
    return {'ready':True,'saved':str(out),'bytes':size,'published':False,'verified_sales':0,
            'note':'Review visual quality and licenses before stitching; no sales or publishing occurred.'}
