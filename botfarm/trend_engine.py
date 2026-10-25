"""Operation Billion v0.6: Google Trends RSS + GitHub/HN evidence -> runnable local startup kits.

No search-engine scraping, speculative income claims, payment, seller-account operations,
external outreach, or execution of code from researched GitHub repositories.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote, urlsplit

from .catalog import BY_KEY as BUILDERS
from .court import Proposal, adjudicate
from .opportunity_lab import BY_KEY, OpportunityLab, clean
from .quality import inspect, prepare_sell_kit
from .workshop import atomic_text, make_artifact

RSS_URL = 'https://trends.google.com/trending/rss?geo=US'
MAX_RSS_BYTES = 150_000
SOURCE_CAP = 100
MIN_REFRESH_HOURS = 6

# Only programmatic local builders that already exist and were tested in the farm.
# Anything not mapped is a fully specified startup plan, NOT a fictitious "completed business".
BUILD_MAP = {
    'template_market':'resume_template', 'education_materials':'learning_worksheets',
    'design_service':'local_service_flyer', 'website_audit':'website_pitch',
    'micro_utility':'price_calculator', 'newsletter_service':'newsletter_kit',
    'affiliate_editorial':'affiliate_review', 'podcast_assets':'social_caption_pack',
    'short_video_assets':'social_caption_pack', 'data_cleanup':'inventory_tracker',
    'local_event_assets':'digital_invitations', 'niche_research':'blog_outline',
    'open_source_support':'blog_outline', 'translation_editing':'cover_letter',
    'printable_games':'learning_worksheets', 'online_tutoring':'learning_worksheets',
    'transcription_captioning':'social_caption_pack', 'virtual_assistant':'study_planner',
    'stock_media':'icon_pack', 'print_on_demand':'pattern_designer',
}

# These tasks are human account/eligibility/fulfillment gates, not permissions to circumvent them.
STARTUP_STEPS = {
 'template_market':(
  'Choose ONE specific buyer problem, e.g. a one-page job-search tracker or restaurant inventory sheet.',
  'Make an original editable file and printable preview; proofread every label, formula and instruction.',
  'Check whether relevant buyers ask for this exact feature; compare genuine public alternatives without copying them.',
  'Prepare a title, clear license, price/fee estimate, five truthful benefit bullets and original screenshots.',
  'Have the owner open/verify a compatible digital shop and approve the first product listing.'),
 'education_materials':(
  'Pick a single grade-level skill and write measurable learning objectives.',
  'Produce five original exercises, an answer key, accessibility review and print-ready preview.',
  'Ask a qualified educator or consenting adult to check correctness and age appropriateness.',
  'Prepare descriptions accurately naming prerequisites and delivery formats.',
  'The owner confirms publishing account, rights and suitable category.'),
 'design_service':(
  'Select one real client type such as barbers, food trucks or local repair shops.',
  'Build three original sample flyers using fictional company details; verify rights and readability.',
  'Publish an owner-reviewed portfolio or share samples only with interested parties.',
  'Draft a scope, turnaround time, revision limit, and clear pricing quote.',
  'Have the owner approve any outreach and payment arrangements; never impersonate a real business.'),
 'website_audit':(
  'Choose a publicly accessible website from an owner-approved or permitted source.',
  'Run a bounded Lighthouse-style quality check on public pages where allowed; no penetration testing.',
  'Draft a reproducible report separating measured findings from optional recommendations.',
  'Create a before/after demonstration on fictional data and a scoped service offer.',
  'Have the owner review the outreach, quote, client consent and actual fulfillment ability.'),
 'micro_utility':(
  'Name one repetitive manual task and the person who performs it.',
  'Build and test a tiny local-only proof of concept using sample data; add usage instructions.',
  'Verify the tool helps at least five interested prospective users with the same problem.',
  'Draft transparent support terms, limitations and pricing without promising hosted uptime.',
  'Have the owner review licensing and any costs before external release.'),
 'newsletter_service':(
  'Define the niche reader and specific benefit of each issue.',
  'Prepare an original sample issue with attributed research and reusable format.',
  'Use a permission-based signup only; do not harvest addresses or send unsolicited bulk email.',
  'Track genuine subscribers, opens and replies where analytics are permitted.',
  'Have the owner create and approve the email provider account and required unsubscribe process.'),
 'affiliate_editorial':(
  'Choose a narrow product category with genuinely researchable buyer questions.',
  'Compile verifiable pros and cons, and clearly distinguish product specs from firsthand testing.',
  'Draft a disclosure and original comparison content; never fabricate product experience.',
  'Check approved affiliate program requirements and relevant retailer rules.',
  'Only the authorized owner can enroll and publish approved affiliate links.'),
 'data_cleanup':(
  'Identify a reproducible spreadsheet cleanup problem and define an acceptable output.',
  'Build a demonstration from entirely synthetic CSV data and show before/after validation.',
  'Record what data must never leave the customer’s environment.',
  'Create a transparent sample deliverable, service quote and acceptance checklist.',
  'Get permission before processing real client records; do not access private data autonomously.'),
 'online_tutoring':(
  'Select a subject the human tutor can confidently teach.',
  'Create an original 20-minute sample lesson, practice activity and feedback rubric.',
  'Verify tutoring platform eligibility, safeguarding and real human involvement.',
  'Measure requests for a lesson from consenting prospective students.',
  'Do not impersonate tutors, automate identity checks, or claim qualifications not held.'),
 'micro_saas_validation':(
  'Identify a costly repetitive workflow and name a specific buyer role.',
  'Create an offline prototype and a demo video or screenshots using fictional data.',
  'Interview five consenting target users and measure interest in a paid version.',
  'Document hosting, privacy, support, refund and payment-provider expenses before launch.',
  'Only the owner may authorize live hosting, subscription billing and account setup.'),
 'podcast_assets':(
  'Pick a specific creator niche and gather examples of public podcast artwork styles without copying them.',
  'Prepare a fictional show-note example, original cover draft and reusable media kit.',
  'Check typography, file size, pronunciation, factual claims and audio permissions.',
  'Offer the sample in a rights-safe portfolio and record qualified inbound requests.',
  'Owner approves all client communications, pricing, revisions and delivery.'),
 'short_video_assets':(
  'Choose one repeatable short-form video production problem for a defined creator audience.',
  'Draft original storyboard, caption variations, a shot list and a royalty-safe audio checklist.',
  'Test video dimensions, readability, duration, and accessibility on a short sample.',
  'Ask interested creators whether the pack saves actual editing time.',
  'Owner authorizes any public posting; do not copy trending music or reupload others videos.'),
 'local_event_assets':(
  'Select a hypothetical event such as a neighborhood fundraiser or workshop.',
  'Create an original invitation, schedule template and printable event checklist.',
  'Test dates, accessibility, legibility, color contrast and printer settings.',
  'Validate interest with event organizers and prepare a truthful listing proposal.',
  'Do not imply a fictional event exists or publish client details without consent.'),
 'niche_research':(
  'Find a narrowly defined buyer decision that requires a structured public research brief.',
  'Collect permitted sources with dates and separate evidence from speculation.',
  'Prepare an original short report, comparison matrix and source-revision log.',
  'Ask a potential buyer whether the report resolves their specific research question.',
  'Set clear pricing and deliverable scope only after a competent owner reviews accuracy.'),
 'open_source_support':(
  'Choose one permissively licensed tool that users struggle to set up or document.',
  'Read the license and official install instructions without running unidentified scripts.',
  'Write an original troubleshooting guide and test it in an isolated safe environment.',
  'Share a transparent sample of documentation or setup help through authorized channels.',
  'Do not claim the maintainers endorsed the service or promise paid support you cannot deliver.'),
 'translation_editing':(
  'Select languages and editing specialties that a qualified human can verify.',
  'Create before/after examples using original invented text and document editorial choices.',
  'Test accuracy, sensitive wording, formatting and client confidentiality.',
  'Prepare a scoped proofreading offer with explicit human quality review.',
  'Owner handles customer onboarding; do not offer unsupported language expertise.'),
 'printable_games':(
  'Choose a target age range and a game concept that does not use protected characters.',
  'Generate original puzzles and an answer key or simple game rules.',
  'Play-test with consenting participants and fix ambiguous rules or wrong answers.',
  'Prepare a clear printable preview, file format and product description.',
  'The owner reviews age suitability, intellectual property and storefront permissions.'),
 'transcription_captioning':(
  'Use your own sample audio or audio for which you have documented permission.',
  'Create a timed-caption example and transcript with speaker labels.',
  'Check timestamps and manually verify speech accuracy and punctuation.',
  'Show consent-based examples to eligible creators and track inquiries.',
  'Only process real client audio after approval and a privacy agreement.'),
 'open_source_bounties':(
  'Research only official public issues with explicit bounty terms and eligibility.',
  'Choose a small issue compatible with current programming skills and a safe license.',
  'Reproduce the problem locally without retrieving secrets or accessing private systems.',
  'Develop and test an original patch, then follow maintainer contribution guidelines.',
  'The owner submits contributions and receives any award; never claim a bounty is guaranteed.'),
 'virtual_assistant':(
  'Choose one repetitive task that a sole proprietor could legitimately delegate.',
  'Create a fictional scheduling, file-naming or checklist demonstration.',
  'Document exactly which personal information and account permissions the task would require.',
  'Offer a defined trial scope and measure actual opt-in client interest.',
  'Human authorization is necessary for inbox, calendar, finance or customer data access.'),
 'consignment_research':(
  'Research items the owner has lawful permission to list or broker.',
  'Draft a commission agreement, item condition checklist and shipping-cost estimator.',
  'Compare public prices without copying listing photos or promising inventory you do not possess.',
  'Test demand with one voluntarily supplied item and truthful documentation.',
  'Owner confirms item ownership, consignment permissions and platform resale rules.'),
 'stock_media':(
  'Select original abstract icons, photos or footage that you have rights to distribute.',
  'Generate a small varied pack and inspect dimensions, metadata and visible defects.',
  'Check each target marketplace licensing policy, use permissions and model/property releases.',
  'Prepare searchable but accurate keywords and compare existing permitted examples.',
  'Owner approves artist enrollment, model releases and any public submission.'),
 'community_support':(
  'Research a real group need that would benefit from original templates or coordination.',
  'Create a consent-safe sample resource and transparent service explanation.',
  'Avoid claiming sponsorship, nonprofit status or community endorsement without proof.',
  'Invite voluntary feedback from legitimate stakeholders without cold-message automation.',
  'Owner reviews mission fit, lawful funding conditions and any external publishing.'),
 'user_research':(
  'Find official user-research or usability-study sites with clear eligibility rules.',
  'Check age, country, time commitment, payment and privacy conditions manually.',
  'Create a comparison sheet of credible participation opportunities and red flags.',
  'Provide the owner with realistic time and privacy trade-offs, not earning guarantees.',
  'Only a real eligible person may enroll or participate; the bot cannot substitute for them.'),
 'print_on_demand':(
  'Choose an original design style and research a lawful zero-inventory printing provider.',
  'Create an original pattern sample and a mockup clearly labeled as a concept.',
  'Verify provider terms, unit cost, fulfillment regions, returns and fees before setting any price.',
  'Estimate the real break-even margin and test interest without promising stock or delivery.',
  'The owner approves supplier onboarding, design rights and platform seller account verification.'),
 'microtask_platforms':(
  'Compare official payment eligibility and fees on legitimate providers.',
  'Prepare scam warnings and age/location requirements from verified provider pages.',
  'Only show human-accessible legitimate options; the bot cannot perform human participation fraudulently.',
  'Record the user’s actual time spent and payouts only if the user supplies truthful evidence.',
  'The owner completes all applications and work personally as required.'),
 'faceless_education_shorts':(
  'Research one genuine audience problem using fresh sources, separating search interest from confirmed buyers.',
  'Write five original instructional scenes with fact-checkable claims and no copied music or movie clips.',
  'Generate vertical scene PNGs and timed SRT subtitles with the local video factory; optional FFmpeg MP4.',
  'Review readability, audio rights, platform AI disclosures and whether every claim can be supported.',
  'Owner authorizes channel and publication; assess actual retention/views after 7/14 days and pivot if unsuccessful.'),
 'long_form_explainers':(
  'Identify a narrow original lesson topic with real learner questions and a clear learning objective.',
  'Create an original structured outline and 16:9 sample scenes; distinguish sourced facts from opinion.',
  'Check that enough original explanation, visuals and commentary exists to avoid repetitive/inauthentic content.',
  'Prepare subtitles, metadata and rights checklist; do not reuse copyrighted images or unlicensed audio.',
  'Owner approves YouTube setup and upload, then track honest audience retention and valid conversions.'),
 'short_form_editing_service':(
  'Choose one group of creators who could benefit from cutting and captioning their own videos.',
  'Create a royalty-free fictional sample using the local image scene and SRT package.',
  'State the editing scope, turnaround assumptions, accuracy review and number of revisions.',
  'Prepare a consent-based portfolio listing and a clear offer without sending unsolicited bulk messages.',
  'Owner signs an actual rights/scope agreement before handling a client recording or publishing edits.'),
 'thumbnail_service':(
  'Research one clear video topic and identify the audience expectation, not just sensational clickbait.',
  'Design three original readable cover concepts with strong contrast and a truthful title.',
  'Check cropping on mobile and verify rights to every logo, photograph and face.',
  'Present a transparent before/after portfolio concept with fictional creator examples.',
  'Owner reviews any actual client brief; record authentic satisfaction and conversion evidence.'),
 'landing_page_development':(
  'Choose a small business niche and the one visitor action the landing page should make easier.',
  'Generate the responsive offline HTML/CSS demonstration, without fake testimonials or client affiliation.',
  'Inspect the page on phones, check accessibility, and add only verified business contact data after approval.',
  'Make an owner-reviewed proposal covering scope, quotation, revisions and commercially permitted hosting.',
  'Get client consent before deployment or outreach; track real requests and client payment after a contract.'),
 'creator_link_pages':(
  'Find one independent creator audience problem such as booking inquiries or organizing verified links.',
  'Build a minimal mobile-friendly static page with demo links and no fabricated endorsements.',
  'Verify the real creator identity and their links only after permission is documented.',
  'Make a clear hosting/maintenance price plan; never assume commercial GitHub Pages hosting is allowed.',
  'Owner approves the preview, publication and any client outreach; measure real inquiries.'),
 'caption_writing_service':(
  'Define one audience and one platform, including its content rules and promotional disclosure requirements.',
  'Write original hooks and captions using checked facts without engagement bait or copied influencer posts.',
  'Use fictional sample brand details and score each caption for clarity, truthfulness and readability.',
  'Offer a sample bundle and defined number of revisions through an approved portfolio channel.',
  'Owner gets the client brief/approval before posting; track authentic responses and paid work.'),
 'local_promo_video':(
  'Select one local business vertical and define a believable benefit without promising traffic results.',
  'Create a clearly fictional 9:16 video storyboard and captions using the original local video builder.',
  'List the exact footage, branding, music, releases and approval rights needed for real client work.',
  'Prepare an unsent outreach draft and scope/price proposal, with compliant business contact details.',
  'Owner secures business consent before using its name or posting an advert; record actual conversions.'),
 'video_caption_subtitles':(
  'Choose the legitimate creator use case and format, such as timed SRT files for client-owned videos.',
  'Prepare a working SRT demo with original scene images and timing checks.',
  'Demonstrate accuracy, speaker identification and accessibility without pretending to transcribe unknown media.',
  'Define client consent, confidentiality, turnaround and revision policy.',
  'Only process authorized recordings after agreement; record accurate fulfillment and client feedback.'),
 'email_design_service':(
  'Define an opted-in newsletter audience and one clear editorial objective.',
  'Create an original copy/layout template using fictitious business information.',
  'Check accessibility, text-only alternatives, links, disclosures and unsubscribe flow.',
  'Prepare an accurate recurring production quote, never a guaranteed open-rate promise.',
  'Owner approves client account connection and compliant consent-based sending; measure genuine results.'),
 'digital_checklists':(
  'Select one repetitive real workflow with a customer who benefits from an easy-to-use checklist.',
  'Build an original printable checklist and editable source, with instructions and accessibility checks.',
  'Get opt-in reader feedback to discover missing steps or wrong assumptions.',
  'Prepare accurate digital download format, fee estimate, description and buyer instructions.',
  'Owner verifies seller account/platform rules before publishing; log legitimate purchases, not mock sales.'),
 'audio_narration':(
  'Choose original educational text or a consented client recording; do not imitate protected voices.',
  'Write a concise original narration script with a license and pronunciation checklist.',
  'Evaluate Piper or another fully local model only when installed and voice weights allow commercial use.',
  'Check intelligibility, accuracy, privacy and rights; make sample deliverable and transparent quote.',
  'Owner approves any voice generation, release, distribution and client contract before charging.'),
 'community_content_research':(
  'Identify a real repeated community question using public permitted sources only.',
  'Make a sourced original FAQ and onboarding draft, without collecting private group discussions.',
  'Ask a consenting organizer whether the draft is actually useful, and correct inaccuracies.',
  'Define a bounded monthly service scope, content review, and clearly stated constraints.',
  'Owner authorizes community access or publication; record accepted deliverables and invoices.'),

}

SCHEMA = '''
PRAGMA busy_timeout=15000;
CREATE TABLE IF NOT EXISTS signals (
 fingerprint TEXT PRIMARY KEY, source TEXT NOT NULL, title TEXT NOT NULL,
 url TEXT NOT NULL, note TEXT NOT NULL, collected_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS kits (
 idea_id INTEGER PRIMARY KEY, method_key TEXT NOT NULL, verdict TEXT NOT NULL,
 path TEXT NOT NULL, digest TEXT NOT NULL, generated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS audit (
 seq INTEGER PRIMARY KEY AUTOINCREMENT, event TEXT NOT NULL, payload TEXT NOT NULL,
 previous TEXT NOT NULL, digest TEXT NOT NULL
);
'''


def utcnow():
    return datetime.now(timezone.utc)


def safe_rss(raw: bytes):
    """Parse official Google Trends RSS only; bounded/DTD-free, never fetch item links."""
    if not isinstance(raw, bytes) or len(raw) > MAX_RSS_BYTES:
        raise ValueError('Google Trends RSS too large')
    upper=raw.upper()
    if b'<!DOCTYPE' in upper or b'<!ENTITY' in upper:
        raise ValueError('XML declarations are not allowed')
    root=ET.fromstring(raw)
    if root.tag != 'rss':
        raise ValueError('Expected RSS format')
    result=[]
    for item in root.findall('./channel/item')[:30]:
        title=clean(item.findtext('title',''),160)
        if not title: continue
        # The origin is the Google RSS feed; don't fetch arbitrary links supplied in XML.
        result.append({'source':'google_trends_rss','title':title,
          'url':'https://trends.google.com/trending?geo=US',
          'note':'Recent search spike, NOT customer demand or a validated product sale'})
    return result


def fetch_trends(fetcher=None):
    if fetcher is None:
        def fetcher(url):
            req=urllib.request.Request(url, headers={
                'User-Agent':'OperationBillionTrendResearch/0.6',
                'Accept':'application/rss+xml,application/xml,text/xml'})
            with urllib.request.urlopen(req, timeout=8) as response:
                # Redirects to arbitrary hosts are forbidden.
                if urlsplit(response.geturl()).hostname != 'trends.google.com':
                    raise ValueError('RSS redirect to unexpected host')
                return response.read(MAX_RSS_BYTES + 1)
    return safe_rss(fetcher(RSS_URL))


def keyword_score(method, title):
    title=title.casefold()
    return sum(1 for kw in method.keywords if re.search(r'(?<!\w)'+re.escape(kw.casefold())+r'(?!\w)',title))


def match_signal(method, observations):
    scored=[]
    for x in observations:
        # Do not promote old repository discoveries as today's live buyer trends.
        try:
            observed=datetime.fromisoformat(x['collected_at'])
            if observed.tzinfo is None or utcnow()-observed>timedelta(days=30):continue
        except (KeyError,TypeError,ValueError):continue
        n=keyword_score(method,x['title'])
        if n:
            # Short news spikes don't prove purchases; GitHub activity isn't demand either.
            scored.append((n,x['collected_at'],x))
    return sorted(scored,key=lambda z:(z[0],z[1]),reverse=True)[0][2] if scored else None


class TrendEngine:
    def __init__(self,home):
        self.home=Path(home)
        self.path=self.home/'data'/'trend_engine.sqlite3'
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.connect() as c: c.executescript(SCHEMA)

    @contextmanager
    def connect(self):
        c=sqlite3.connect(self.path,timeout=15,isolation_level=None)
        c.row_factory=sqlite3.Row
        try: yield c
        finally: c.close()

    @staticmethod
    def audit(c,event,payload):
        body=json.dumps(payload,sort_keys=True,separators=(',',':'),ensure_ascii=True)
        p=c.execute('SELECT digest FROM audit ORDER BY seq DESC LIMIT 1').fetchone()
        prev=p['digest'] if p else 'GENESIS'
        digest=hashlib.sha256((prev+'\n'+event+'\n'+body).encode()).hexdigest()
        c.execute('INSERT INTO audit(event,payload,previous,digest) VALUES(?,?,?,?)',
                  (event,body,prev,digest))

    def audit_valid(self):
        prev='GENESIS';signals=set();kits=set()
        with self.connect() as c:
            for event in c.execute('SELECT * FROM audit ORDER BY seq'):
                if event['previous']!=prev or hashlib.sha256((prev+'\n'+event['event']+'\n'+event['payload']).encode()).hexdigest()!=event['digest']:
                    return False
                try:
                    payload=json.loads(event['payload'])
                    if event['event']=='signal':
                        k=payload['fingerprint']
                        row=c.execute('SELECT * FROM signals WHERE fingerprint=?',(k,)).fetchone()
                        if not row or any(row[col]!=payload[col] for col in ('source','title','url','note','collected_at')):
                            return False
                        signals.add(k)
                    elif event['event']=='kit':
                        i=payload['idea_id']
                        row=c.execute('SELECT * FROM kits WHERE idea_id=?',(i,)).fetchone()
                        if not row or any(row[col]!=payload[col] for col in ('method_key','verdict','path','digest','generated_at')):
                            return False
                        path=self.home / row['path']
                        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=row['digest']:
                            return False
                        kits.add(i)
                    else: return False
                except (KeyError,ValueError,TypeError,OverflowError,OSError,MemoryError):
                    return False
                prev=event['digest']
            return (len(signals)==c.execute('SELECT COUNT(*) FROM signals').fetchone()[0]
                 and len(kits)==c.execute('SELECT COUNT(*) FROM kits').fetchone()[0])

    def store(self, entries):
        allow={'google_trends_rss':{'trends.google.com'},
               'github_public_repos':{'github.com'},
               'hn_public_search':{'news.ycombinator.com'},
               'github_blog_rss':{'github.blog'}}
        count=0
        for x in list(entries)[:SOURCE_CAP]:
            source=x.get('source',''); url=x.get('url','')
            u=urlsplit(url)
            if source not in allow or u.scheme!='https' or u.hostname not in allow[source] or u.username or u.password:
                continue
            title=clean(x.get('title',''),180)
            if not title: continue
            fp=hashlib.sha256((source+'\0'+title.casefold()+'\0'+url).encode()).hexdigest()
            payload={'fingerprint':fp,'source':source,'title':title,'url':url,
                     'note':clean(x.get('note',''),250),'collected_at':utcnow().isoformat(timespec='seconds')}
            if x.get('recorded_at'):
                try:
                    prior=datetime.fromisoformat(x['recorded_at'])
                    if prior.tzinfo and prior<=utcnow():payload['collected_at']=prior.isoformat(timespec='seconds')
                except (ValueError,TypeError):pass
            with self.connect() as c:
                c.execute('BEGIN IMMEDIATE')
                if c.execute('SELECT 1 FROM signals WHERE fingerprint=?',(fp,)).fetchone():
                    c.execute('COMMIT');continue
                c.execute('''INSERT INTO signals(fingerprint,source,title,url,note,collected_at)
                             VALUES(:fingerprint,:source,:title,:url,:note,:collected_at)''',payload)
                self.audit(c,'signal',payload)
                c.execute('COMMIT');count+=1
        return count

    def _fresh_rss(self,fetcher=None,now=None):
        now=now or utcnow()
        with self.connect() as c:
            r=c.execute("SELECT value FROM meta WHERE key='last_rss_attempt'").fetchone()
            if r:
                try:
                    if now-datetime.fromisoformat(r['value']) < timedelta(hours=MIN_REFRESH_HOURS):
                        return 0,'cached: Google Trends polled within past six hours'
                except ValueError: pass
            # Record attempt even on failure to avoid hammering feeds during outages.
            c.execute('BEGIN IMMEDIATE')
            c.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('last_rss_attempt',?)",(now.isoformat(),))
            c.execute('COMMIT')
        try:
            return self.store(fetch_trends(fetcher)),'Google Trends official RSS fetched'
        except (ValueError,ET.ParseError,urllib.error.URLError,TimeoutError,OSError) as e:
            return 0,'Google Trends RSS unavailable: '+type(e).__name__

    def source_rows(self):
        with self.connect() as c:
            return [dict(x) for x in c.execute('SELECT * FROM signals ORDER BY collected_at DESC LIMIT 300')]

    def import_existing_public_sources(self,lab):
        # These sources were already safely retrieved by v0.5; do not send extra requests.
        with lab.connect() as c:
            obs=[dict(x) for x in c.execute('SELECT * FROM observations ORDER BY id DESC LIMIT 80')]
        return self.store([{'source':x['source'],'url':x['url'],'title':x['title'],'note':x['note'],
                            'recorded_at':x['recorded_at']} for x in obs])

    def write_kit(self,idea,signal=None):
        method=BY_KEY[idea['method_key']]
        steps=STARTUP_STEPS.get(method.key,(
          'Specify the exact buyer, immediate problem, and what a paid deliverable includes.',
          'Create a small original example: '+method.deliverable+'.',
          'Quality-check the result, cost, accessibility, rights, and factual claims.',
          'Validate the hypothesis: '+method.test+'.',
          'Complete account, eligibility or human-delivery prerequisites before external publication.'))
        court=json.loads(idea['court_json'])
        if idea['status']!='APPROVED_LOCAL_PLAN' or idea['verdict']!='NOT GUILTY' or court.get('verdict')!='NOT GUILTY':
            raise ValueError('Cannot execute unapproved or retired court case')
        proposal=adjudicate(Proposal('trend_'+method.key,'Make local startup sample: '+method.offer,
                   action='generate_local_draft',expenditure_usd=0))
        if proposal.verdict!='NOT GUILTY':
            raise ValueError('New startup job rejected by court')
        with self.connect() as c:
            if c.execute('SELECT 1 FROM kits WHERE idea_id=?',(idea['id'],)).fetchone():
                return None
        result={'status':'STARTUP_KIT_NOT_LAUNCHED','builder':'NO_AUTOMATED_DELIVERABLE',
                'sample_path':None,'quality':'NOT_RUN'}
        key=BUILD_MAP.get(method.key)
        if key:
            builder=BUILDERS[key]
            fp=hashlib.sha256(('trend-idea-v06-'+str(idea['id'])+'-'+key).encode()).hexdigest()
            path=make_artifact(self.home,builder,0,fp,[])
            quality=inspect(path)
            if quality['passed']:
                if builder.suggested_price>0:
                    prepare_sell_kit(path,builder.channel)
                result={'status':'LOCAL_SAMPLE_CREATED_NOT_LAUNCHED','builder':key,
                        'sample_path':str(path.relative_to(self.home)),'quality':'PASSED'}
            else:
                result['quality']='FAILED: '+','.join(quality['issues'][:3])
        elif method.key in ('faceless_education_shorts','long_form_explainers','short_form_editing_service',
                                 'landing_page_development','creator_link_pages','local_promo_video','video_caption_subtitles'):
            # Validated second local-court vote inside Wing; NOT a social/hosted launch.
            from .creator_website_wing import Wing
            wing=Wing(self.home)
            if method.key in ('landing_page_development','creator_link_pages'):
                sample=wing.create('website','independent tutor' if method.key=='creator_link_pages' else 'local cafe',variant=int(idea['id'])%97)
            elif method.key=='long_form_explainers':
                sample=wing.create('youtube','Create an educational short',variant=int(idea['id'])%97)
            else:
                sample=wing.create('short','Create an educational short',variant=int(idea['id'])%97)
            if sample.get('verdict')=='NOT GUILTY' and sample.get('folder'):
                result={'status':'LOCAL_SAMPLE_CREATED_NOT_LAUNCHED','builder':'creator_website_wing',
                        'sample_path':str(Path(sample['folder']).relative_to(self.home)),
                        'quality':'PENDING HUMAN CONTENT / RIGHTS REVIEW'}
        if signal:
            source={'kind':signal['source'],'title':signal['title'],'url':signal['url'],
                    'interpretation':('Search interest only, not evidence of a buyer or transaction'
                        if signal['source']=='google_trends_rss' else
                         'Repository/discussion visibility only, not verified buyer demand')}
        else:
            source={'kind':'NO_MATCH','title':'No matching current trend', 'url':'',
                    'interpretation':'Unvalidated catalog hypothesis; no present demand measured'}
        packet={
          'idea_id':idea['id'],'method_key':method.key,'income_lane':method.lane,
          'candidate_customer':method.buyer,'offering':method.offer,
          'startup_budget_usd':0,'budget_note':'No mandatory paid service; external seller/payment fees may apply',
          'evidence':source,'court_verdict':'NOT GUILTY: LOCAL ACTIONS ONLY',
          'startup_actions':[{'number':i,'action':s,'performed_automatically':False} for i,s in enumerate(steps,1)],
          'performed_local_work':result,
          'market_validation':{'hypothesis':method.test,'first_signal':'qualified interest, inquiries or opt-ins',
             'conversion_signal':'real orders or paid invoices with costs recorded separately',
             'days_to_early_review':7,'days_to_retirement_review':14,
             'early_review_note':'7-day rule needs actual exposure/engagement, not missing analytics',
             'retirement_note':'No launch after 14 days is UNLAUNCHED, not evidence of a failed offer'},
          'start_here':{'channel':method.channel,'needs_before_live_launch':method.prerequisite,
             'owner_must_do':['set up and verify required accounts','accept payment and payout terms',
                              'authorize any publication or customer contact'],
             'bots_can_do':['make permitted local samples','research public signals and draft materials',
                            'check sample quality','suggest a different technique if retired']},
          'google_research_links':{
             'trend_explore':'https://trends.google.com/trends/explore?geo=US',
             'trending_now':'https://trends.google.com/trending?geo=US',
             'manual_google_search':'https://www.google.com/search?q='+quote(method.offer)
          },
          'safety_note':'Do not upload scraped media, invent verified sales, install stranger GitHub code, or automate restricted verification.'
        }
        folder=self.home/'output'/'startup_kits'/('idea_%04d_%s'%(idea['id'],method.key))
        folder.mkdir(parents=True,exist_ok=True)
        text=json.dumps(packet,indent=2,ensure_ascii=True)+'\n'
        path=folder/'startup_plan.json'
        atomic_text(path,text)
        # Also write easy-to-read steps for phone-friendly review; JSON is audit protected.
        md=['# Startup plan: '+method.offer,'',
            '**NOT LAUNCHED. NO VERIFIED SALES.**','',
            'Buyer: '+method.buyer,'Channel: '+method.channel,'',
            '## What the bots did','', result['status']+' | '+str(result['sample_path']),'',
            '## How to start','']
        md += [str(i)+'. '+s for i,s in enumerate(steps,1)]
        md += ['','## Evidence and caveats','',source['interpretation'],source['url'],
               '','## Success / retirement','',
               'Review measurable engagement at 7 days, retire unsuccessful launched work after 14 days,',
               'and do NOT call unlaunched work a failed market experiment.','',
               'Owner account verification, publishing, payments and customer contact are never performed here.']
        atomic_text(folder/'START_HERE.md','\n'.join(md)+'\n')
        relative=str(path.relative_to(self.home))
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        entry={'idea_id':idea['id'],'method_key':method.key,'verdict':idea['verdict'],
               'path':relative,'digest':digest,'generated_at':utcnow().isoformat(timespec='seconds')}
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            if c.execute('SELECT 1 FROM kits WHERE idea_id=?',(idea['id'],)).fetchone():
                c.execute('ROLLBACK');return None
            c.execute('''INSERT INTO kits(idea_id,method_key,verdict,path,digest,generated_at)
                         VALUES(:idea_id,:method_key,:verdict,:path,:digest,:generated_at)''',entry)
            self.audit(c,'kit',entry)
            c.execute('COMMIT')
        return {'idea_id':idea['id'],'method':method.key,'status':result['status'],'packet':relative}

    def scan(self,lab=None,live=False,limit=3,fetcher=None,now=None):
        if not 1<=limit<=12:raise ValueError('limit must be between 1 and 12')
        lab=lab or OpportunityLab(self.home)
        if not lab.audit_valid() or not self.audit_valid():
            raise RuntimeError('Research audit failed; startup execution halted')
        saved=self.import_existing_public_sources(lab)
        status='Offline mode; using existing saved sources'
        if live:
            fresh,status=self._fresh_rss(fetcher=fetcher,now=now);saved+=fresh
        signals=self.source_rows()
        with self.connect() as c:
            completed={r['idea_id'] for r in c.execute('SELECT idea_id FROM kits')}
        active=[x for x in reversed(lab.rows(300)) if x['status']=='APPROVED_LOCAL_PLAN'
                and x['verdict']=='NOT GUILTY' and x['id'] not in completed and x['method_key'] in BY_KEY]
        # Prefer methods with relevant public evidence but don't claim a search spike means sales.
        ranked=sorted(active,key=lambda x:(not bool(match_signal(BY_KEY[x['method_key']],signals)),x['id']))
        kits=[]
        for idea in ranked[:limit]:
            packet=self.write_kit(idea,match_signal(BY_KEY[idea['method_key']],signals))
            if packet:kits.append(packet)
        result={'sources_added':saved,'sources_total':len(signals),
                'google_trends':status,'startup_kits_created':kits,
                'marketplace_published':0,'sales_verified':0,
                'remaining_eligible_plans':max(0,len(active)-len(kits)),'audit_valid':self.audit_valid()}
        atomic_text(self.home/'output'/'startup_kits'/'LATEST_SUMMARY.json',
                    json.dumps(result,indent=2)+'\n')
        return result
