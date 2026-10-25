"""Zero-upfront, LOCAL original short-form video production lab.

Offers formats inspired by popular *editing styles*, never downloads Reddit posts,
private media, or paid model assets. The script and illustrations are original.
No upload, email, API key, paid model, or earnings claim is made.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
import struct
import subprocess
import sys
import textwrap
import urllib.error
import urllib.request
import wave
import zlib
from datetime import datetime, timezone
from pathlib import Path

from .court import Proposal, adjudicate
from .storage import Store
from .creator_website_wing import FONT

FORMATS = {
    "fruit-story": "Original talking fruit/food character storyboards with lively illustrated scenes",
    "fictional-reddit": "Original fictional first-person story with Reddit-style reading layout; NOT a copied Reddit post",
    "quick-quiz": "Original short quiz/puzzle with question, countdown, answer and explanation",
    "micro-drama": "Original five-beat cinematic fiction: hook, conflict, twist, resolution",
    "tips": "Useful brief explainer, checklist or mini-tutorial on a selected topic",
}

RESEARCH_REFERENCES = [
    {"name":"RedditVideoMakerBot", "url":"https://github.com/elebumm/RedditVideoMakerBot",
     "note":"Study the narration/caption/video assembly pattern; never reproduce posts without rights"},
    {"name":"Short Video Maker", "url":"https://github.com/gyoridavid/short-video-maker",
     "note":"Local speech, captions and stock-video assembly; separately review media licensing"},
    {"name":"Kokoro ONNX", "url":"https://github.com/thewh1teagle/kokoro-onnx",
     "note":"Optional local CPU narrator in an existing separate Python 3.12 environment"},
    {"name":"PyToon", "url":"https://github.com/lukerbs/pytoon",
     "note":"Research audio-reactive cartoon animation; not installed or imported"},
    {"name":"FFmpeg", "url":"https://github.com/FFmpeg/FFmpeg",
     "note":"Local video rendering with movement, fades and MP4; detected on PATH"},
]


def _clean(text, limit=110):
    if not isinstance(text, str):
        raise ValueError('Topic must be text')
    value=' '.join(text.split())
    if not 3 <= len(value) <= limit or any(ord(c)<32 for c in value):
        raise ValueError('Enter a topic between 3 and 110 printable characters')
    return value


def _script_fallback(fmt, topic):
    """Every frame is original and changes with topic; a fallback is not marketed as AI."""
    topic = topic.strip().rstrip('.!?')
    if fmt == 'fruit-story':
        return [
            f'On the kitchen counter, a curious strawberry spotted {topic}.',
            'A dramatic banana warned everyone that something was going wrong.',
            'The orange had a clever idea, but nobody wanted to listen.',
            'Then the strawberry discovered what everyone had misunderstood.',
            'The fruit friends solved the mystery together. What would you do?',
        ]
    if fmt == 'fictional-reddit':
        return [
            f'FICTIONAL STORY: I never expected this to happen with {topic}.',
            'At first I thought the situation was just a misunderstanding.',
            'Then a small detail completely changed what I believed.',
            'I asked one question and finally got an honest answer.',
            'Here is what I learned. Would you have handled it differently?',
        ]
    if fmt == 'quick-quiz':
        return [
            f'QUICK QUIZ: What do you really know about {topic}?',
            'Here is a tricky question. Think before you answer.',
            'Three... two... one... lock in your best guess.',
            f'The key is understanding the real basics of {topic}.',
            'Tell us your answer, then check a trustworthy source to learn more.',
        ]
    if fmt == 'micro-drama':
        return [
            f'An ordinary day changed when I discovered {topic}.',
            'One tiny decision created a problem no one expected.',
            'Just as everything seemed lost, a new clue appeared.',
            'It turned out the whole situation had been misunderstood.',
            'The ending changed how everyone thought about the problem.',
        ]
    return [
        f'Here is a useful starting point for {topic}.',
        'First, identify one real problem you want to solve.',
        'Next, find a free tool and test one small example.',
        'Check the results and improve one thing at a time.',
        'Save the steps that worked. Which one will you try?',
    ]


def _local_ai(fmt, topic, model='qwen3:8b', timeout=240):
    """Bounded direct localhost Ollama request. No remote paid API or downloaded code."""
    if not re.fullmatch(r'[A-Za-z0-9_.:-]{2,80}', model):
        raise ValueError('Invalid local Ollama model name')
    task = ('Write exactly five lines for a SHORT ORIGINAL video story. '
            'Each line: 7-17 spoken words, complete sentence. '
            'Line 1 an immediate hook; lines 2-4 develop a coherent story; line 5 meaningful payoff. '
            'No real Reddit posts, personal information, celebrity likenesses, misleading facts, '
            'copyrighted characters, earnings promises, quotes, or markdown. '
            f'Video style: {fmt}. Topic: {topic}. Return only five lines.')
    payload = json.dumps({'model':model,'prompt':task,'stream':False,'think':False,
                          'options':{'num_predict':230,'temperature':0.8}}).encode('utf-8')
    req=urllib.request.Request('http://127.0.0.1:11434/api/generate',data=payload,
                               headers={'Content-Type':'application/json'},method='POST')
    try:
        with urllib.request.urlopen(req,timeout=timeout) as response:
            raw=response.read(64_000)
    except (OSError,TimeoutError,urllib.error.URLError) as exc:
        return None, 'Local Ollama unavailable: '+str(exc)[:120]
    try:
        result=json.loads(raw.decode('utf-8'))['response']
        lines=[re.sub(r'^\s*(?:[-*]|\d+[.)])\s*','',line).strip(' "\'')
               for line in result.splitlines() if line.strip()]
        if len(lines)!=5 or any(not 15 <= len(x) <= 170 for x in lines):
            return None, 'AI output failed five-scene format checks'
        return lines,None
    except (ValueError,KeyError,TypeError):
        return None,'AI output could not be validated'


def _paint_png(path, scene, fmt, topic, i, width=360, height=640):
    """Draw original cartoon/storyboard PNGs with Python stdlib; no image credits, fonts or GPU."""
    w,h=width,height
    tones=[((18,23,47),(54,32,95)), ((17,39,70),(18,85,100)),
           ((44,28,66),(125,56,84)),((25,45,56),(58,95,67)),
           ((60,33,45),(108,55,57))]
    c1,c2=tones[(i-1)%len(tones)]
    buf=bytearray(w*h*3)
    for y in range(h):
        t=y/h
        color=tuple(int(a+(b-a)*t) for a,b in zip(c1,c2))
        buf[y*w*3:(y+1)*w*3]=bytes(color)*w
    def rect(x0,y0,x1,y1,color):
        x0=max(0,int(x0));x1=min(w,int(x1));y0=max(0,int(y0));y1=min(h,int(y1))
        if x1<=x0 or y1<=y0:return
        bar=bytes(color)*(x1-x0)
        for y in range(y0,y1):buf[(y*w+x0)*3:(y*w+x1)*3]=bar
    def ellipse(cx,cy,rx,ry,color):
        if rx<=0 or ry<=0:return
        for y in range(max(0,int(cy-ry)),min(h,int(cy+ry)+1)):
            term=1-((y-cy)/ry)**2
            if term<0:continue
            run=rx*math.sqrt(term)
            rect(cx-run,y,cx+run+1,y+1,color)
    def label(text,y,scale=3,ink=(242,246,251),max_lines=4):
        cap=max(8, (w-32)//(6*scale))
        lines=textwrap.wrap(str(text).upper(),width=cap,break_long_words=True)[:max_lines]
        for line in lines:
            x=(w-len(line)*6*scale)//2
            for letter in line:
                glyph=FONT.get(letter,FONT.get('?',('00000',)*7))
                for ry, bits in enumerate(glyph):
                    for rx,v in enumerate(bits):
                        if v=='1':rect(x+rx*scale,y+ry*scale,x+(rx+1)*scale,y+(ry+1)*scale,ink)
                x+=6*scale
            y+=9*scale
    rect(0,0,w,9,(110,234,218))
    label('ORIGINAL / LOCAL',34,2,(140,255,225),max_lines=1)
    if fmt == 'fruit-story':
        colors=[(243,74,97),(248,206,66),(250,154,55),(166,100,215),(250,85,125)]
        body=colors[(i-1)%len(colors)]
        ellipse(w//2,320,107,139,(12,16,29))
        ellipse(w//2,308,102,136,body)
        # leaf + dimensional highlight
        ellipse(w//2-20,166,31,15,(52,154,91))
        ellipse(w//2+12,161,31,17,(72,183,93))
        ellipse(w//2-35,268,16,39,tuple(min(255,c+25) for c in body))
        for ex in (w//2-41,w//2+41):
            ellipse(ex,285,15,21,(249,253,255))
            ellipse(ex+3,287,7,13,(20,24,36))
            ellipse(ex+5,281,2,3,(255,255,255))
        # alternating mouth poses (two selected during animation using static scene changes)
        if i%2==0:
            ellipse(w//2,356,23,30,(63,24,39))
            ellipse(w//2,369,15,9,(247,126,139))
        else:
            ellipse(w//2,356,25,10,(60,21,34))
            rect(w//2-18,351,w//2+18,357,(250,242,235))
        label(['STRAWBERRY','BANANA','ORANGE','GRAPE','FRUIT FRIENDS'][i-1],485,3,(255,238,187),1)
    elif fmt=='fictional-reddit':
        rect(24,153,w-24,480,(238,245,250))
        rect(24,153,w-24,216,(240,120,75))
        label('FICTIONAL POST',173,3,(25,31,46),1)
        label('MY STORY',245,4,(30,35,51),1)
        ellipse(w//2,348,42,42,(240,150,97))
        label('ORIGINAL FICTION',409,2,(45,61,75),2)
    elif fmt=='quick-quiz':
        label('QUICK QUIZ',173,4,(254,204,100),2)
        ellipse(w//2,322,105,105,(47,67,110))
        label('?',277,12,(251,241,176),1)
    else:
        ellipse(w//2,290,117,117,(55,92,118))
        label(('NEW STORY' if fmt=='micro-drama' else '5 QUICK STEPS'),230,3,(254,219,140),2)
        label(str(i),325,8,(230,243,255),1)
    # Background panel gives readable subtitles on phone-sized screens
    rect(15,522,w-15,625,(11,16,27))
    label(scene,536,2,(255,255,255),max_lines=4)
    path=Path(path)
    raw=b''.join(b'\x00'+bytes(buf[y*w*3:(y+1)*w*3]) for y in range(h))
    def chunk(tag, content):
        return struct.pack('!I',len(content))+tag+content+struct.pack('!I',zlib.crc32(tag+content)&0xffffffff)
    png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw,6))+chunk(b'IEND',b'')
    path.write_bytes(png)


def _ffprobe_seconds(audio):
    exe=shutil.which('ffprobe')
    if not exe:raise RuntimeError('ffprobe missing; install the complete free FFmpeg package')
    p=subprocess.run([exe,'-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(audio)],
                     capture_output=True,text=True,timeout=30,check=False)
    if p.returncode:raise RuntimeError('Cannot measure the local narration file')
    duration=float(p.stdout.strip())
    if not math.isfinite(duration) or duration<=0 or duration>300:raise ValueError('Narration must be 1–300 seconds')
    return duration


def _kokoro(home,script,out,voice='af_sarah'):
    home=Path(home)
    py=home/'.voice-env'/'Scripts'/'python.exe'
    if not py.exists():py=home/'.voice-env'/'bin'/'python'
    model=home/'local_media'/'kokoro'/'kokoro-v1.0.onnx'
    voices=home/'local_media'/'kokoro'/'voices-v1.0.bin'
    if not all(p.is_file() for p in (py,model,voices)):
        raise RuntimeError('Local Kokoro model not ready. Keep using your existing .voice-env and local_media/kokoro setup; no new downloads performed.')
    if voice not in ('af_sarah','af_heart','am_michael','am_adam'):
        raise ValueError('Choose one of the supported local Kokoro voices')
    import os
    # Short sentences are less memory-intensive on CPU than one long inference.
    program = (
        'import re,sys,traceback\n'
        'try:\n'
        ' import numpy as np, soundfile as sf\n'
        ' from kokoro_onnx import Kokoro\n'
        ' m=Kokoro(sys.argv[1],sys.argv[2])\n'
        ' text=sys.argv[4].strip()\n'
        ' pieces=[x.strip() for x in re.split(r"(?<=[.!?])\\s+",text) if x.strip()]\n'
        ' if not pieces: raise ValueError("Narration script is empty")\n'
        ' chunks=[]; rate=None\n'
        ' for part in pieces:\n'
        '  data,r=m.create(part,voice=sys.argv[5],speed=1.05,lang="en-us")\n'
        '  if rate is not None and r!=rate: raise ValueError("Voice sample rates differ")\n'
        '  rate=r; chunks.append(np.asarray(data).reshape(-1))\n'
        ' sf.write(sys.argv[3],np.concatenate(chunks),rate)\n'
        ' print("KOKORO_RENDERED",len(pieces),flush=True)\n'
        'except BaseException:\n'
        ' traceback.print_exc()\n'
        ' sys.exit(3)\n'
    )
    env=os.environ.copy()
    for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
        env[key]='1'
    try:
        p=subprocess.run([str(py),'-c',program,str(model),str(voices),str(out),script,voice],
                         stdin=subprocess.DEVNULL,capture_output=True,text=True,
                         errors='replace',timeout=420,check=False,env=env)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError('Kokoro CPU narration timed out; try a shorter script') from exc
    if p.returncode or not out.is_file() or out.stat().st_size<100:
        detail=(p.stderr or p.stdout or 'Child Python exited without diagnostic text').strip()[-1400:]
        raise RuntimeError(f'Local Kokoro failed (exit code {p.returncode}): {detail}')
    return out


def _render(scene_paths,out,audio=None,quality='preview'):
    ffmpeg=shutil.which('ffmpeg')
    if not ffmpeg:raise RuntimeError('FFmpeg missing: install free FFmpeg on PATH')
    if quality not in ('preview','standard'):raise ValueError('Choose preview or standard')
    duration=max(15.0,(_ffprobe_seconds(audio)+1.2) if audio else 15.0)
    # Scene duration follows narration duration, not the old hard-coded 15s cutoff.
    per=duration/5
    out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
    args=[ffmpeg,'-hide_banner','-nostdin','-loglevel','error','-y']
    for path in scene_paths:
        args += ['-loop','1','-framerate','12','-t',f'{per:.3f}','-i',str(path)]
    if audio:
        args += ['-i',str(audio)]
    filters=[]
    for i in range(5):
        filters.append(f'[{i}:v]scale=360:640,format=yuv420p,setpts=PTS-STARTPTS,'
                       f'fade=t=in:st=0:d=0.25,fade=t=out:st={per-0.25:.3f}:d=0.24[v{i}]')
    filters.append(''.join(f'[v{i}]' for i in range(5))+'concat=n=5:v=1:a=0[vout]')
    args+=['-filter_complex',';'.join(filters),'-map','[vout]']
    if audio:
        args+=['-map','5:a:0','-c:a','aac','-af','apad']
    args+=['-t',f'{duration:.2f}','-c:v','libx264','-preset','ultrafast' if quality=='preview' else 'veryfast',
           '-crf','28' if quality=='preview' else '23','-pix_fmt','yuv420p','-movflags','+faststart',str(out)]
    try:
        p=subprocess.run(args,stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=210,check=False)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError('Local FFmpeg render exceeded the bounded time limit') from exc
    if p.returncode or not out.is_file() or out.stat().st_size<3000:
        raise RuntimeError('FFmpeg failed to render preview: '+p.stderr[-500:])
    return {'path':str(out),'seconds':round(duration,2),'bytes':out.stat().st_size}


def make(home, fmt, topic, ai=False, narrate=False, render=False, voice='af_sarah',model='qwen3:8b'):
    if fmt not in FORMATS:raise ValueError('Unsupported studio format')
    topic=_clean(topic)
    from .court import Proposal, adjudicate
    judgment=adjudicate(Proposal(bot_key='viral_creator_'+fmt,title=f'Create original {fmt} draft: {topic}',
                                action='generate_local_draft',expenditure_usd=0,third_party_ip=False,
                                expected_revenue_claim='unknown'))
    if judgment.verdict!='NOT GUILTY':
        raise RuntimeError('Court rejected this local proposal')
    home=Path(home).resolve()
    fingerprint=hashlib.sha256(('viral_studio_v1:'+fmt+':'+topic).encode()).hexdigest()
    folder=home/'output'/'viral_studio'/fmt/fingerprint[:14]
    # No overwriting approved outputs or rerunning duplicates that would inflate docket counts.
    if (folder/'metadata.json').exists():
        old=json.loads((folder/'metadata.json').read_text(encoding='utf-8'))
        return {'status':'already_created','folder':str(folder),'court_verdict':old['court_verdict'],
                'ai_script_used':old['ai_script_used'],'published':False,'verified_sales':0}
    store=Store(home)
    caseid=store.add_case(fingerprint,'viral_creator_'+fmt,'Original '+fmt+': '+topic,0,judgment.data())
    scenes= _script_fallback(fmt,topic)
    ai_issue=None
    ai_used=False
    if ai:
        generated,ai_issue=_local_ai(fmt,topic,model=model)
        if generated:
            scenes=generated
            ai_used=True
    folder.mkdir(parents=True,exist_ok=True)
    images=[]
    for i,scene in enumerate(scenes,1):
        path=folder/f'scene_{i:02d}.png'
        _paint_png(path,scene,fmt,topic,i)
        images.append(path)
    script=' '.join(scenes)
    (folder/'script.txt').write_text(script+'\n',encoding='utf-8')
    (folder/'scenes.json').write_text(json.dumps(scenes,indent=2),encoding='utf-8')
    audio=None
    if narrate:
        audio=_kokoro(home,script,folder/'narration.wav',voice=voice)
    total_seconds=max(15.0,(_ffprobe_seconds(audio)+1.2) if audio else 15.0)
    scene_seconds=total_seconds/5.0
    def stamp(t):
        millis=int(round(t*1000))
        hours,rem=divmod(millis,3600_000)
        minutes,rem=divmod(rem,60_000)
        seconds,millis=divmod(rem,1000)
        return f'{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}'
    (folder/'captions.srt').write_text(''.join(f'{i}\n{stamp((i-1)*scene_seconds)} --> {stamp(i*scene_seconds)}\n{scene}\n\n'
                                         for i,scene in enumerate(scenes,1)),encoding='utf-8')
    video=None
    if render:
        video=_render(images,folder/'preview.mp4',audio=audio)
    meta={
        'created_utc':datetime.now(timezone.utc).isoformat(),
        'format':fmt,'topic':topic,'original_fiction':fmt in ('fruit-story','fictional-reddit','micro-drama'),
        'court_verdict':judgment.verdict,'case_id':caseid,'ai_script_requested':bool(ai),
        'ai_script_used':ai_used,'ai_note':ai_issue,'local_voice_used':bool(audio),
        'video':video,'no_external_content_copied':True,'paid_services_called':False,
        'human_publication_approval_required':True,'published':False,'verified_sales':0,
        'license_review_required_before_publication':True,
        'assets':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in images},
    }
    (folder/'metadata.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
    (folder/'PUBLISHING_CHECKLIST.txt').write_text(
        'ORIGINAL local video draft only. Watch it and review factual claims, pacing, audio, and subtitles.\n'
        'If using realistic AI media, label it appropriately. Fictional Reddit-style stories are not real Reddit testimonials.\n'
        'Do not use copied Reddit posts, copyrighted gameplay, unlicensed music, or others\' faces/voices.\n'
        'Add platform authorizations and owner approvals before publication. No income is guaranteed.\n',encoding='utf-8')
    if caseid:store.update_artifact(caseid,str(folder))
    return {'status':'created','folder':str(folder),'court_verdict':judgment.verdict,
            'court_case_id':caseid,'ai_script_used':ai_used,'voice_created':bool(audio),
            'render':video,'published':False,'verified_sales':0}


def doctor(home):
    h=Path(home)
    return {'formats':FORMATS,'references':RESEARCH_REFERENCES,
            'ffmpeg_ready':bool(shutil.which('ffmpeg')),
            'kokoro_voice_ready':all((h/x).is_file() for x in (
                '.voice-env/Scripts/python.exe','local_media/kokoro/kokoro-v1.0.onnx',
                'local_media/kokoro/voices-v1.0.bin')),
            'ollama_optional':True,'no_paid_apis':True,'automatic_posting':False}


def daily_studio(home, now=None):
    """One varied local creative draft per UTC day; no auto-posting or earnings claims."""
    from datetime import date
    now = now or datetime.now(timezone.utc)
    day = now.date() if hasattr(now,'date') else date.today()
    styles=tuple(FORMATS)
    fmt=styles[day.toordinal()%len(styles)]
    prompts={
        'fruit-story':('The strawberry who solved a grocery store mystery',
                       'The lemon who opened a smoothie restaurant',
                       'The banana who lost a secret recipe',
                       'The blueberry who fixed a broken bicycle'),
        'fictional-reddit':('A surprise invitation that changed my weekend',
                            'A lost key and a note from my neighbor',
                            'The birthday surprise everyone kept secret',
                            'A strange package at the wrong apartment'),
        'quick-quiz':('Three clever questions about everyday budgeting',
                     'Common misconceptions about saving money',
                     'How to spot a fake online offer',
                     'Five basic facts about free software'),
        'micro-drama':('A forgotten note inside a secondhand jacket',
                       'The mysterious light across the street',
                       'An old photograph with a hidden message',
                       'A challenge between two best friends'),
        'tips':('How to organize free online learning resources',
                'How to plan a weekly study schedule',
                'How to make an original digital portfolio',
                'How to check whether a free app is trustworthy'),
    }
    topic=prompts[fmt][(day.toordinal()//len(styles))%4]
    home=Path(home)
    voice_ready=doctor(home)['kokoro_voice_ready']
    use_ai=False  # Autonomous default is bounded, deterministic, testable; enable local AI explicitly.
    # Avoid unbounded CPU utilization while other research and business workers are active.
    try:
        result=make(home,fmt,topic,ai=use_ai,narrate=voice_ready,
                    render=bool(shutil.which('ffmpeg')))
        return {'cycle_date_utc':day.isoformat(),'format':fmt,'output':result,
                'topic_signal':'curated_original_prompt_not_verified_trend',
                'external_posted':False}
    except (RuntimeError,ValueError,OSError) as exc:
        return {'cycle_date_utc':day.isoformat(),'format':fmt,
                'skipped_or_failed':str(exc)[:250],'external_posted':False}
