"""Opportunity Intelligence Hub: public-source research -> local court -> experiment briefs.

No account access, mass scraping, executable repo installs, outreach or sales claims.
All external content is untrusted evidence about possible demand, not proof of profit.
Only known endpoints are fetched, with capped bytes and a six-hour research cache.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from .court import Proposal, adjudicate
from .lifecycle import assess
from .workshop import atomic_text


@dataclass(frozen=True)
class Method:
    key: str
    lane: str
    offer: str
    buyer: str
    keywords: tuple[str, ...]
    deliverable: str
    test: str
    channel: str
    prerequisite: str


# A starting hypothesis library, not a directory of proven or guaranteed income streams.
# These are distinct ways to provide value without up-front inventory/software expense.
METHODS = (
    Method('template_market', 'Digital templates', 'Editable job-search and business templates', 'job seekers / solo operators',
           ('template', 'resume', 'spreadsheet', 'document'), 'An original editable sample and license checklist',
           'Show one sample to relevant opt-in readers; measure visits and interest', 'digital storefront', 'A seller profile and an approved digital-product platform'),
    Method('education_materials', 'Educational assets', 'Original printable practice and lesson kits', 'tutors / parents / teachers',
           ('learning', 'teacher', 'worksheet', 'curriculum', 'study'), 'One original worksheet pack with answer guidance',
           'Validate the learning need with educators; log eligible site visits and buyer questions', 'digital storefront', 'Quality review and appropriate age/education claims'),
    Method('design_service', 'Freelance visual design', 'Custom flyers, menus, icons, and social graphics', 'small organizations',
           ('design', 'graphics', 'logo', 'art', 'illustration'), 'A sample portfolio and transparent service scope',
           'Make a public portfolio; measure inquiries from opted-in prospects', 'freelance portfolio', 'Original artwork and the ability to fulfill client requests'),
    Method('website_audit', 'Web improvement services', 'Page-speed and accessibility improvement plans', 'site owners',
           ('website', 'lighthouse', 'seo', 'accessibility', 'performance'), 'A truthful demonstration audit and scoped proposal',
           'Offer an opt-in sample; record qualified requests and paid conversions', 'freelance portfolio', 'Permission for any nonpublic site checks; no security intrusion'),
    Method('micro_utility', 'Software utilities', 'Simple offline calculators and workflow helpers', 'people with repetitive tasks',
           ('open source', 'developer', 'api', 'cli', 'automation', 'tool'), 'A locally working proof-of-concept and README',
           'Test the specific problem with at least five potential users before offering paid support', 'software demo', 'A functioning, tested utility; delivery/support capacity'),
    Method('micro_saas_validation', 'Micro-SaaS research', 'Specialized hosted-tool concept and validation', 'niche professional users',
           ('saas', 'workflow', 'crm', 'b2b', 'startup'), 'A prototype and a user interview script, not a claimed SaaS product',
           'Collect voluntary interest before hosting anything with operating costs', 'research / demo', 'Hosting and payment costs may arise; remain in research until budgeted'),
    Method('newsletter_service', 'Newsletter operations', 'Newsletter editorial calendar and formatting service', 'independent publishers',
           ('newsletter', 'email', 'writing', 'content', 'substack'), 'Original opt-in sample issue and newsletter production plan',
           'Measure real opt-in subscribers and recurring client interest', 'permission-based newsletter', 'Consent-based subscription list; clear unsubscribe process'),
    Method('affiliate_editorial', 'Affiliate editorial', 'Disclosed original product-comparison guides', 'readers making purchases',
           ('affiliate', 'review', 'shopping', 'comparison'), 'Disclosure template and evidence checklist (no fake reviews)',
           'Validate a niche before applying for legitimate affiliate enrollment', 'content website', 'Affiliate approval and genuine firsthand/verifiable product evidence'),
    Method('podcast_assets', 'Creator support', 'Podcast cover-art, episode notes, and media kits', 'independent creators',
           ('podcast', 'creator', 'video', 'audio', 'episode'), 'An original media kit template and show-notes example',
           'Get opt-in feedback and measure requests for custom packs', 'portfolio', 'Rights to all supplied media and client authorization'),
    Method('short_video_assets', 'Video production assets', 'Storyboard and short-form promo template packs', 'video creators / small brands',
           ('short', 'video', 'reels', 'editing', 'caption'), 'An original storyboard sample and caption kit',
           'Publish a truthful portfolio sample after authorization; measure inquiries', 'portfolio', 'Rights-cleared footage/audio and platform compliance'),
    Method('data_cleanup', 'Data organization services', 'CSV cleaning, dashboards, and record templates', 'teams managing spreadsheets',
           ('csv', 'data', 'spreadsheet', 'reporting', 'dashboard'), 'An offline sample CSV-cleaning script for synthetic data',
           'Validate common pain points and record opt-in requests for a custom tool', 'freelance portfolio', 'Never upload or process private client data without authorization'),
    Method('local_event_assets', 'Event assets', 'Original printable event and invitation kits', 'community event organizers',
           ('event', 'invitation', 'calendar', 'ticket', 'rsvp'), 'A downloadable event kit using fictional example details',
           'Test a few original designs with an opt-in audience', 'digital storefront', 'No impersonation, copyrighted characters, or false event claims'),
    Method('niche_research', 'Specialized research', 'Custom niche briefs using permitted public information', 'small organizations / creators',
           ('research', 'market', 'trend', 'analysis', 'report'), 'A sourced, qualified sample research brief',
           'Show an example without fabricating demand; measure requests for original reports', 'portfolio', 'Source attribution and independent verification of claims'),
    Method('open_source_support', 'Developer support', 'Open-source setup, documentation, and integration help', 'developers / small businesses',
           ('github', 'opensource', 'readme', 'documentation', 'python'), 'An original documentation sample and service checklist',
           'Evaluate interest in documentation fixes and voluntary support requests', 'freelance portfolio', 'Respect each dependency license; no installing unreviewed code'),
    Method('translation_editing', 'Language and editing', 'Proofreading and plain-language revision services', 'writers / small businesses',
           ('localization', 'translation', 'language', 'editing'), 'A fictional writing sample showing editing methodology',
           'Test an opt-in portfolio listing; only offer languages you can verify', 'freelance portfolio', 'Human quality verification for language-specific work'),
    Method('printable_games', 'Games and activities', 'Original puzzles, scavenger hunts, and printable games', 'families / educators',
           ('game', 'puzzle', 'quiz', 'activity'), 'Original rule sheet and small playable sample',
           'Test playability and willingness to pay without copied game IP', 'digital storefront', 'Original game mechanics/assets and suitability review'),
    Method('online_tutoring', 'Online tutoring', 'Remote tutoring and educational support', 'students who request tutoring',
           ('tutor', 'teaching', 'math', 'coding', 'learning'), 'One original sample lesson and lesson-plan portfolio',
           'Check opt-in demand for a subject you can competently teach', 'approved tutoring profile', 'Age safeguards, qualifications, and real human delivery'),
    Method('transcription_captioning', 'Transcription and captioning', 'Accurate transcripts and subtitles for owned content', 'video and podcast creators',
           ('transcription', 'subtitles', 'captions', 'audio'), 'A sample transcript from your own original audio',
           'Test response to a quality-rated, consent-based sample', 'freelance portfolio', 'Client authorization, rights, and careful manual accuracy review'),
    Method('open_source_bounties', 'Open-source contributor bounties', 'Documented code fixes and project improvements', 'maintainers offering legitimate bounties',
           ('bounty', 'bugfix', 'issue', 'maintainer', 'open source'), 'A tested sample patch and original documentation',
           'Research official bounty terms without accessing private systems', 'public contributions', 'Maintainer permission, contribution license and human review'),
    Method('virtual_assistant', 'Virtual assistant services', 'Scheduling, content formatting, and operations checklists', 'solo creators / founders',
           ('assistant', 'calendar', 'scheduling', 'operations'), 'A fictional scheduling and handoff template',
           'Validate the tasks clients are willing to delegate', 'freelance portfolio', 'No access to client emails/calendars without explicit permission'),
    Method('consignment_research', 'Consignment and resale research', 'Permission-based consignment listing support', 'owners who want to sell goods',
           ('resell', 'secondhand', 'consignment', 'marketplace'), 'A cost and fulfillment checklist, not an inventory claim',
           'Check commissions, rights to list, actual stock, and transport costs', 'research / consignment', 'Ownership/consent, physical delivery, fees, and possible nonzero costs'),
    Method('stock_media', 'Original stock media', 'License-compliant original photos and audio clips', 'creators seeking stock assets',
           ('stock', 'photography', 'photo', 'sound', 'audio'), 'A small original sample with release/licensing notes',
           'Explore authorized licensing channels and actual download interest', 'stock content storefront', 'Ownership, model releases and account review'),
    Method('community_support', 'Community operations', 'Moderation guidelines and member onboarding kits', 'forum and membership organizers',
           ('community', 'forum', 'moderation', 'members'), 'A volunteer or paid moderation checklist for fictional example',
           'Test demand for community-management support without joining accounts automatically', 'services portfolio', 'Platform policies, privacy and owner permission'),
    Method('user_research', 'Human research participation', 'Legitimate paid user-testing and research panels', 'research organizations',
           ('user testing', 'usability', 'focus group', 'feedback'), 'A personal eligibility and scam-checking guide',
           'Identify legitimate eligibility and time requirements; do not pretend to be a participant', 'research-only opportunities',
           'Human participation, identity checks, eligibility, consent; not automatable by a bot'),
    Method('print_on_demand', 'Print-on-demand concept research', 'Original zero-inventory design concepts', 'niche apparel buyers',
           ('print-on-demand', 'merch', 'tshirt', 'shirt'), 'An original mockup and fulfillment/cost checklist',
           'Verify real seller terms, shipping, fees and actual no-upfront inventory options', 'research / authorized storefront',
           'Supplier approval, rights, order fulfillment and fees; no automatic POD listing'),
    Method('microtask_platforms', 'Microtask eligibility research', 'Comparison of legitimate paid microtask programs', 'individual qualified workers',
           ('microtask', 'annotation', 'data labeling', 'survey'), 'A scam and payout-policy comparison template',
           'Compare genuine programs and eligibility; require real human performance', 'research only',
           'Cannot automate human-verification tasks, misrepresent identity or bypass platform rules'),
    Method('faceless_education_shorts', 'Original educational short videos', 'Research, script, and edit original short lessons', 'viewers seeking practical tutorials',
           ('shorts', 'tiktok', 'youtube', 'video', 'tutorial', 'creator'), 'Original vertical-video storyboard, PNG scenes, SRT captions and honest script',
           'Compare real published watch time and audience retention; no reposted clips', 'authorized creator channel', 'Channel approval, platform disclosure, real audience and originality checks'),
    Method('long_form_explainers', 'Original educational YouTube', 'Research and produce educational explainer videos', 'people interested in learning',
           ('youtube', 'education', 'explainer', 'video'), '16:9 video scenes, storyboard and source-reviewed script',
           'Review topic search-interest and actual viewer retention after publishing', 'authorized YouTube channel', 'Owner review, genuine research and own music/visuals'),
    Method('short_form_editing_service', 'Video editing for clients', 'Captioning, editing and repackaging client-owned shorts', 'independent content creators',
           ('video', 'caption', 'reels', 'shorts', 'editing'), 'Rights-cleared portfolio sample and service description',
           'Ask opt-in creators whether sample saves them editing time', 'freelance portfolio', 'Client rights, scope and appropriate tool licenses'),
    Method('thumbnail_service', 'YouTube thumbnail design', 'Original readable video thumbnails and cover packs', 'video creators',
           ('thumbnail', 'youtube', 'cover', 'graphic'), 'Three original thumbnail concepts with readability review',
           'Run an ethical split test using owners own material', 'freelance portfolio', 'Copyright/likeness approval and no clickbait'),
    Method('landing_page_development', 'Website building', 'Mobile-friendly static business landing pages', 'small business owners',
           ('website', 'landing page', 'web design', 'html', 'frontend'), 'A working local responsive sample site with original copy',
           'Measure owner-approved inquiries and prospective-client requests', 'website portfolio', 'Client approval, hosting terms and verified business information'),
    Method('creator_link_pages', 'Creator websites', 'Simple link-in-bio and creator portfolio websites', 'independent creators',
           ('creator', 'portfolio', 'link', 'website'), 'A working local preview with placeholders and accessibility review',
           'Test via permission-based creator feedback', 'website portfolio', 'Client permission, commercial hosting eligibility'),
    Method('caption_writing_service', 'Social media copywriting', 'Original captions, hooks and scripts for client projects', 'small brands and creators',
           ('caption', 'social media', 'hooks', 'marketing'), 'Ten distinctly original example captions and truthfulness checklist',
           'Measure approved client responses; no engagement bait', 'portfolio', 'No misleading claims or unauthorized publication'),
    Method('local_promo_video', 'Business promo videos', 'Original local-business video adverts and animated promos', 'local service providers',
           ('promotional', 'ad video', 'commercial', 'small business'), 'A clearly marked fictional business demo video storyboard',
           'Get opt-in business owner review; track genuine inquiries', 'service portfolio', 'Written client approval for branding and public posting'),
    Method('video_caption_subtitles', 'Subtitle services', 'Original subtitles for authorized client videos', 'podcasters and creators',
           ('subtitle', 'srt', 'transcript', 'captioning'), 'Timed SRT examples and accuracy-review procedure',
           'Offer small owner-approved corrections and track requests', 'freelance portfolio', 'Rights to supplied recordings and privacy safeguards'),
    Method('email_design_service', 'Newsletter design', 'Original HTML newsletters and welcome-email layouts', 'independent newsletter publishers',
           ('newsletter', 'email', 'campaign', 'template'), 'A sample accessible email design (no send)',
           'Measure opt-in client feedback; avoid scraped lists', 'service portfolio', 'CAN-SPAM and subscriber consent/opt out'),
    Method('digital_checklists', 'Checklist micro-products', 'Niche task trackers and printable checklists', 'buyers with repeatable workflows',
           ('checklist', 'planner', 'productivity', 'workflow'), 'Original printable checklist and instructions',
           'Compare real buyer interest instead of treating views as sales', 'digital storefront', 'Shop account, rights, and accurate descriptions'),
    Method('audio_narration', 'Audio content services', 'Narration and audio-cleanup plans using consented voices', 'independent publishers',
           ('tts', 'podcast', 'audio', 'voiceover'), 'Original narration script and voice model licensing checklist',
           'Get authorized sample feedback; no voice cloning of others', 'services portfolio', 'Voice rights and commercial licensing checked'),
    Method('community_content_research', 'Community content operations', 'Ethical FAQ, community guides and moderation templates', 'niche community organizers',
           ('community', 'guide', 'faq', 'onboarding'), 'Original FAQ examples with supported sources',
           'Test usefulness with opt-in community managers', 'services portfolio', 'No scraping private groups or impersonating users'),

)
BY_KEY = {m.key: m for m in METHODS}

SCHEMA = '''
PRAGMA journal_mode=WAL;
PRAGMA busy_timeout=15000;
CREATE TABLE IF NOT EXISTS observations (
 id INTEGER PRIMARY KEY AUTOINCREMENT, fingerprint TEXT NOT NULL UNIQUE,
 source TEXT NOT NULL, title TEXT NOT NULL, url TEXT NOT NULL,
 recorded_at TEXT NOT NULL, note TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS ideas (
 id INTEGER PRIMARY KEY AUTOINCREMENT, fingerprint TEXT NOT NULL UNIQUE,
 method_key TEXT NOT NULL, source_id INTEGER REFERENCES observations(id),
 verdict TEXT NOT NULL, court_json TEXT NOT NULL,
 status TEXT NOT NULL, artifact TEXT NOT NULL DEFAULT '',
 created_at TEXT NOT NULL, launched_at TEXT, retired_at TEXT,
 retirement_reason TEXT NOT NULL DEFAULT '',
 views INTEGER NOT NULL DEFAULT 0, clicks INTEGER NOT NULL DEFAULT 0,
 sales INTEGER NOT NULL DEFAULT 0, gross_cents INTEGER NOT NULL DEFAULT 0,
 fee_cents INTEGER NOT NULL DEFAULT 0,
 launch_url TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_ideas_method ON ideas(method_key,status);
CREATE TABLE IF NOT EXISTS audit (
 seq INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT NOT NULL,
 payload TEXT NOT NULL, prev_hash TEXT NOT NULL, digest TEXT NOT NULL
);
'''


def now_utc():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def clean(value, limit=200):
    return re.sub(r'\s+', ' ', str(value or '')).strip()[:limit]


def trusted_url(url, domains):
    try:
        p=urllib.parse.urlsplit(str(url))
        return p.scheme=='https' and p.hostname in domains and not p.username and not p.password
    except (TypeError, ValueError):
        return False


def source_json(url, allow_host, fetcher=None):
    if not trusted_url(url, {allow_host}):
        raise ValueError('Unapproved source URL')
    if fetcher is None:
        def fetcher(path):
            req=urllib.request.Request(path,headers={'Accept':'application/json',
                          'User-Agent':'OperationBillionOpportunityResearch/0.5 (public metadata)'})
            with urllib.request.urlopen(req,timeout=7) as response:
                return response.read(180_001)
    raw=fetcher(url)
    if len(raw)>180_000: raise ValueError('Source size limit exceeded')
    return json.loads(raw)


def collect_public(slot=0, fetcher=None, rss_fetcher=None):
    """Fixed public JSON endpoints and official RSS. Never fetch discovered URLs."""
    observations=[]; errors=[]
    rotating=(
        ('freelance website tools in:name,description stars:>10', 'freelance'),
        ('open source education templates in:name,description stars:>10', 'worksheet'),
        ('python automation small business in:name,description stars:>20', 'automation'),
        ('newsletter open source tooling in:name,description stars:>10', 'newsletter'),
        ('image design svg generator in:name,description stars:>10', 'design'),
        ('data cleaning visualization in:name,description stars:>10', 'dashboard'),
        ('podcast video content tools in:name,description stars:>10', 'creator'),
        ('open source micro saas starter in:name,description stars:>10', 'startup'),
        ('open source AI video editing text to speech in:name,description stars:>20', 'video'),
        ('open source website generator local AI in:name,description stars:>20', 'website'),
        ('open source podcast subtitles automation in:name,description stars:>20', 'captions'),
    )
    # Rotate: opportunity coverage changes without hammering all services every pass.
    github_q,hn_q=rotating[slot % len(rotating)]
    github_url='https://api.github.com/search/repositories?'+urllib.parse.urlencode(
        {'q':github_q,'sort':'updated','order':'desc','per_page':'5'})
    try:
        data=source_json(github_url,'api.github.com',fetcher)
        for repo in data.get('items',[])[:5]:
            url=repo.get('html_url','')
            if trusted_url(url,{'github.com'}):
                observations.append({'source':'github_public_repos','title':clean(' '.join([
                   str(repo.get('full_name') or ''),str(repo.get('description') or '')]),200),
                    'url':url,'note':'Repository/tool existence; not commercial validation'})
    except (ValueError,TypeError,KeyError,urllib.error.URLError,TimeoutError,OSError) as e:
        errors.append({'source':'github_public_repos','error':type(e).__name__})
    hn_url='https://hn.algolia.com/api/v1/search?'+urllib.parse.urlencode(
        {'query':hn_q,'tags':'story','hitsPerPage':'5'})
    try:
        data=source_json(hn_url,'hn.algolia.com',fetcher)
        for item in data.get('hits',[])[:5]:
            ident=str(item.get('objectID',''))
            if not ident.isdigit(): continue
            observations.append({'source':'hn_public_search', 'title':clean(item.get('title','')),
              'url':'https://news.ycombinator.com/item?id='+ident,
              'note':'Public discussion; not proof of customers or revenue'})
    except (ValueError,TypeError,KeyError,urllib.error.URLError,TimeoutError,OSError) as e:
        errors.append({'source':'hn_public_search','error':type(e).__name__})
    # GitHub Blog official RSS; XML is parsed after caps and entity rejection.
    rss_url='https://github.blog/feed/'
    try:
        if rss_fetcher is None:
            def rss_fetcher(path):
                req=urllib.request.Request(path, headers={'User-Agent':'OperationBillionOpportunityResearch/0.5'})
                with urllib.request.urlopen(req,timeout=7) as response:
                    return response.read(180_001)
        raw=rss_fetcher(rss_url)
        if len(raw)>180_000 or b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():
            raise ValueError('RSS size or entity restriction')
        root=ET.fromstring(raw)
        items=root.findall('.//item')[:5]
        for item in items:
            title=clean(item.findtext('title',''))
            link=clean(item.findtext('link',''),500)
            if title and trusted_url(link,{'github.blog'}):
                observations.append({'source':'github_blog_rss','title':title,'url':link,
                    'note':'Software news; relevance and commercial viability not confirmed'})
    except (ValueError,TypeError,ET.ParseError,urllib.error.URLError,TimeoutError,OSError) as e:
        errors.append({'source':'github_blog_rss','error':type(e).__name__})
    return observations,errors


def fit(method:Method, title:str):
    low=title.lower()
    return sum(1 for kw in method.keywords if kw in low)


class OpportunityLab:
    def __init__(self,home:Path):
        self.home=Path(home)
        self.db=self.home/'data'/'opportunity_lab.sqlite3'
        self.db.parent.mkdir(parents=True,exist_ok=True)
        with self.connect() as c:
            c.executescript(SCHEMA)

    @contextmanager
    def connect(self):
        con=sqlite3.connect(self.db,timeout=15,isolation_level=None)
        try:
            con.row_factory=sqlite3.Row
            con.execute('PRAGMA foreign_keys=ON')
            con.execute('PRAGMA busy_timeout=15000')
            yield con
        finally: con.close()

    @staticmethod
    def audit(con,action,payload):
        canon=json.dumps(payload,sort_keys=True,separators=(',',':'))
        row=con.execute('SELECT digest FROM audit ORDER BY seq DESC LIMIT 1').fetchone()
        prev=row['digest'] if row else 'GENESIS'
        digest=hashlib.sha256((prev+'\n'+action+'\n'+canon).encode()).hexdigest()
        con.execute('INSERT INTO audit(action,payload,prev_hash,digest) VALUES(?,?,?,?)',(action,canon,prev,digest))

    def audit_valid(self):
        """Replay the append-only event ledger against current records and balances."""
        expected={}; seen_obs=set(); prev='GENESIS'
        with self.connect() as c:
            for r in c.execute('SELECT * FROM audit ORDER BY seq'):
                if r['prev_hash']!=prev or hashlib.sha256((prev+'\n'+r['action']+'\n'+r['payload']).encode()).hexdigest()!=r['digest']:
                    return False
                try:
                    p=json.loads(r['payload']); iid=p['id']
                    if r['action']=='observation':
                        saved=c.execute('SELECT * FROM observations WHERE id=?',(iid,)).fetchone()
                        if not saved or any(saved[k]!=p[k] for k in ('fingerprint','source','title','url','recorded_at','note')):
                            return False
                        seen_obs.add(iid)
                    elif r['action']=='idea':
                        saved=c.execute('SELECT * FROM ideas WHERE id=?',(iid,)).fetchone()
                        if not saved or any(saved[k]!=p[k] for k in
                              ('fingerprint','method_key','source_id','court_json','verdict','created_at')):
                            return False
                        if iid in expected: return False
                        expected[iid]={'status':p['status'],'artifact':'','launch_url':'',
                          'retirement_reason':'','views':0,'clicks':0,'sales':0,
                          'gross_cents':0,'fee_cents':0,'launched_at':None,'retired_at':None}
                    elif r['action']=='artifact':
                        expected[iid]['artifact']=p['dir']
                    elif r['action']=='launch':
                        expected[iid]['launch_url']=p['url']
                        expected[iid]['status']='LAUNCHED_USER_REPORTED'
                        expected[iid]['launched_at']=p['at']
                    elif r['action']=='event':
                        key={'view':'views','click':'clicks','sale':'sales'}[p['kind']]
                        expected[iid][key]+=p['quantity']
                        expected[iid]['gross_cents']+=p['gross_cents']
                        expected[iid]['fee_cents']+=p['fee_cents']
                    elif r['action']=='retire':
                        expected[iid]['status']='RETIRED'
                        expected[iid]['retirement_reason']=p['reason']
                        expected[iid]['retired_at']=p['at']
                    else:
                        return False
                except (KeyError,TypeError,ValueError,json.JSONDecodeError):
                    return False
                prev=r['digest']
            if c.execute('SELECT COUNT(*) FROM observations').fetchone()[0]!=len(seen_obs):
                return False
            if c.execute('SELECT COUNT(*) FROM ideas').fetchone()[0]!=len(expected):
                return False
            for iid,values in expected.items():
                saved=c.execute('SELECT * FROM ideas WHERE id=?',(iid,)).fetchone()
                if not saved or any(saved[k]!=v for k,v in values.items()):
                    return False
        return True

    def ingest(self,signals):
        new=0
        for s in signals:
            title=clean(s.get('title')); url=clean(s.get('url'),500)
            source=clean(s.get('source'),80)
            if not title or not trusted_url(url, {'github.com','news.ycombinator.com','github.blog'}):
                continue
            fp=hashlib.sha256((source+'\0'+url).encode()).hexdigest()
            with self.connect() as c:
                c.execute('BEGIN IMMEDIATE')
                row=c.execute('SELECT id FROM observations WHERE fingerprint=?',(fp,)).fetchone()
                if row:
                    c.execute('COMMIT');continue
                at=now_utc(); note=clean(s.get('note'),300)
                cur=c.execute('INSERT INTO observations(fingerprint,source,title,url,recorded_at,note) VALUES(?,?,?,?,?,?)',
                    (fp,source,title,url,at,note))
                self.audit(c,'observation',{'id':cur.lastrowid,'fingerprint':fp,'source':source,
                    'title':title,'url':url,'recorded_at':at,'note':note})
                c.execute('COMMIT');new+=1
        return new

    def rows(self,limit=150):
        with self.connect() as c:
            return [dict(x) for x in c.execute('SELECT * FROM ideas ORDER BY id DESC LIMIT ?', (limit,))]

    def overview(self):
        with self.connect() as c:
            count=c.execute('SELECT COUNT(*) FROM observations').fetchone()[0]
            ideas=c.execute('SELECT COUNT(*) FROM ideas').fetchone()[0]
            active=c.execute("SELECT COUNT(*) FROM ideas WHERE status IN ('APPROVED_LOCAL_PLAN','LAUNCHED_USER_REPORTED')").fetchone()[0]
            retire=c.execute("SELECT COUNT(*) FROM ideas WHERE status='RETIRED'").fetchone()[0]
            return {'methods_catalogued':len(METHODS),'public_observations':count,
                    'experiment_plans':ideas,'active_plans':active,'retired_plans':retire,
                    'audit_valid':self.audit_valid()}

    def _source_for(self,method):
        with self.connect() as c:
            choices=c.execute('SELECT * FROM observations ORDER BY id DESC LIMIT 250').fetchall()
        scored=sorted(((fit(method,x['title']),x) for x in choices), key=lambda x:(x[0],x[1]['id']),reverse=True)
        return dict(scored[0][1]) if scored and scored[0][0]>0 else None

    def propose(self,method:Method, source=None):
        """Court local experiment, persist original case and its source provenance atomically."""
        srcid=source['id'] if source else None
        evidence=(source['url'],) if source else ()
        fp=hashlib.sha256(('opportunity-v05\0'+method.key+'\0'+str(srcid or 'catalog')).encode()).hexdigest()
        judgment=adjudicate(Proposal('opportunity_'+method.key, method.offer,
           action='generate_local_draft',expenditure_usd=0,evidence_links=evidence))
        jtxt=json.dumps(judgment.data(),sort_keys=True)
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            old=c.execute('SELECT id FROM ideas WHERE fingerprint=?',(fp,)).fetchone()
            if old:
                c.execute('COMMIT');return None
            status='APPROVED_LOCAL_PLAN' if judgment.verdict=='NOT GUILTY' else 'COURT_REJECTED'
            at=now_utc()
            cur=c.execute('''INSERT INTO ideas(fingerprint,method_key,source_id,verdict,court_json,status,created_at)
                 VALUES(?,?,?,?,?,?,?)''',(fp,method.key,srcid,judgment.verdict,jtxt,status,at))
            iid=cur.lastrowid
            self.audit(c,'idea',{'id':iid,'fingerprint':fp,'method_key':method.key,'source_id':srcid,
                                'verdict':judgment.verdict,'court_json':jtxt,'created_at':at,'status':status})
            c.execute('COMMIT')
        if judgment.verdict=='NOT GUILTY':
            self.write_brief(iid,method,source,judgment)
        return {'id':iid,'method':method.key,'verdict':judgment.verdict,
                'status':'APPROVED_LOCAL_PLAN' if judgment.verdict=='NOT GUILTY' else 'COURT_REJECTED',
                'evidence_type':'public discussion / software existence' if source else 'catalog hypothesis only'}

    def write_brief(self,iid,method,source,judgment):
        folder=self.home/'output'/'opportunity_research'/('idea_%04d_%s'%(iid,method.key))
        folder.mkdir(parents=True,exist_ok=True)
        detail=('Public signal: '+source['title']+'\nSource: '+source['url']+'\n' if source else 'No external demand evidence; curated starting hypothesis.\n')
        brief=f'''# Opportunity Brief #{iid}: {method.offer}

**Status:** APPROVED FOR LOCAL PLANNING ONLY. **Zero verified buyers; zero verified earnings.**
**Income method:** {method.lane}  
**Who might pay:** {method.buyer}  
**Potential offering:** {method.offer}  
**Public-source relevance:** weak signal only. Not evidence of transactions.  
{detail}
## Original, zero-upfront-cost experiment

1. Create: {method.deliverable}.
2. Run a local quality and rights review; demonstrate the promised value with original work.
3. Validate: {method.test}.
4. Choose an authorized channel: {method.channel}. Obtain authorization and complete account/identity setup manually.
5. Start the **14-day clock only after a genuine external launch has been reported**; track actual views, clicks and sales.
6. At day 7 with 100+ real views and zero clicks, review or retire. At day 14 without results, retire or pivot.
7. If not launched within 14 days of this brief, retire it as UNLAUNCHED, **not as proof the market rejected it**.

## Prerequisites, costs and risks

- {method.prerequisite}.
- Software can be free locally; seller commissions, transaction fees, hosting, hardware, labor, or taxes can still apply.
- Do not copy someone else's product, source code, artwork or listings without proper licenses.
- No login, upload, unsolicited outreach, spending, or publication was performed by this court decision.
- Source is a weak hypothesis clue; independently verify demand, rights and fees.

## Court

Verdict: **{judgment.verdict}** — {judgment.decision}

## Evidence log

Record the REAL launch URL with `py -3 -m botfarm opportunity-launch {iid} https://actual-listing-url`, then manually report metrics with `py -3 -m botfarm opportunity-record {iid} view --quantity 5` (or click/sale).
These are **user-reported, unverified**; the farm does not have access to account sales data.
'''
        atomic_text(folder/'VALIDATION_BRIEF.md',brief)
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            c.execute('UPDATE ideas SET artifact=? WHERE id=?',(str(folder),iid))
            self.audit(c,'artifact',{'id':iid,'dir':str(folder)})
            c.execute('COMMIT')

    def retire_due(self,now=None):
        retired=[]
        for r in self.rows(500):
            if r['status'] not in ('APPROVED_LOCAL_PLAN','LAUNCHED_USER_REPORTED'): continue
            dec=assess({'created_at':r['created_at'],'launched_at':r['launched_at'],
                'artifact_dir':r['artifact'],'verdict':r['verdict'],'retired_at':r['retired_at'],
                'views':r['views'],'clicks':r['clicks'],'sales':r['sales'],
                'gross_cents':r['gross_cents'],'fee_cents':r['fee_cents']},now=now)
            if dec.action!='retire':continue
            with self.connect() as c:
                c.execute('BEGIN IMMEDIATE')
                retired_at=now_utc()
                cur=c.execute("UPDATE ideas SET status='RETIRED', retired_at=?, retirement_reason=? WHERE id=? AND retired_at IS NULL",
                    (retired_at,dec.classification,r['id']))
                if cur.rowcount:
                    self.audit(c,'retire',{'id':r['id'],'reason':dec.classification,'at':retired_at})
                    retired.append({'id':r['id'],'method':r['method_key'],'reason':dec.classification})
                c.execute('COMMIT')
        return retired

    def scan(self,live=False,limit=3,now=None,fetcher=None,rss_fetcher=None):
        if not self.audit_valid():raise RuntimeError('Opportunity lab audit chain invalid; research halted')
        if not 1<=limit<=8:raise ValueError('Opportunity scan limit must be 1–8')
        retired=self.retire_due(now=now)
        errors=[];new_sources=0
        cache=self.home/'data'/'opportunity_last_online.json'
        slot=int(time.time()//(6*3600))
        # Persist a refresh window even if fetching fails. No public service hammering.
        should_refresh=live and (fetcher is not None or rss_fetcher is not None or not cache.is_file()
               or time.time()-cache.stat().st_mtime>6*3600)
        if should_refresh:
            observations,errors=collect_public(slot=slot,fetcher=fetcher,rss_fetcher=rss_fetcher)
            new_sources=self.ingest(observations)
            atomic_text(cache,json.dumps({'refreshed_at':now_utc(),'source_count':len(observations),
                                         'errors':errors},indent=2))
        elif live and cache.is_file():
            try: errors=json.loads(cache.read_text(encoding='utf-8')).get('errors',[])
            except (ValueError,OSError): errors=[]
        counts={}
        current=self.rows(500)
        for row in current:
            if row['status']!='RETIRED':counts[row['method_key']]=counts.get(row['method_key'],0)+1
        # Skip retired methods until *other* lanes get a chance; not infinite cosmetic variants.
        last_retired={x['method_key'] for x in current if x['status']=='RETIRED'}
        eligible=[m for m in METHODS if counts.get(m.key,0)==0 and m.key not in last_retired]
        # Exhaustion is a safe pause, never recycle a rejected/retired technique automatically.
        # Rotate across distinct revenue mechanisms, not just variations of stickers.
        start=(int(time.time()//86400))%len(METHODS)
        order=list(METHODS[start:])+list(METHODS[:start])
        # Prefer sources relevant to an income method; otherwise rotate across the catalog.
        eligible.sort(key=lambda m: (0 if self._source_for(m) else 1, order.index(m)))
        ideas=[]
        for method in eligible[:limit]:
            source=self._source_for(method)
            result=self.propose(method,source)
            if result:ideas.append(result)
        self.write_index()
        return {'online_requested':live,'public_observations_added':new_sources,
           'public_fetch_errors':errors, 'new_plans':ideas,'retired':retired,
           'overview':self.overview(),'external_accounts_connected':False}

    def write_index(self):
        rows=self.rows(100)
        out=self.home/'output'/'opportunity_research'/'RESEARCH_LIBRARY.md'
        lines=['# Operation Billion — Opportunity Research Library','',
          '**This is a list of hypotheses and local plans, not earnings or proof of demand.**','',
          'Free research tools do not eliminate selling fees, effort, hardware or taxes.','',
          '| Plan | Technique | Court | Trial stage |', '|---|---|---|---|']
        for r in rows:
            lines.append(f"| {r['id']} | {BY_KEY[r['method_key']].lane} | {r['verdict']} | {r['status']} |")
        lines+=['','## Different income techniques the scouts may investigate','']
        lines.extend(f'- **{m.lane}:** {m.offer} — {m.channel}' for m in METHODS)
        with self.connect() as c:
            sources=[dict(v) for v in c.execute('SELECT source,title,url FROM observations ORDER BY id DESC LIMIT 150')]
        unseen=[x for x in sources if not any(fit(m,x['title']) for m in METHODS)]
        lines+=['','## Unclassified new signals — human/AI research queue','',
                'These may reveal NEW techniques outside the 26 approved templates, but are NOT executable business methods.',
                'A new technique needs a clear deliverable, customer, cost, rights review and fresh court trial before any local test.', '']
        for x in unseen[:25]:
            safe_title=x['title'].replace('|','/').replace('[','(').replace(']',')')
            lines.append(f"- {safe_title} — {x['url']} ({x['source']})")
        if not unseen: lines.append('- No unclassified public source signals recorded yet.')
        lines+=['','## Research boundaries','',
                'Public GitHub repositories, Hacker News discussions, and the official GitHub Blog RSS are weak idea signals.',
                'No copying source code into products, executing unfamiliar repositories, mass outreach, or fake conversions.',
                'Unlaunched ideas are retired after 14 days as UNLAUNCHED; actual tests use observed user-reported measurements.']
        atomic_text(out,'\n'.join(lines)+'\n')
        return str(out)

    def launch(self,iid,url):
        p=urllib.parse.urlsplit(url)
        if p.scheme!='https' or not p.hostname or p.username or p.password or p.fragment:
            raise ValueError('Use an actual HTTPS listing/portfolio URL')
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            old=c.execute('SELECT status FROM ideas WHERE id=?',(iid,)).fetchone()
            if not old or old['status']!='APPROVED_LOCAL_PLAN':
                c.execute('ROLLBACK');raise ValueError('Only court-approved unlaunched plans can be marked launched')
            launched_at=now_utc()
            c.execute("UPDATE ideas SET status='LAUNCHED_USER_REPORTED',launched_at=?,launch_url=? WHERE id=?",
                      (launched_at,url[:500],iid))
            self.audit(c,'launch',{'id':iid,'url':url[:500],'at':launched_at,'source':'user_reported'})
            c.execute('COMMIT')
        return 'USER_REPORTED_LAUNCH_NOT_VERIFIED'

    def record(self,iid,kind,quantity=1,gross_cents=0,fee_cents=0):
        if kind not in ('view','click','sale') or not isinstance(quantity,int) or quantity<=0 or quantity>100000:
            raise ValueError('Invalid kind or quantity')
        if not all(isinstance(n,int) and 0<=n<=100000000 for n in (gross_cents,fee_cents)):
            raise ValueError('Invalid money values')
        if kind!='sale' and (gross_cents or fee_cents):raise ValueError('Money amounts are only allowed on reported sales')
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            row=c.execute('SELECT status FROM ideas WHERE id=?',(iid,)).fetchone()
            if not row or row['status']!='LAUNCHED_USER_REPORTED':
                c.execute('ROLLBACK');raise ValueError('A real trial must be marked launched first')
            field={'view':'views','click':'clicks','sale':'sales'}[kind]
            c.execute(f'UPDATE ideas SET {field}={field}+?, gross_cents=gross_cents+?,fee_cents=fee_cents+? WHERE id=?',
                    (quantity,gross_cents,fee_cents,iid))
            self.audit(c,'event',{'id':iid,'kind':kind,'quantity':quantity,
                                  'gross_cents':gross_cents,'fee_cents':fee_cents,'source':'user_reported'})
            c.execute('COMMIT')
        return 'USER_REPORTED_UNVERIFIED'
