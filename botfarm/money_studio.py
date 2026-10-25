"""Court-gated zero-upfront-cost business launch kits and account preparation.

No new dependencies, remote execution, marketplace publication, payments, messages,
identity verification, or invented sales. A real account may be connected separately.
"""
from __future__ import annotations
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import re
import sqlite3

from .court import Proposal, adjudicate
from .creator_website_wing import Wing
from .workshop import atomic_text

# The workflow patterns reference public GitHub repositories, not vendored libraries.
# Tool catalogs are research leads: verify their current license and commercial terms.
TOOLS = [
    {'name':'PurffleShorts','url':'https://github.com/Chamanrajragu/purffle-shorts','function':'original short video pipeline','status':'review_optional','caution':'YouTube publishing needs authorized Google OAuth; TikTok relay may cost money'},
    {'name':'MoneyPrinterTurbo','url':'https://github.com/harry0703/MoneyPrinterTurbo','function':'video scripting, narration, captioning','status':'review_optional','caution':'paid providers are optional; pick Ollama/local/free rights-cleared media'},
    {'name':'Dyad','url':'https://github.com/dyad-sh/dyad','function':'local assisted website builder','status':'review_optional','caution':'open-source core; premium modules separately licensed'},
    {'name':'bolt.diy','url':'https://github.com/stackblitz-labs/bolt.diy','function':'local model web application prototyping','status':'review_optional','caution':'check production use and hosting licenses'},
    {'name':'Activepieces','url':'https://github.com/activepieces/activepieces','function':'workflow triggers and integrations','status':'review_optional','caution':'self-hosting and service connections may have resource costs'},
    {'name':'n8n','url':'https://github.com/n8n-io/n8n','function':'optional visual workflows','status':'research_only','caution':'Sustainable Use License; not standard OSI open source'},
    {'name':'FFmpeg','url':'https://github.com/FFmpeg/FFmpeg','function':'local MP4 assembly','status':'existing_optional','caution':'check codecs and asset rights'},
    {'name':'Ollama','url':'https://github.com/ollama/ollama','function':'local AI research and drafts','status':'existing_optional','caution':'model weights have independent license terms'},
    {'name':'Hugo','url':'https://github.com/gohugoio/hugo','function':'free static website building','status':'review_optional','caution':'hosting sites have their own commerce terms'},
    {'name':'Lighthouse','url':'https://github.com/GoogleChrome/lighthouse','function':'permitted website quality diagnostics','status':'review_optional','caution':'no unauthorized probes or invented audit results'},
    {'name':'Crawl4AI','url':'https://github.com/unclecode/crawl4ai','function':'public website research','status':'review_optional','caution':'follow sites rules and never defeat anti-bot controls'},
    {'name':'whisper.cpp','url':'https://github.com/ggml-org/whisper.cpp','function':'local media transcription','status':'review_optional','caution':'use authorized media and licensed speech models'},
    {'name':'Piper','url':'https://github.com/rhasspy/piper','function':'voice drafts','status':'review_optional','caution':'voice model license and commercialization vary'},
    {'name':'VTracer','url':'https://github.com/visioncortex/vtracer','function':'convert owned artwork to SVG','status':'review_optional','caution':'vectorization does not grant rights to an image'},
    {'name':'WeasyPrint','url':'https://github.com/Kozea/WeasyPrint','function':'HTML to printable PDFs','status':'review_optional','caution':'Windows setup needs dependencies'},
]

@dataclass(frozen=True)
class Method:
    label: str
    buyer: str
    deliverable: str
    category: str
    sample: str | None
    platform: str
    measure: str
    caveat: str
    steps: tuple[str,...]

METHODS: dict[str,Method] = {
'original_shorts': Method('Original educational Shorts','viewers seeking one useful idea','original 9:16 video with checked script and captions','creator','short','YouTube / TikTok (owner-authenticated)','authentic views, watch time, subscribers','Creator monetization thresholds vary; avoid repetitive template spam',('Choose a specific problem','Verify facts and script','Create a five-scene sample and MP4','Review originality and disclosures','Connect owner channel and publish only when authorized')),
'video_editing': Method('Short-form video editing service','creators with permission to share raw footage','licensed client clip with captions and edits','service','short','direct client proposal','replies, quotes, paid completed jobs','Never download or repurpose others footage without permission',('Produce sample using your own media','Define turnaround and revisions','Prepare a truthful portfolio example','Seek permission before touching client media','Measure inquiries and completed orders')),
'captions': Method('Captioning and subtitles','creators with media they own','captioned sample clip and SRT file','service','short','portfolio / client direct','inquiries, sample acceptance','Do not invent transcripts or clone voices',('Make sample with your own footage','Define languages and accuracy standards','Review timing and accessibility','Create an opt-in service offer','Measure replies and paid jobs')),
'educational_youtube': Method('Original long-form teaching videos','students and hobby learners','original video storyboard and script','creator','youtube','YouTube','retention, viewers returning, subscribers','Avoid unsourced facts and impersonation',('Select a lesson with genuine value','Research reliable sources','Draft original multi-part lesson','Review factual accuracy','Measure viewing and feedback')),
'website_service': Method('Local business website service','local businesses requesting redesign','mobile-responsive demonstration homepage','service','website','consensual outreach / portfolio','legitimate consultations, closed deals','Demo is fictional until a client authorizes real claims',('Choose a niche','Build fictional demo','Assess a user-provided website only with permission','Create honest scope and quote','Record actual opt-in inquiries')),
'landing_pages': Method('Landing-page design','independent makers with approved product details','responsive landing-page prototype','service','website','portfolio / direct client','qualified inquiries, accepted quotes','No fake testimonials or false claims',('Pick a real customer pain point','Build original static demo','Test phone layouts','Prepare deliverables and scope','Seek interested clients ethically')),
'web_tools': Method('Tiny web utilities','people with simple repeatable problems','static prototype of a useful web tool','software','website','own portfolio or permitted software marketplace','real users, repeat usage, requested features','No guarantees of a product-market fit',('Identify small repetitive task','Prototype locally','Validate function and privacy','Share demo only after approval','Collect real usage evidence')),
'digital_stickers': Method('Downloadable vector stickers','designers and planners','original sticker artwork and optional SVG','digital',None,'eligible digital storefront','visits, clicks, legitimate purchases','Do not assume every eBay category permits downloadable goods',('Research niche and originality','Create rights-cleared art','Export transparent/vector formats','Prepare store listing draft','Measure real sales after approved launch')),
'printable_planners': Method('Printable planners','students, organizers, families','original printable planning sheets','digital',None,'eligible digital storefront','real listing clicks and purchases','Check usability and file quality',('Define precise target user','Produce a functional sample','Proofread printable pages','Prepare branded listing draft','Test real customer response')),
'resume_templates': Method('Resume and cover-letter kits','job seekers','editable original template bundle','digital',None,'eligible digital storefront','legitimate downloads and feedback','No guaranteed employment claims',('Choose entry-level target','Prepare accessible examples','Test edits in common editors','Create listing draft','Record user feedback')),
'newsletter_services': Method('Newsletter formatting service','small newsletter publishers','consent-based original newsletter template','service',None,'opt-in service outreach','interested replies and paid projects','Never bulk-send unsolicited messages',('Create original layout','Define editorial scope','Prepare one sample newsletter','Offer to opted-in prospects','Track confirmed interest')),
'podcast_clip_service': Method('Authorized podcast clipping','podcast owners','short captioned clips from licensed recordings','service','short','permission-based portfolio','engagement and signed jobs','Written permission for third-party media required',('Offer clipping to rights holder','Get footage rights','Make approved sample clip','Review captions and credits','Track client feedback')),
'website_audits': Method('Website usability audit','owners seeking accessibility improvements','evidence-based performance checklist','service','website','client-approved proposal','real audit requests','Do not claim a Lighthouse test was run unless it was',('Use one user-approved URL','Run permitted basic accessibility checks','Document real evidence','Write prioritized recommendations','Record consultations')),
'document_design': Method('Business document design','small teams and freelancers','editable proposals and report layouts','digital',None,'eligible digital storefront','legitimate orders and user ratings','Check font and asset commercial rights',('Pick repeated document need','Design original structure','Test edits and page breaks','Provide license terms','Collect honest feedback')),
'creator_thumbnails': Method('Original thumbnails and channel banners','video creators','original themed thumbnail concepts','service',None,'creative services portfolio','real inquiries and contracts','No celebrity likeness or misleading clickbait',('Select content niche','Design original mockup','Verify text and visuals','Prepare service package','Record buyer interest')),
'virtual_assistant': Method('Digital admin and data cleanup','business owners with permission','anonymized work demonstration','service',None,'authorized freelance services','qualifying leads, paid hours','Client data requires permission and protection',('Choose one precise task','Build fictional demo','Document privacy controls','Set honest service scope','Collect client interest')),
}

ACCOUNTS = [
    {'kind':'digital_shop','choices':['Ko-fi shop','Gumroad','other eligible digital storefront'],'owner_steps':['Create storefront yourself','Agree to seller policies','Verify email and payouts in platform','Check listing and transaction fees'],'bot_prepares':['preview files','draft titles and tags','delivery folder','customer reply drafts'],'connected':False},
    {'kind':'creator_channel','choices':['YouTube','TikTok','Instagram'],'owner_steps':['Create and verify channel','Complete platform/age requirements','Grant approved OAuth API access only when ready','Review synthetic media and originality rules'],'bot_prepares':['original MP4 draft','cover and subtitles','draft upload metadata'],'connected':False},
    {'kind':'client_outreach','choices':['dedicated business email','contact forms that invite proposals'],'owner_steps':['Create business inbox','Set real identity and contact address','Review CAN-SPAM and recipient preferences','Approve each outreach integration'],'bot_prepares':['proposal','unsent personalized draft','follow-up plan'],'connected':False},
    {'kind':'portfolio','choices':['self-hosted static site','commercially permitted static hosting'],'owner_steps':['Choose host with business use permitted','Approve a domain/URL if needed','Review content and privacy policy'],'bot_prepares':['local HTML site','portfolio copy','accessibility checklist'],'connected':False},
]

def clean_topic(value):
    value=' '.join(str(value).split())
    if not 3<=len(value)<=100 or any(ord(c)<32 for c in value):
        raise ValueError('Topic must contain 3-100 printable characters')
    return value

class MoneyStudio:
    def __init__(self, home):
        self.home=Path(home)
        db_dir=self.home/'data'; db_dir.mkdir(parents=True,exist_ok=True)
        self.db=db_dir/'money_studio.sqlite3'
        with self.connect() as con:
            con.execute('''CREATE TABLE IF NOT EXISTS kits (
                fingerprint TEXT PRIMARY KEY, method TEXT NOT NULL, topic TEXT NOT NULL,
                verdict TEXT NOT NULL, folder TEXT, created TEXT NOT NULL, digest TEXT NOT NULL)''')
            con.execute('''CREATE TABLE IF NOT EXISTS audit (
                seq INTEGER PRIMARY KEY, fingerprint TEXT NOT NULL, previous TEXT NOT NULL, digest TEXT NOT NULL)''')
    @contextmanager
    def connect(self):
        con=sqlite3.connect(self.db,timeout=8)
        con.row_factory=sqlite3.Row
        try:
            yield con
            con.commit()
        finally:con.close()
    def audit_ok(self):
        with self.connect() as con:
            prev='GENESIS';seen=[]
            for row in con.execute('SELECT * FROM audit ORDER BY seq'):
                digest=hashlib.sha256((prev+'|'+row['fingerprint']).encode()).hexdigest()
                if row['previous']!=prev or row['digest']!=digest:return False
                prev=digest;seen.append(row['fingerprint'])
            rows=[dict(row) for row in con.execute('SELECT * FROM kits ORDER BY rowid')]
            if seen!=[r['fingerprint'] for r in rows]:return False
            for row in rows:
                expected=hashlib.sha256(json.dumps({k:row[k] for k in ('fingerprint','method','topic','verdict','folder','created')},sort_keys=True).encode()).hexdigest()
                if expected!=row['digest']:return False
            return True
    def create(self,method,topic,make_sample=False):
        if method not in METHODS:raise ValueError('Unknown money-making technique')
        if not self.audit_ok():raise RuntimeError('Business kit audit invalid; further writing disabled')
        topic=clean_topic(topic)
        m=METHODS[method]
        fp=hashlib.sha256(json.dumps([method,topic,make_sample],sort_keys=True).encode()).hexdigest()
        with self.connect() as con:
            row=con.execute('SELECT * FROM kits WHERE fingerprint=?',(fp,)).fetchone()
            if row:return {'status':'existing','verdict':row['verdict'],'folder':row['folder'],'fingerprint':fp}
        ruling=adjudicate(Proposal(bot_key='money_studio_'+method,title='Local launch plan: '+topic,action='generate_local_draft',expected_revenue_claim='unknown'))
        folder=None;sample=None
        if ruling.verdict=='NOT GUILTY':
            target=self.home/'output'/'money_launch_kits'/fp[:16]
            target.mkdir(parents=True,exist_ok=True)
            if make_sample and m.sample:
                created=Wing(self.home).create(m.sample,topic)
                if created['verdict']!='NOT GUILTY':raise RuntimeError('Sample court rejected')
                sample={'kind':m.sample,'folder':created['folder'],'status':'local_only'}
            plan={'method':method,'name':m.label,'topic':topic,'target_customer':m.buyer,
                  'deliverable':m.deliverable,'buyer_channel_to_review':m.platform,'trial_metrics':m.measure,
                  'steps':list(m.steps),'caveat':m.caveat,'sample':sample,
                  'day_7':'Review real impressions and engagement only if actually launched; never infer results from drafts',
                  'day_14':'If launched and no validated traction, retire and propose a different technique; if never launched, mark UNLAUNCHED not FAILURE',
                  'permission_status':'NOT CONNECTED','publishing':'NOT PERFORMED','customer_contact':'NOT PERFORMED',
                  'cost_limit_usd':0,'revenue_verified_usd':0,'market_demand_verified':False,
                  'court_verdict':ruling.verdict}
            atomic_text(target/'LAUNCH_PLAN.json',json.dumps(plan,indent=2,ensure_ascii=False))
            checklist='\n'.join(f'- [ ] {line}' for line in m.steps)
            atomic_text(target/'CHECKLIST.md',f'# {m.label}\n\nTarget: {topic}\n\n{checklist}\n\nRequires account authorization before publication or outreach.\n')
            folder=str(target)
        stamp=datetime.now(timezone.utc).isoformat()
        record={'fingerprint':fp,'method':method,'topic':topic,'verdict':ruling.verdict,'folder':folder,'created':stamp}
        digest=hashlib.sha256(json.dumps(record,sort_keys=True).encode()).hexdigest()
        with self.connect() as con:
            con.execute('BEGIN IMMEDIATE')
            if con.execute('SELECT fingerprint FROM kits WHERE fingerprint=?',(fp,)).fetchone():return {'status':'existing','fingerprint':fp}
            con.execute('INSERT INTO kits(fingerprint,method,topic,verdict,folder,created,digest) VALUES (?,?,?,?,?,?,?)',(*record.values(),digest))
            previous=con.execute('SELECT digest FROM audit ORDER BY seq DESC LIMIT 1').fetchone()
            prev=previous['digest'] if previous else 'GENESIS'
            chain=hashlib.sha256((prev+'|'+fp).encode()).hexdigest()
            con.execute('INSERT INTO audit(fingerprint,previous,digest) VALUES (?,?,?)',(fp,prev,chain))
        return {'status':'created','verdict':ruling.verdict,'folder':folder,'sample':sample,'fingerprint':fp,'audit_valid':self.audit_ok()}
    def daily_idea(self, now=None):
        """One new business-method startup kit each UTC day, no account activity.

        A bounded daily rotation ensures the autopilot explores genuinely different
        categories instead of spamming variants of one product. It does not imply
        the idea has been published or exposed to customers.
        """
        day=(now or datetime.now(timezone.utc)).date().toordinal()
        keys=tuple(METHODS)
        key=keys[day%len(keys)]
        label=METHODS[key].label
        topic=f'{label}: original practical example for first-time customers'
        return self.create(key,topic,make_sample=bool(METHODS[key].sample))

    def report(self):
        with self.connect() as con:
            rows=[dict(r) for r in con.execute('SELECT method,topic,verdict,folder,created FROM kits ORDER BY rowid DESC LIMIT 30')]
        return {'kits':rows,'audit_valid':self.audit_ok(),'real_revenue_verified':0,'accounts_connected':0}

def options():
    return [{'key':key,'category':m.category,'offer':m.label,'sample_supported':bool(m.sample),
             'buyer':m.buyer} for key,m in METHODS.items()]
