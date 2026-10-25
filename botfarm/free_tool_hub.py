"""Free-only tool selection, public GitHub candidate discovery, and startup playbooks.

Never runs, installs, clones, posts, pays, emails, or uploads third-party code.
Unreviewed GitHub results are RESEARCH CANDIDATES, not production tools.
Software licenses do not establish licenses for model weights, voices, media or outputs.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sqlite3
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
from .workshop import atomic_text

MAX_RESPONSE = 240_000
MIN_SCAN_INTERVAL = timedelta(hours=24)

@dataclass(frozen=True)
class Tool:
    key: str
    name: str
    repo: str
    jobs: tuple[str, ...]
    kind: str               # built_in, free_local_optional
    binary: str
    cost: str
    requirements: str
    rights: str
    install: str
    caution: str


def t(key, name, repo, jobs, kind='free_local_optional', binary='',
      requirements='Free local app; install separately.', rights='Review third-party inputs and licenses.',
      install='Visit official repository and follow its documented Windows install.', caution=''):
    return Tool(key,name,repo,tuple(jobs.split(',')),kind,binary,'$0 software subscription / no paid API required',requirements,rights,install,caution)

TOOLS = (
    t('farm','Operation Billion built-in creators','local://botfarm','videos,websites,stickers,templates,design,documents,content,services',
      'built_in','', 'Python 3.11+; CPU only; original draft files.',
      'Works only on original generated assets; inspect factual and sales claims.',
      'Already included in Operation Billion; no setup.','Sample assets are not sales, real users, or externally published media.'),
    t('ffmpeg','FFmpeg','https://github.com/FFmpeg/FFmpeg','videos,captions,content,audio',binary='ffmpeg',
      requirements='CPU video encoding possible on ordinary laptops.',
      rights='FFmpeg LGPL/GPL build and codecs differ; only use your own or properly licensed video/audio.',
      install='Optional: install an official-linked FFmpeg Windows build and add ffmpeg to PATH.'),
    t('ollama','Ollama','https://github.com/ollama/ollama','ideas,writing,websites,content,documents,services,videos,automation',binary='ollama',
      requirements='RAM needed for downloaded local model; smaller models on low-spec PCs.',
      rights='Each downloaded model has separate weights/license; use only a model allowing your intended commercial use.',
      install='Install Ollama for Windows from ollama.com; explicitly choose a small license-checked model.',
      caution='No model automatically downloaded. Local Ollama endpoint only.'),
    t('kokoro','Kokoro TTS','https://github.com/hexgrad/kokoro','voice,audio,videos,content',
      requirements='Local inference engine and model download; CPU performance varies.',
      rights='Kokoro-82M weights labeled Apache-2.0; check voice/model/dependency licenses.',
      install='Follow Kokoro official GitHub install and reviewed model instructions.'),
    t('piper','Piper voice engine','https://github.com/rhasspy/piper','voice,audio,videos',binary='piper',
      requirements='Download binaries/voice models once; lightweight local synthesis possible.',
      rights='Voice licenses vary independently; do not use a model with unknown/non-commercial rights.',
      install='Install a trusted Piper binary and a separately verified, commercially permissible voice.'),
    t('whisper','Whisper.cpp','https://github.com/ggml-org/whisper.cpp','captions,transcription,audio,videos',binary='whisper-cli',
      requirements='Local STT model download; CPU compatible with smaller models.',
      rights='Only transcribe audio you own/have permission to use; verify model license.',
      install='Download/build the official project and a suitable licensed small model.'),
    t('comfy','ComfyUI','https://github.com/Comfy-Org/ComfyUI','images,stickers,videos,design',
      requirements='Heavy local models; practical speed often needs a capable GPU and free disk.',
      rights='Model/checkpoint licenses may restrict commercial output even when ComfyUI code is free.',
      install='Optional after RAM/GPU check: ComfyUI local desktop + approved model.'),
    t('inkscape','Inkscape','https://inkscape.org','design,stickers,templates,images',binary='inkscape',
      requirements='Windows desktop application; no paid service.',
      rights='Generated designs must be original or appropriately licensed.',
      install='Install from inkscape.org then enable optional command-line export.'),
    t('vtracer','VTracer','https://github.com/visioncortex/vtracer','stickers,design,images',binary='vtracer',
      rights='Vectorization does not clear copyrights of input images.',
      install='Install from official repository/release; inspect SVG results before selling.'),
    t('hugo','Hugo','https://github.com/gohugoio/hugo','websites,content,newsletters,services',binary='hugo',
      requirements='Free local static site generator; hosting is a separate choice.',
      rights='Themes, stock assets and public hosting have their own licenses/terms.',
      install='Install Hugo extended from gohugo.io; generate and preview locally.'),
    t('lighthouse','Lighthouse','https://github.com/GoogleChrome/lighthouse','websites,services,research',binary='lighthouse',
      requirements='Chrome and recent Node.js; Chrome DevTools has built-in Lighthouse UI.',
      rights='Only assess publicly accessible permitted sites at respectful rates.',
      install='In Chrome DevTools open Lighthouse; optional npm CLI if Node installed.'),
    t('playwright','Playwright Python','https://github.com/microsoft/playwright-python','websites,services,automation',
      requirements='Requires separate Python package and browser download.',
      rights='Use only for sites/workflows allowed by site rules; do not bypass verification.',
      install='Optional: install playwright in separate virtualenv; run browser install manually.'),
    t('crawl4ai','Crawl4AI','https://github.com/unclecode/crawl4ai','research,ideas,services',
      requirements='Local crawling library + browsers; heavier than built-in public RSS/API scout.',
      rights='Honor robots.txt, site terms, copyright and rate limits.',
      install='Optional: follow official Crawl4AI local installation; no managed API.'),
    t('searxng','SearXNG','https://github.com/searxng/searxng','research,ideas',
      requirements='Requires self-hosting; many public instances have rate limits or prohibit automated use.',
      rights='AGPL-3.0 code and upstream search provider rules; do not scrape Google around restrictions.',
      install='Optional Docker/self-host per official instructions. Do not use strangers\' instances without permission.'),
    t('weasyprint','WeasyPrint','https://github.com/Kozea/WeasyPrint','documents,templates,services',
      requirements='Python package with Windows rendering dependencies.',
      rights='Check fonts, illustrations and template content licensing.',
      install='Optional: follow official Windows install; built-in templates work without it.'),
    t('docx','python-docx','https://github.com/python-openxml/python-docx','documents,templates,services',
      requirements='Free Python library (additional local installation).',
      rights='Original editable Word content; no proprietary templates copied.',
      install='Optional: python -m pip install python-docx'),
    t('pptx','python-pptx','https://github.com/scanny/python-pptx','documents,templates,services',
      requirements='Free Python library (additional local installation).',
      rights='Original slides and designs; use images you are allowed to sell.',
      install='Optional: python -m pip install python-pptx'),
    t('kdenlive','Kdenlive','https://github.com/KDE/kdenlive','videos,content',binary='kdenlive',
      requirements='Free GUI editor; no cloud key.',
      rights='Use your own or properly licensed media.',
      install='Install from kdenlive.org if you need manual polish.'),
    t('shotcut','Shotcut','https://github.com/mltframework/shotcut','videos,content',binary='shotcut',
      requirements='Free GUI editor; local CPU/GPU usage.',
      rights='Use your own/cleared footage and music.',
      install='Install from shotcut.org.'),
    t('obs','OBS Studio','https://github.com/obsproject/obs-studio','videos,content,services',binary='obs64',
      requirements='Local recording/capture; verify machine performance.',
      rights='Record your own or consented presentations, not third-party material.',
      install='Install from obsproject.com.'),
    t('audacity','Audacity','https://github.com/audacity/audacity','audio,voice,videos',binary='audacity',
      requirements='Free desktop audio editing software.',
      rights='Edit only authorized sound recordings.',
      install='Install from audacityteam.org.'),
)
TOOL_MAP = {tool.key: tool for tool in TOOLS}
assert len(TOOL_MAP) == len(TOOLS)

# Five actionable, no-spend steps per technique; do not imply real publication.
PLAYBOOKS = {
    'videos': ('Choose an original useful educational angle from dated public research.',
               'Make a factual script, scenes, original graphics, caption file and thumbnail.',
               'Render locally with FFmpeg if available; check sound/media/model rights.',
               'Create creator accounts yourself; review platform requirements before any upload.',
               'Only after real posting: track retention, views, clicks and conversion; pivot using 7/14-day rules.'),
    'websites': ('Choose one small-business niche; investigate a customer need using permitted public sources.',
                 'Generate an original fictional website demo using the built-in Website Factory.',
                 'Audit mobile readability, links, accessibility and truthfulness with local tools.',
                 'Prepare a specific, unsent B2B pitch; you must authorize and handle lawful outreach.',
                 'If a real client agrees, arrange written scope, assets, free hosting terms and actual payment.'),
    'stickers': ('Research a precise audience and the kinds of digital sticker packs they request.',
                 'Create original PNG/SVG assets without trademarks, celebrities or unlicensed media.',
                 'QC resolution, transparency, vector paths, readme and rights provenance.',
                 'Prepare a storefront draft; owner creates and verifies seller/payout accounts.',
                 'Only after listing: track customer visits and paid conversions; pivot based on evidence.'),
    'documents': ('Select one buyer workflow that a useful original template improves.',
                   'Create accessible original template pages, DOCX/PDF where local tools support it.',
                   'Verify formulas, typography, instructions, and format compatibility.',
                   'Prepare product packet and clear preview; seller account/payout approval are external.',
                   'Collect real feedback and validate with inquiries or paid results, never simulated profit.'),
    'services': ('Choose a specific service that can be delivered with free tools and your actual skills.',
                 'Research public demand and prepare a sample for a fictional demonstration customer.',
                 'Define truthful scope, turnaround, deliverables, and any free-tool limitations.',
                 'Draft a personalized offer; owner authorizes outreach and client agreement.',
                 'Record real replies, accepted proposals and payment after actual delivery.'),
    'research': ('Gather dated public data from permitted feeds/APIs with provenance links.',
                 'Form a buyer-specific hypothesis; a viral topic is not proof of demand.',
                 'Send local trial actions through the court and reject unsupported monetization claims.',
                 'Make an original sample and identify where the true audience spends attention.',
                 'Retire tests with qualified evidence; separate unlaunched plans from market failures.'),
    'audio': ('Find a voiceover or audio-cleanup task using your own recorded material.',
              'Use original scripts and free local editing; select only license-cleared voice models.',
              'Verify pronunciation, intelligibility, accuracy and media rights.',
              'Prepare a sample for a creator or customer; do not impersonate real speakers.',
              'After an authorized launch, measure inquiries and completed paid orders.'),
    'captions': ('Choose a permitted original audio/video sample to caption.',
                 'Generate captions by hand or locally with a license-checked transcription model.',
                 'Review timing, punctuation, names, accessibility and confidentiality.',
                 'Prepare a clear captioning-service offer with delivery examples.',
                 'Track verified inquiries and paid work, not algorithmically guessed revenue.'),
    'ideas': ('Look for public problems reported by actual people or businesses.',
              'Find free/open-source candidate tools; record evidence and license caveats.',
              'Propose an original product or service and have the court test costs and legality.',
              'Implement only bounded locally approved actions with supported builders.',
              'If guilty or unproductive, choose a genuinely different technique without repeating failures.'),
    'content': ('Identify a narrow helpful creator niche rather than a viral celebrity trend.',
                'Create original factual posts, visuals and scripts with cleared media.',
                'Check usefulness and platform restrictions on repetitive/AI-generated content.',
                'Prepare previews, titles, CTA and links for an owner-run account.',
                'After publishing with authorization, track genuine retention and customer interest.'),
    'templates': ('Choose a buyer pain point and a concrete printable or editable deliverable.',
                  'Create an original editable draft using built-in templates and optional open-source formatters.',
                  'Inspect readability, licensing, mobile/print size and instructions.',
                  'Create a storefront listing packet but do not publish without an authorized account.',
                  'Track real marketplace evidence and retire poor fits.'),
}
ALIASES = {'youtube':'videos','tiktok':'videos','reels':'videos','shorts':'videos','video':'videos',
           'website':'websites','landing':'websites','local-business':'services','freelance':'services',
           'sticker':'stickers','digital':'templates','products':'templates','voice':'audio','subtitle':'captions',
           'product':'templates','business':'services','affiliate':'content','ai':'ideas',
           'newsletters':'content','blog':'content','automation':'ideas','design':'stickers'}

# Fixed public search prompts; fetched only when explicitly --live or live autopilot.
SEARCH_QUERIES = (
    'open source video editor text to speech',
    'open source landing page website builder',
    'open source digital product generator python',
)
GITHUB_REPO = re.compile(r'^https://github\.com/[A-Za-z0-9_.-]{1,80}/[A-Za-z0-9_.-]{1,100}/?$')


def canonical_need(need: str) -> str:
    need = str(need).lower().strip()
    return ALIASES.get(need, need)


def available_tools(need: str = '', which=shutil.which):
    need = canonical_need(need)
    if need and need not in PLAYBOOKS:
        raise ValueError('Unknown need. Choose: ' + ', '.join(sorted(PLAYBOOKS)))
    selected = [tool for tool in TOOLS if not need or need in tool.jobs or tool.key == 'farm']
    output = []
    for item in selected:
        installed = item.kind == 'built_in' or bool(item.binary and which(item.binary))
        output.append({**asdict(item), 'currently_usable':installed,
                       'status':'ready_local' if installed else 'optional_not_verified_installed',
                       'downloaded_by_farm':False})
    return output


def free_doctor(which=shutil.which):
    """This only reports executable presence, not installed model weights/licensing."""
    rows=available_tools(which=which)
    return {'checked':len(rows),'ready_local':[r['key'] for r in rows if r['currently_usable']],
            'optional_not_verified':[r['key'] for r in rows if not r['currently_usable']],
            'paid_api_required':False, 'automatically_installed':False,
            'model_weights_and_commercial_rights':'MUST_CHECK_SEPARATELY',
            'gpu_capability':'NOT_DETECTED',
            'real_seller_or_publishing_accounts_connected':False}


def iso_now(now=None):
    value=now or datetime.now(timezone.utc)
    if value.tzinfo is None: raise ValueError('Timezone-aware now required')
    return value.astimezone(timezone.utc).isoformat()


def safe_words(text, maxlen=150):
    if not isinstance(text,str): return ''
    return ' '.join(''.join(ch for ch in text if ch.isprintable()).split())[:maxlen]


def fetch_github(query: str, fetcher=None):
    """Fixed public GitHub search only. No auth, shell, repo cloning or execution."""
    if query not in SEARCH_QUERIES: raise ValueError('Only fixed, reviewed searches are permitted')
    url='https://api.github.com/search/repositories?'+urllib.parse.urlencode(
        {'q':query+' archived:false','sort':'updated','order':'desc','per_page':5})
    if fetcher is None:
        def fetcher(endpoint):
            req=urllib.request.Request(endpoint,headers={'User-Agent':'OperationBillion-FreeToolScout/1.0',
                                                         'Accept':'application/vnd.github+json'})
            with urllib.request.urlopen(req,timeout=9) as resp:
                if urllib.parse.urlsplit(resp.geturl()).hostname!='api.github.com':
                    raise ValueError('Unexpected GitHub redirect')
                return resp.read(MAX_RESPONSE+1)
    raw=fetcher(url)
    if not isinstance(raw,bytes) or len(raw)>MAX_RESPONSE: raise ValueError('Oversized or malformed response')
    obj=json.loads(raw.decode('utf-8'))
    if not isinstance(obj,dict) or not isinstance(obj.get('items'),list): raise ValueError('Bad API response')
    out=[]
    for row in obj['items'][:5]:
        if not isinstance(row,dict): continue
        repo=row.get('html_url',''); fullname=row.get('full_name','')
        if not isinstance(repo,str) or not GITHUB_REPO.fullmatch(repo):continue
        if not isinstance(fullname,str) or repo.rstrip('/').lower() != ('https://github.com/'+fullname).lower():continue
        if row.get('archived') or row.get('disabled') or row.get('private'): continue
        lic=row.get('license') or {}
        spdx=safe_words(lic.get('spdx_id','UNKNOWN') if isinstance(lic,dict) else 'UNKNOWN',40)
        out.append({'url':repo.rstrip('/'),'name':safe_words(fullname,150),
                    'description':safe_words(row.get('description',''),240),
                    'spdx_reported_by_github':spdx,
                    'language':safe_words(row.get('language','') or '',32),
                    'status':'unreviewed_candidate_only', 'can_auto_execute':False,
                    'cost_verified':False,'rights_verified':False,'may_require_paid_services':True,
                    'source':'GitHub search API','search_query':query})
    return out


class FreeToolHub:
    """Local tamper-evident ledger for GitHub scout results and generated plans."""
    def __init__(self,home):
        self.home=Path(home)
        path=self.home/'data'/'free_tool_hub.sqlite3'
        path.parent.mkdir(parents=True,exist_ok=True)
        self.db=path
        with self.connect() as conn:
            conn.executescript('''
            CREATE TABLE IF NOT EXISTS findings(
              id INTEGER PRIMARY KEY, query TEXT NOT NULL, payload TEXT NOT NULL,
              created_at TEXT NOT NULL, prev_hash TEXT NOT NULL, chain_hash TEXT NOT NULL,
              UNIQUE(query, payload));
            CREATE TABLE IF NOT EXISTS scans(query TEXT PRIMARY KEY, last_scanned TEXT NOT NULL);
            ''')

    def connect(self):
        return _Connection(self.db)

    @staticmethod
    def _digest(previous,query,payload,created):
        return hashlib.sha256(json.dumps([previous,query,payload,created],separators=(',',':')).encode()).hexdigest()

    def audit_valid(self):
        with self.connect() as c:
            prev='GENESIS'
            for row in c.execute('SELECT query,payload,created_at,prev_hash,chain_hash FROM findings ORDER BY id'):
                if row['prev_hash']!=prev or self._digest(prev,row['query'],row['payload'],row['created_at'])!=row['chain_hash']:
                    return False
                prev=row['chain_hash']
        return True

    def scan(self,live=False,now=None,fetcher=None,limit=3):
        if not self.audit_valid(): raise RuntimeError('Free-tool research audit invalid; halted')
        if not live:
            return {'online':False,'new_candidates':0,'attempted_queries':0,'note':'Offline free-tool catalogue is still available.'}
        if not 1<=limit<=3:raise ValueError('Limit must be 1..3')
        moment=datetime.fromisoformat(iso_now(now)); results=[]; failures=[];attempted=0
        for query in SEARCH_QUERIES[:limit]:
            with self.connect() as c:
                last=c.execute('SELECT last_scanned FROM scans WHERE query=?',(query,)).fetchone()
            if last and moment-datetime.fromisoformat(last[0])<MIN_SCAN_INTERVAL:continue
            attempted+=1
            try:
                found=fetch_github(query,fetcher=fetcher)
            except (ValueError, OSError, TimeoutError, json.JSONDecodeError, UnicodeDecodeError) as e:
                failures.append({'query':query,'reason':type(e).__name__})
                continue
            with self.connect() as c:
                c.execute('BEGIN IMMEDIATE')
                previous=c.execute('SELECT chain_hash FROM findings ORDER BY id DESC LIMIT 1').fetchone()
                prev=previous[0] if previous else 'GENESIS'
                for item in found:
                    payload=json.dumps(item,sort_keys=True,separators=(',',':'))
                    old=c.execute('SELECT 1 FROM findings WHERE query=? AND payload=?',(query,payload)).fetchone()
                    if old:continue
                    stamp=iso_now(now)
                    chain=self._digest(prev,query,payload,stamp)
                    c.execute('INSERT INTO findings(query,payload,created_at,prev_hash,chain_hash) VALUES(?,?,?,?,?)',
                              (query,payload,stamp,prev,chain))
                    prev=chain
                    results.append(item)
                c.execute('INSERT INTO scans(query,last_scanned) VALUES(?,?) ON CONFLICT(query) DO UPDATE SET last_scanned=excluded.last_scanned',
                          (query,iso_now(now)))
        if not self.audit_valid(): raise RuntimeError('Free-tool evidence integrity check failed')
        return {'online':True,'new_candidates':len(results),'attempted_queries':attempted,
                'failed_queries':failures,'candidates_require_review':True,
                'paid_dependent_candidates_never_auto_enabled':True}

    def findings(self,limit=25):
        with self.connect() as c:
            rows=c.execute('SELECT id,payload,created_at FROM findings ORDER BY id DESC LIMIT ?', (min(max(int(limit),1),100),)).fetchall()
        return [{**json.loads(r['payload']),'evidence_id':r['id'],'observed_at':r['created_at']} for r in rows]

    def plan(self,need,topic,execute_local=False):
        need=canonical_need(need)
        if need not in PLAYBOOKS:raise ValueError('No verified zero-cost playbook for '+need)
        topic=safe_words(topic,100)
        if not topic:raise ValueError('Provide a useful topic')
        tools=available_tools(need)
        ready=[r['key'] for r in tools if r['currently_usable']]
        planned={'need':need,'topic':topic,'steps':PLAYBOOKS[need],
                 'tools_ready':[t for t in ready],
                 'optional_tools':[t['key'] for t in tools if not t['currently_usable']],
                 'startup_spend_ceiling_usd':0,'paid_api_keys_required':False,
                 'stage':'LOCAL_PLAN_NOT_LAUNCHED',
                 'court_rule':'External publishing, customer contact, payouts, model installs and spend still require authorization.',
                 'revenue_verified_usd':0,'validation_after_real_launch':'7-day early evidence review and 14-day decision; unlaunched is not failed demand.'}
        # Local builder is already court-controlled and audited. Nothing leaves this computer.
        if execute_local:
            if need not in ('videos','websites'):
                planned['execution']='No direct local builder for this category; prepared plan only.'
            else:
                from .creator_website_wing import Wing
                kind='short' if need=='videos' else 'website'
                result=Wing(self.home).create(kind, topic)
                planned['local_builder_result']=result
                planned['execution']='Local court-reviewed sample; nothing posted, emailed or sold.'
        slug=re.sub(r'[^a-z0-9]+','-',topic.lower()).strip('-')[:44] or 'plan'
        fingerprint=hashlib.sha256((need+'\0'+topic.lower()).encode()).hexdigest()[:12]
        folder=self.home/'output'/'free_tool_hub'/(need+'_'+slug+'_'+fingerprint)
        folder.mkdir(parents=True,exist_ok=True)
        atomic_text(folder/'free_plan.json',json.dumps(planned,indent=2,ensure_ascii=False))
        planned['saved_to']=str(folder/'free_plan.json')
        return planned


class _Connection:
    """sqlite3 context manager that ALSO closes (sqlite3.Connection.__exit__ does not)."""
    def __init__(self,path): self.path=path;self.con=None
    def __enter__(self):
        self.con=sqlite3.connect(self.path,timeout=8)
        self.con.row_factory=sqlite3.Row
        self.con.execute('PRAGMA busy_timeout=8000')
        return self.con
    def __exit__(self,type_,value,tb):
        try:
            if type_ is None:self.con.commit()
            else:self.con.rollback()
        finally:self.con.close()
