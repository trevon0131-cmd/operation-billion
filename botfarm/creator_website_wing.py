"""Original content and website samples, shared court and append-only provenance.

Built-in: standard-library HTML, SVG, PNG, SRT, script + proposal creation.
Optional: locally installed FFmpeg turns slides into an MP4, with a bounded timeout.
Never downloads models, posts, emails, enrolls, claims sales, or runs GitHub code.
"""
from __future__ import annotations
import hashlib
import html
import os
import urllib.request
import urllib.error
import json
import re
import shutil
import sqlite3
import struct
import subprocess
import zlib
from contextlib import contextmanager, closing
from datetime import datetime, timezone, timedelta
from pathlib import Path
from .court import Proposal, adjudicate
from .workshop import atomic_text

TOPICS = (
    ('Organize a job search', 'How to organize a job search without expensive apps', 'Track application dates', 'Save company links', 'Review follow-ups weekly'),
    ('Make a simple budget', 'A basic budget you can make using free tools', 'List recurring expenses', 'Separate needs and wants', 'Review your totals regularly'),
    ('Improve a small business site', 'Three checks for a useful small business website', 'Make contact details obvious', 'Check mobile readability', 'Make one clear call to action'),
    ('Create original product photos', 'Better product presentation without expensive equipment', 'Use daylight when available', 'Choose a clean background', 'Show multiple accurate angles'),
    ('Plan a weekly routine', 'Create a weekly plan using simple checklists', 'Name one priority', 'Reserve realistic time', 'Review what worked'),
    ('Create an educational short', 'Three steps to making an original educational video', 'Choose one focused question', 'Verify each factual claim', 'Edit for clarity and accessibility'),
)
NICHES = ('local cafe','plumbing service','barbershop','independent tutor','cleaning company','local nonprofit','fitness instructor')
TOOLS = (
    {'name':'FFmpeg','url':'https://github.com/FFmpeg/FFmpeg','role':'video encoding/editing','mode':'optional_local','cost':'free software; local CPU resources','note':'MP4 rendering with installed ffmpeg; verify codec licensing for distribution'},
    {'name':'MoneyPrinterTurbo','url':'https://github.com/harry0703/MoneyPrinterTurbo','role':'short-form media pipeline inspiration','mode':'research_only','cost':'software free; third-party providers may charge','note':'Not installed or invoked; needs installation, configuration and licensing review'},
    {'name':'Ollama','url':'https://github.com/ollama/ollama','role':'local brainstorming and script rewriting','mode':'optional_local','cost':'free app; compute/memory/model license requirements','note':'Existing Ollama adapter; model must be installed independently'},
    {'name':'Piper','url':'https://github.com/rhasspy/piper','role':'local text-to-speech inspiration','mode':'research_only','cost':'free software; voice model licenses vary','note':'Separate binaries and models required; no automatic voice downloads'},
    {'name':'ComfyUI','url':'https://github.com/Comfy-Org/ComfyUI','role':'AI image/video generation','mode':'research_only','cost':'free software; powerful hardware/model licenses often needed','note':'Not installed; heavy GPU workflow optional'},
    {'name':'MoviePy','url':'https://github.com/Zulko/moviepy','role':'Python video editing','mode':'research_only','cost':'free library; setup and FFmpeg required','note':'Alternative not loaded in minimal core'},
    {'name':'bolt.diy','url':'https://github.com/stackblitz-labs/bolt.diy','role':'AI-assisted websites','mode':'research_only','cost':'source open; production WebContainer license may be needed','note':'No commercial runtime license assumed; static local generator used instead'},
    {'name':'Hugo','url':'https://github.com/gohugoio/hugo','role':'static site builder','mode':'optional_local','cost':'free binary','note':'Hosting providers have separate commercial-use terms'},
    {'name':'Lighthouse','url':'https://github.com/GoogleChrome/lighthouse','role':'public website diagnostics','mode':'research_only','cost':'free local tool','note':'Only permitted scans with rate caps; never claim a scan occurred if not run'},
    {'name':'Playwright','url':'https://github.com/microsoft/playwright-python','role':'site visual testing and screenshots','mode':'research_only','cost':'free software; browser installation','note':'Does not bypass CAPTCHAs, logins, payments or security checks'},
    {'name':'Crawl4AI','url':'https://github.com/unclecode/crawl4ai','role':'public web content research','mode':'research_only','cost':'free software; browser resource requirements','note':'Honor robots, site policy, source licenses, and reasonable limits'},
    {'name':'OpenShot','url':'https://github.com/OpenShot/openshot-qt','role':'human-reviewed video editing','mode':'research_only','cost':'free desktop editor','note':'Optional editing interface, not a backend currently installed'},
    {'name':'Auto-Editor','url':'https://github.com/WyattBlue/auto-editor','role':'optional video silence cut','mode':'research_only','cost':'free software; local resources','note':'Not installed'},
    {'name':'Whisper.cpp','url':'https://github.com/ggml-org/whisper.cpp','role':'optional local transcription','mode':'research_only','cost':'free core; download a properly licensed model','note':'User must have rights to transcribe media'},
)

# Font is deliberately tiny and original; no third-party assets or downloadable fonts needed.
FONT = {
'A':('01110','10001','10001','11111','10001','10001','10001'),
'B':('11110','10001','10001','11110','10001','10001','11110'),
'C':('01111','10000','10000','10000','10000','10000','01111'),
'D':('11110','10001','10001','10001','10001','10001','11110'),
'E':('11111','10000','10000','11110','10000','10000','11111'),
'F':('11111','10000','10000','11110','10000','10000','10000'),
'G':('01111','10000','10000','10111','10001','10001','01111'),
'H':('10001','10001','10001','11111','10001','10001','10001'),
'I':('11111','00100','00100','00100','00100','00100','11111'),
'J':('00111','00010','00010','00010','10010','10010','01100'),
'K':('10001','10010','10100','11000','10100','10010','10001'),
'L':('10000','10000','10000','10000','10000','10000','11111'),
'M':('10001','11011','10101','10101','10001','10001','10001'),
'N':('10001','11001','10101','10011','10001','10001','10001'),
'O':('01110','10001','10001','10001','10001','10001','01110'),
'P':('11110','10001','10001','11110','10000','10000','10000'),
'Q':('01110','10001','10001','10001','10101','10010','01101'),
'R':('11110','10001','10001','11110','10100','10010','10001'),
'S':('01111','10000','10000','01110','00001','00001','11110'),
'T':('11111','00100','00100','00100','00100','00100','00100'),
'U':('10001','10001','10001','10001','10001','10001','01110'),
'V':('10001','10001','10001','10001','10001','01010','00100'),
'W':('10001','10001','10001','10101','10101','10101','01010'),
'X':('10001','10001','01010','00100','01010','10001','10001'),
'Y':('10001','10001','01010','00100','00100','00100','00100'),
'Z':('11111','00001','00010','00100','01000','10000','11111'),
'0':('01110','10001','10011','10101','11001','10001','01110'),
'1':('00100','01100','00100','00100','00100','00100','01110'),
'2':('01110','10001','00001','00010','00100','01000','11111'),
'3':('11110','00001','00001','01110','00001','00001','11110'),
'4':('00010','00110','01010','10010','11111','00010','00010'),
'5':('11111','10000','11110','00001','00001','10001','01110'),
'6':('01111','10000','10000','11110','10001','10001','01110'),
'7':('11111','00001','00010','00100','01000','01000','01000'),
'8':('01110','10001','10001','01110','10001','10001','01110'),
'9':('01110','10001','10001','01111','00001','00001','11110'),
' ':('00000',)*7,'-':('00000','00000','00000','11111','00000','00000','00000'),
'.':('00000','00000','00000','00000','00000','00110','00110'),
':':('00000','00110','00110','00000','00110','00110','00000'),
'?':('01110','10001','00001','00010','00100','00000','00100'),
'/':('00001','00001','00010','00100','01000','10000','10000'),
}

def safe_text(value, maximum=100):
    text=re.sub(r'\s+', ' ', str(value)).strip()
    if not text or len(text)>maximum or any(ord(c)<32 for c in text):
        raise ValueError('Text missing or too long')
    return text

def safe_slug(value):
    s=re.sub(r'[^a-z0-9]+','-',value.lower()).strip('-')[:55]
    return s or 'sample'

def png_slide(path:Path,title:str,subtitle:str,portrait=True):
    """Write readable original bitmap text art (PNG), no Pillow or external assets."""
    w,h=(540,960) if portrait else (960,540)
    base=[19,35,61]
    accent=(70,194,170)
    canvas=bytearray(bytes(base)*w*h)
    def rect(x0,y0,x1,y1,col):
        for y in range(max(0,y0),min(h,y1)):
            line=y*w*3
            for x in range(max(0,x0),min(w,x1)):
                start=line+x*3;canvas[start:start+3]=bytes(col)
    def render_line(text,y,scale=7):
        text=text.upper(); glyph_width=6*scale
        x=(w-len(text)*glyph_width)//2
        for char in text:
            glyph=FONT.get(char,FONT['?'])
            for gy,pattern in enumerate(glyph):
                for gx,v in enumerate(pattern):
                    if v=='1':rect(x+gx*scale,y+gy*scale,x+(gx+1)*scale,y+(gy+1)*scale,(242,249,250))
            x+=glyph_width
    rect(0,0,w,18,accent);rect(0,h-18,w,h,accent)
    scale=5 if portrait else 5
    cap=max(8,(w-40)//(6*scale))
    def wrap(s):
        words=s.upper().split(); lines=[]; current=''
        for word in words:
            if len(word)>cap:word=word[:cap]
            proposed=(current+' '+word).strip()
            if len(proposed)>cap and current:lines.append(current); current=word
            else: current=proposed
        if current:lines.append(current)
        return lines[:5]
    title_lines=wrap(title)
    start=h//4
    for i,line in enumerate(title_lines):render_line(line,start+i*49,scale)
    rect(60,int(h*.67),w-60,int(h*.67)+4,accent)
    subtitle_lines=wrap(subtitle)
    for i,line in enumerate(subtitle_lines):render_line(line,int(h*.73)+i*49,scale)
    raw=bytearray()
    for y in range(h): raw.append(0); raw.extend(canvas[y*w*3:(y+1)*w*3])
    def chunk(kind,payload):
        return struct.pack('!I',len(payload))+kind+payload+struct.pack('!I',zlib.crc32(kind+payload)&0xffffffff)
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',w,h,8,2,0,0,0))+
                     chunk(b'IDAT',zlib.compress(bytes(raw),9))+chunk(b'IEND',b''))

def timecode(seconds):
    ms=round(seconds*1000)
    return f'{ms//3600000:02}:{(ms//60000)%60:02}:{(ms//1000)%60:02},{ms%1000:03}'

def local_ai_storyboard(subject,model='gemma3:1b',fetcher=None):
    """Optional Ollama on loopback ONLY. Never executes suggestions or trusts their claims.
    Does not download a model, connect to paid services, or use web search.
    """
    subject=safe_text(subject,100)
    if not re.fullmatch(r'[a-zA-Z0-9_./:-]{1,80}',model):raise ValueError('Invalid local model')
    instructions=('Produce ONLY a JSON array of exactly five SHORT and DISTINCT scene headings (max 60 characters each) '
                  'for an original educational short about '+subject+'. Avoid quotes, unverifiable factual claims, '
                  'celebrity likeness, trademarks, fabricated prices or earnings promises. No reused movie/music clips. '
                  'These suggestions are not validated evidence of market demand.')
    payload=json.dumps({'model':model,'prompt':instructions,'stream':False,
                        'format':'json','think':False if model.startswith('qwen3:') else None,'options':{'temperature':0.4,'num_predict':180}}).encode()
    if fetcher is None:
        def fetcher(request):
            with urllib.request.urlopen(request,timeout=300) as response:return response.read(26000)
    request=urllib.request.Request('http://127.0.0.1:11434/api/generate',data=payload,
                                   headers={'Content-Type':'application/json'},method='POST')
    raw=fetcher(request)
    if len(raw)>26000:raise ValueError('Local AI response too large')
    message=json.loads(raw)
    lines=json.loads(message['response'])
    if (not isinstance(lines,list) or len(lines)!=5 or
        not all(isinstance(x,str) and 3<=len(x.strip())<=60 and '\n' not in x for x in lines)):
        raise ValueError('Local AI returned an invalid storyboard')
    return [safe_text(x,60) for x in lines]

def write_video(folder:Path, topic_key:int=0, format='short', render_mp4=False, ai_lines=None, requested_topic=None):
    if format not in ('short','youtube') or type(topic_key)!=int or not 0<=topic_key<len(TOPICS):
        raise ValueError('Unsupported format/topic')
    folder.mkdir(parents=True,exist_ok=True)
    subject,title,*steps=TOPICS[topic_key]
    portrait=format=='short'
    if requested_topic is not None:
        requested_topic = safe_text(requested_topic,100)
        if requested_topic.casefold() != subject.casefold():
            # Never silently replace the user's idea with a preset niche.
            title = requested_topic
            subject = requested_topic
            steps = ('Define the problem clearly', 'Create one practical example',
                     'Show how to apply the idea')
    lines=ai_lines if ai_lines is not None else [('What is '+subject+'?')[:70],*steps,'One useful next step']
    if len(lines)!=5 or not all(isinstance(x,str) and 1<=len(x)<=70 for x in lines):
        raise ValueError('Invalid storyboard input')
    paths=[]
    for i,headline in enumerate(lines):
        path=folder/f'scene_{i+1:02}.png'; png_slide(path,headline,subject,portrait);paths.append(path)
    script=f'Topic: {title}\n\n'+'\n'.join(f'Scene {i}: {txt}' for i,txt in enumerate(lines,1))+'\n\nVerify any additional factual claims before publication.\n'
    atomic_text(folder/'script.txt',script)
    secs=3
    srt='\n'.join(f'{i}\n{timecode((i-1)*secs)} --> {timecode(i*secs)}\n{text}\n' for i,text in enumerate(lines,1))
    atomic_text(folder/'captions.srt',srt)
    metadata={'format':format,'topic':title,'platforms':['YouTube Shorts','TikTok','Instagram Reels'] if portrait else ['YouTube'],
              'duration_seconds':len(lines)*secs,'requested_topic':requested_topic or subject,'source_of_claims':'original instructional suggestions; no viral/sales metrics asserted',
              'script_origin':'optional local Ollama draft, human fact-check required' if ai_lines else 'original curated scene suggestions',
              'footage':'original locally generated bitmap images','music':'none (no copied music)','voiceover':'not generated',
              'monetization':'NOT CONNECTED','publishing':'OWNER REVIEW REQUIRED',
              'quality_gates':['check factual accuracy','check readability','check originality',
                               'disclose realistic AI-generated imagery where required','review each platform policy'],
              'validation':['publish only after channel connection and owner approval','record genuine views and retention',
                            'compare distinct original topics','review after 7 days; retire or pivot after 14 days without results']}
    atomic_text(folder/'metadata.json',json.dumps(metadata,indent=2))
    atomic_text(folder/'README.txt',"Original video scenes and captions. To render MP4, install FFmpeg and run 'py -3 -m botfarm video-demo --render'.\n"+
          'No auto-publication, voice cloning, copyrighted footage, or earnings claims.\n')
    rendered=False;error='FFmpeg not installed or render not requested'
    if render_mp4:
        binary=shutil.which('ffmpeg')
        if binary:
            parts=[]
            for path in paths:
                parts.append("file '"+path.name+"'\n"+f'duration {secs}\n')
            parts.append("file '"+paths[-1].name+"'\n")
            atomic_text(folder/'frames.txt',''.join(parts))
            args=[binary,'-hide_banner','-nostdin','-loglevel','error','-y','-f','concat','-safe','1',
                  '-i',str(folder/'frames.txt'),'-vf','fps=12,format=yuv420p','-c:v','libx264','-t',str(len(paths)*secs),
                  str(folder/'preview.mp4')]
            try:
                process=subprocess.run(args,cwd=folder,capture_output=True,text=True,timeout=90,check=False)
                rendered=process.returncode==0 and (folder/'preview.mp4').stat().st_size>0 if (folder/'preview.mp4').exists() else False
                error='' if rendered else 'FFmpeg could not encode this project; storyboard is available'
            except (subprocess.TimeoutExpired,OSError): error='FFmpeg timed out or could not start; scenes remain usable'
    return {'folder':str(folder),'topic':title,'scenes':len(lines),'png_count':len(paths),'mp4_rendered':rendered,'render_note':error,'external_published':False}

def write_site(folder:Path,niche='local cafe',business='Example Neighborhood Studio'):
    niche=safe_text(niche,100); business=safe_text(business,100)
    folder.mkdir(parents=True,exist_ok=True)
    b=html.escape(business,quote=True);n=html.escape(niche,quote=True)
    # Placeholder-only claims, no fake reviews, false credentials, or fabricated opening hours.
    page=f'''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{b} | Website Demonstration</title><meta name="robots" content="noindex,nofollow">
<style>:root{{--ink:#142b3d;--accent:#168b7c;--cream:#f6f8fa}}*{{box-sizing:border-box}}body{{margin:0;font:18px/1.6 system-ui,Segoe UI,sans-serif;color:var(--ink);background:var(--cream)}}
header{{background:white;padding:1rem 5vw;display:flex;justify-content:space-between;align-items:center;gap:1rem;flex-wrap:wrap}}a{{color:#086e64}}nav a{{margin-right:1.2rem}}.hero{{padding:8vh 6vw;background:linear-gradient(120deg,#12334b,#197e78);color:white}}h1{{font-size:clamp(2.1rem,5vw,4rem);max-width:850px;line-height:1.15}}.hero p{{max-width:700px}}.tag{{display:inline-block;color:#fff;background:#ad4c32;padding:.3rem .7rem;border-radius:.3rem}}.btn{{display:inline-block;background:#fbdb7b;color:#172a38;padding:.8rem 1.2rem;border-radius:.4rem;text-decoration:none;font-weight:bold}}.wrap{{max-width:1100px;margin:auto;padding:4rem 5vw}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1rem}}article{{background:white;padding:1.7rem;border-radius:.8rem;border:1px solid #dce4e8}}footer{{background:#152b3d;color:white;padding:2rem 5vw}}footer a{{color:#b6ece4}}.placeholder{{background:#fff6e6;padding:1rem;border-left:4px solid #d99b25}}:focus-visible{{outline:3px solid #df7d37}}</style></head>
<body><header><strong>{b} — DEMO</strong><nav aria-label="Main"><a href="#services">Services</a><a href="#about">About</a><a href="#contact">Contact</a></nav></header>
<main><section class="hero"><span class="tag">FICTIONAL DEMO — NOT A REAL BUSINESS</span><h1>A clearer website for your {n}.</h1><p>This original sample shows a mobile-friendly layout with services, trust-building information, and a simple way to make contact.</p><a class="btn" href="#contact">See contact section</a></section>
<section id="services" class="wrap"><h2>How we could help</h2><div class="grid"><article><h3>One clear offer</h3><p>Replace this card with a real service and an accurate description.</p></article><article><h3>Easy next steps</h3><p>Show visitors how to ask a question or request a quote.</p></article><article><h3>Mobile-friendly layout</h3><p>Built to adapt to narrow screens without requiring an expensive builder.</p></article></div></section>
<section id="about" class="wrap"><h2>About this demo</h2><p>This is a fictional concept website for a potential {n}. No real testimonials, guarantees, certifications, address, or achievements are claimed.</p></section>
<section id="contact" class="wrap"><h2>Get in touch</h2><div class="placeholder"><strong>PLACEHOLDER</strong><p>Replace with the client's verified contact email, telephone, location and operating hours after approval. No form or payment processor is connected.</p></div></section></main>
<footer><strong>{b}</strong> — Sample only. No hosting, contact submission or payment processing.</footer></body></html>'''
    atomic_text(folder/'index.html',page)
    proposal=f'''WEBSITE SERVICE PROPOSAL — DRAFT ONLY\nBusiness niche: {niche}\nClient: FICTIONAL, no real relationship\n\nDeliverables: responsive HTML/CSS homepage, accessible sections, verified contact details after client approval, mobile checks, content handoff.\nNot included: paid hosting, custom domain, advanced forms or payment processing, SEO rankings, or guaranteed conversions.\n\nSteps: learn client's goals; get written permission/content; approve scope and quote; tailor with real information; test; owner approves publication.\n\nValidation: present a legitimate sample through an approved channel; record actual inquiries and client feedback; reassess at 7 and 14 days.\n'''
    atomic_text(folder/'proposal_DRAFT.txt',proposal)
    email_draft='''UNSENT COMMERCIAL OUTREACH DRAFT — OWNER MUST REVIEW\nSubject: A simple website improvement idea for [BUSINESS NAME]\n\nHello [VERIFIED CONTACT NAME],\n\nI offer website design services. I put together a fictional example of a mobile-friendly homepage, and I can prepare a customized proposal if this is useful to your business. I have not audited your site or claimed any relationship.\n\nIf you are interested, reply and I can share an example and discuss the scope and price.\n\nRegards,\n[YOUR BUSINESS NAME]\n[YOUR VALID POSTAL ADDRESS]\n[WORKING CONTACT AND OPT-OUT METHOD]\n\nAdvertisement / commercial solicitation. No email has been sent. Comply with CAN-SPAM, recipient preferences, and applicable local laws.\n'''
    atomic_text(folder/'outreach_UNSENT.txt',email_draft)
    atomic_text(folder/'CHECKLIST.txt','Verify all claims and client permissions. Review WCAG accessibility. Test on a real phone. Choose commercially permitted hosting. Do not assume GitHub Pages permits e-commerce hosting. Connect contact/payment systems only with explicit authorization.\n')
    return {'folder':str(folder),'niche':niche,'preview':str(folder/'index.html'),'email_sent':False,'website_published':False,'customer_or_order':False}

class Wing:
    def __init__(self,home):
        self.home=Path(home);self.db=self.home/'data'/'creator_website_wing.sqlite3'
        self.db.parent.mkdir(parents=True,exist_ok=True)
        with self.connect() as con:
            con.executescript('''CREATE TABLE IF NOT EXISTS drafts(id INTEGER PRIMARY KEY, fingerprint TEXT NOT NULL UNIQUE, kind TEXT NOT NULL, subject TEXT NOT NULL, verdict TEXT NOT NULL, judgment TEXT NOT NULL, folder TEXT, created TEXT NOT NULL);CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY,event TEXT,payload TEXT,previous TEXT,digest TEXT);''')
    @contextmanager
    def connect(self):
        con=sqlite3.connect(self.db,timeout=5)
        con.row_factory=sqlite3.Row
        try:yield con;con.commit()
        finally:con.close()
    def _audit(self,con,event,payload):
        body=json.dumps(payload,sort_keys=True)
        prev=con.execute('SELECT digest FROM audit ORDER BY id DESC LIMIT 1').fetchone()
        earlier=prev['digest'] if prev else 'GENESIS'
        digest=hashlib.sha256((earlier+'|'+event+'|'+body).encode()).hexdigest()
        con.execute('INSERT INTO audit(event,payload,previous,digest) VALUES (?,?,?,?)',(event,body,earlier,digest))
    def audit_valid(self):
        with self.connect() as con:
            prev='GENESIS';seen=[]
            for row in con.execute('SELECT * FROM audit ORDER BY id'):
                if row['previous']!=prev or row['digest']!=hashlib.sha256((prev+'|'+row['event']+'|'+row['payload']).encode()).hexdigest():return False
                payload=json.loads(row['payload'])
                if row['event']=='draft':seen.append(payload['fingerprint'])
                prev=row['digest']
            rows=[dict(row) for row in con.execute('SELECT * FROM drafts ORDER BY id')]
            if len(seen)!=len(rows):return False
            audited=[json.loads(row['payload']) for row in con.execute("SELECT payload FROM audit WHERE event='draft' ORDER BY id")]
            return all(p['fingerprint']==r['fingerprint'] and p['kind']==r['kind'] and
                       p['subject']==r['subject'] and p['verdict']==r['verdict'] and
                       p['folder']==r['folder'] and p['stamp']==r['created'] and
                       json.loads(r['judgment'])['verdict']==r['verdict']
                       for p,r in zip(audited,rows))
    def create(self,kind,subject,variant=0,render=False,unsafe=False,use_ai=False):
        if kind not in ('short','youtube','website'):raise ValueError('Unknown builder')
        if type(variant)!=int or not 0<=variant<100:raise ValueError('Invalid variant')
        subject=safe_text(subject,100)
        fp=hashlib.sha256(json.dumps([kind,subject,variant,bool(unsafe),bool(use_ai)],ensure_ascii=True).encode()).hexdigest()
        if not self.audit_valid():raise RuntimeError('Expansion audit invalid; execution blocked')
        with self.connect() as con:
            row=con.execute('SELECT * FROM drafts WHERE fingerprint=?',(fp,)).fetchone()
            if row:
                if render and kind in ('short','youtube') and row['folder'] and not (Path(row['folder'])/'preview.mp4').exists():
                    topic_index=next((i for i,t in enumerate(TOPICS) if subject.lower() in t[0].lower() or t[0].lower() in subject.lower()),variant%len(TOPICS))
                    write_video(Path(row['folder']),topic_index,kind,render_mp4=True,requested_topic=subject)
                return {'status':'existing','verdict':row['verdict'],'folder':row['folder'],'fingerprint':fp}
        proposal=Proposal(bot_key='expansion_'+kind,title='Create original local '+kind+': '+subject,
                          action='publish_to_marketplace' if unsafe else 'generate_local_draft',
                          expected_revenue_claim='unknown')
        ruling=adjudicate(proposal)
        folder=None; outcome={}
        if ruling.verdict=='NOT GUILTY':
            directory=self.home/'output'/'expansion_wing'/kind/fp[:15]
            if kind in ('short','youtube'):
                # Select a specific researched topic by stable public vocabulary (not arbitrary unverified claims).
                topic_index=next((i for i,t in enumerate(TOPICS) if subject.lower() in t[0].lower() or t[0].lower() in subject.lower()),variant%len(TOPICS))
                ai_lines=None
                if use_ai:
                    try:ai_lines=local_ai_storyboard(subject,model=os.getenv('OPERATION_BILLION_OLLAMA_MODEL','gemma3:1b'))
                    except (ValueError,KeyError,TypeError,TimeoutError,OSError,urllib.error.URLError,json.JSONDecodeError):
                        atomic_text(directory/'AI_MODEL_STATUS.txt','Local model unavailable/invalid; used curated scenes. No model downloaded and no cloud API used.\n')
                outcome=write_video(directory,topic_index,kind,render_mp4=render,ai_lines=ai_lines,requested_topic=subject)
            else:outcome=write_site(directory,subject)
            folder=str(directory)
        stamp=datetime.now(timezone.utc).isoformat()
        with self.connect() as con:
            con.execute('BEGIN IMMEDIATE')
            if con.execute('SELECT 1 FROM drafts WHERE fingerprint=?',(fp,)).fetchone():return {'status':'existing','fingerprint':fp}
            con.execute('INSERT INTO drafts(fingerprint,kind,subject,verdict,judgment,folder,created) VALUES (?,?,?,?,?,?,?)',
                        (fp,kind,subject,ruling.verdict,json.dumps(ruling.data()),folder,stamp))
            self._audit(con,'draft',{'fingerprint':fp,'kind':kind,'subject':subject,'verdict':ruling.verdict,'folder':folder,'stamp':stamp})
        return {'status':'created','verdict':ruling.verdict,'court':ruling.data(),'folder':folder,'outcome':outcome,'fingerprint':fp}
    def overview(self):
        with self.connect() as con:
            rows=[dict(x) for x in con.execute('SELECT id,kind,subject,verdict,folder,created FROM drafts ORDER BY id DESC LIMIT 30')]
            return {'drafts':rows,'audit_valid':self.audit_valid(),'sales_verified':0,'outreach_sent':0,'accounts_connected':0}
    def find_topic_evidence(self, now=None):
        """Match CURRENT approved public signals to known useful topics, else no trend claim.
        The scanner reads local v0.6 data; it never fetches arbitrary URLs itself.
        """
        now=now or datetime.now(timezone.utc)
        db=self.home/'data'/'trend_engine.sqlite3'
        if not db.exists():return None
        try:
            # sqlite3.Connection context managers do not close the connection.
            # closing() releases the readonly database handle on Windows too.
            with closing(sqlite3.connect(f'file:{db.as_posix()}?mode=ro',uri=True,timeout=1)) as con:
                observations=con.execute("SELECT title,url,collected_at FROM signals WHERE source='google_trends_rss' ORDER BY collected_at DESC LIMIT 60").fetchall()
        except sqlite3.DatabaseError:return None
        keyword_groups=(('job','resume','career','employment'),('budget','saving','money plan'),('website','small business','web design'),('photo','photography','product photos'),('routine','productivity','weekly plan'),('learning','education','tutorial'))
        for title,url,when in observations:
            try:
                age=now-datetime.fromisoformat(when)
                if age<timedelta(0) or age>timedelta(days=3):continue
            except (ValueError,TypeError):continue
            low=title.lower()
            for i,words in enumerate(keyword_groups):
                if any(w in low for w in words):return {'topic_index':i,'source':'google_trends_rss','source_title':title[:180],
                                                        'url':url,'interpretation':'Search-interest signal, NOT proof of sales or viewer demand'}
        return None

    def cycle(self):
        """Bounded daily safe local builds; unrelated trending headlines are ignored."""
        day=datetime.now(timezone.utc).toordinal()
        evidence=self.find_topic_evidence()
        index=evidence['topic_index'] if evidence else day%len(TOPICS)
        a=self.create('short',TOPICS[index][0],variant=day%97,render=bool(shutil.which('ffmpeg')),
                      use_ai=os.environ.get('OPERATION_BILLION_LOCAL_AI')=='1')
        # Only newly created and court-approved daily samples get local CPU polish.
        # Do not render repeatedly, install models, or make external uploads.
        if (a.get('status') == 'created' and a.get('verdict') == 'NOT GUILTY'
                and a.get('folder') and shutil.which('ffmpeg')):
            try:
                from .ai_media_lab import polish
                a['local_polish'] = polish(Path(a['folder']), width=270, fps=12)
            except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as exc:
                a['local_polish'] = {'complete': False, 'reason':type(exc).__name__, 'auto_publish':False}
        if evidence and a.get('folder'):
            atomic_text(Path(a['folder'])/'research_signal.json',json.dumps(evidence,indent=2))
        b=self.create('website',NICHES[day%len(NICHES)],variant=day%97)
        return {'short':{k:v for k,v in a.items() if k!='court'},'site':{k:v for k,v in b.items() if k!='court'},
                'content_signal':evidence or {'kind':'no_relevant_current_trend','selected':'evergreen educational idea'},
                'audited':self.audit_valid()}

