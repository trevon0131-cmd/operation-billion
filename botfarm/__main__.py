"""Zero-Cost Bot Farm CLI: all outputs start local and offline."""
import argparse
import hashlib
import json
import shutil
import sys
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from .catalog import BOTS
from .court import Proposal, adjudicate
from .dashboard import serve
from .experiments import recommendations
from .research import Research
from .runner import run_once, watch
from .storage import Store

DEFAULT_HOME=Path(__file__).resolve().parent.parent

def cents(amount):
    try:
        value=Decimal(amount)
        if not value.is_finite() or value < 0:
            raise ValueError('Amount must be a finite positive dollar amount')
        return int((value*100).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f'Invalid dollar amount: {amount}') from exc

def parser():
    p=argparse.ArgumentParser(prog='python -m botfarm', description='Free, local-first business idea farm; nothing is auto-published')
    p.add_argument('--home', type=Path, default=DEFAULT_HOME, help='Writable project folder (default: extracted ZIP folder)')
    cmd=p.add_subparsers(dest='command',required=True)
    cmd.add_parser('init',help='Initialize storage and show first steps')
    cmd.add_parser('roster',help='Show specialist bots')
    run=cmd.add_parser('run',help='Create approved local product drafts');run.add_argument('--live',action='store_true',help='Fetch live public signals');run.add_argument('--max-cases',type=int,default=12)
    wa=cmd.add_parser('watch',help='Run repeated research passes while this PC is on');wa.add_argument('--live',action='store_true');wa.add_argument('--interval',type=int,default=900);wa.add_argument('--max-cases',type=int,default=12)
    se=cmd.add_parser('serve',help='Serve read-only localhost dashboard');se.add_argument('--port',type=int,default=8765)
    apilot=cmd.add_parser('autopilot',help='Run automatic local work and dashboard in ONE process')
    apilot.add_argument('--live',action='store_true')
    apilot.add_argument('--interval',type=int,default=900)
    apilot.add_argument('--max-cases',type=int,default=8)
    apilot.add_argument('--port',type=int,default=8765)
    cmd.add_parser('autostart-install',help='OPT IN to start automatic local workflow at Windows sign-in')
    cmd.add_parser('autostart-remove',help='Remove Windows sign-in launcher')
    cmd.add_parser('status',help='Summary and audit validation')
    cmd.add_parser('audit-check',help='Exit with failure if the evidence audit chain is invalid')
    cmd.add_parser('learning',help='Conservative data-driven testing notes')
    cs=cmd.add_parser('court',help='Examine a courtroom record');cs.add_argument('case_id',type=int)
    risk=cmd.add_parser('trial',help='Test a risky case to see judge refuse it');risk.add_argument('--scenario',choices=['trademark','paid','publish','inventory','false-income','outreach'],required=True);risk.add_argument('--save',action='store_true',help='Add clearly marked demo rejection to local courtroom docket')
    re=cmd.add_parser('research',help='Show background market signals');re.add_argument('--live',action='store_true')
    ap=cmd.add_parser('mark-ready',help='After your own review, mark a draft ready for MANUAL publication');ap.add_argument('case_id',type=int);ap.add_argument('--rights-confirmed',action='store_true');ap.add_argument('--platform-reviewed',action='store_true')
    event=cmd.add_parser('record',help='Add manually reported data (never claimed verified)')
    event.add_argument('case_id',type=int);event.add_argument('kind',choices=['view','click','sale','refund']);event.add_argument('--quantity',type=int,default=1);event.add_argument('--gross',default='0');event.add_argument('--fee',default='0');event.add_argument('--note',default='')
    launch=cmd.add_parser('trial-launch',help='Record a listing that YOU actually published (no publication performed)');launch.add_argument('case_id',type=int);launch.add_argument('url')
    cmd.add_parser('experiments',help='See lifecycle status of all business experiments')
    # Research library: broadly explore 26 distinct no-upfront business techniques.
    ops=cmd.add_parser('opportunity-scan',help='Research public GitHub, Hacker News and blog RSS, and court-test local validation ideas')
    ops.add_argument('--live',action='store_true',help='Use fixed public API endpoints; no login required')
    ops.add_argument('--limit',type=int,default=3)
    ts=cmd.add_parser('trend-scan',help='Prepare Google Trends + GitHub/HN-backed startup kits for approved ideas')
    ts.add_argument('--live',action='store_true',help='Fetch only Google Trends official RSS; existing GitHub/HN signals are reused')
    ts.add_argument('--limit',type=int,default=5)
    cmd.add_parser('trend-report',help='Show saved public trend research and generated startup kits')
    cmd.add_parser('opportunity-list',help='Show income-technique catalog and previous research plans')
    cmd.add_parser('opportunity-review',help='Report 7/14-day experiment assessment and research audit')
    opl=cmd.add_parser('opportunity-launch',help='Record actual launched URL supplied by the user (unverified)')
    opl.add_argument('idea_id',type=int);opl.add_argument('url')
    opr=cmd.add_parser('opportunity-record',help='Record user-reported trial metrics, never claimed verified')
    opr.add_argument('idea_id',type=int);opr.add_argument('kind',choices=['view','click','sale'])
    opr.add_argument('--quantity',type=int,default=1);opr.add_argument('--gross',default='0');opr.add_argument('--fee',default='0')
    ays=cmd.add_parser('agent-youtube-search',help='Use optional installed Agent Reach to search public YouTube videos')
    ays.add_argument('query')
    qa=cmd.add_parser('video-queue-add',help='Queue a PUBLIC YouTube video for opt-in bounded autopilot research')
    qa.add_argument('url')
    cmd.add_parser('video-queue-list',help='List read-only public video research queue')
    qr=cmd.add_parser('video-queue-run',help='Research one queued public video; only with --live')
    qr.add_argument('--live',action='store_true')
    cmd.add_parser('internet-doctor',help='Check optional Agent Reach, video research and public internet access tools')
    vr=cmd.add_parser('video-research',help='Research ONE public YouTube video from metadata and subtitles; never download video media')
    vr.add_argument('url');vr.add_argument('--ai',action='store_true',help='Optionally summarize subtitles with local Ollama')
    vr.add_argument('--model',default='qwen3:8b')
    vf=cmd.add_parser('video-frames',help='Inspect local owner-provided video frames; optional Ollama vision')
    vf.add_argument('file');vf.add_argument('--ai',action='store_true');vf.add_argument('--model',default='qwen2.5vl:3b')
    cmd.add_parser('doctor',help='Check local optional integrations')
    brand=cmd.add_parser('seller-brand',help='Configure PUBLIC store brand for all drafts; no payments or identity')
    brand.add_argument('shop_name');brand.add_argument('--support-email',default='');brand.add_argument('--voice',default='clear and useful')
    cmd.add_parser('launch-queue',help='Create digital + local-service go-to-market packet from approved cases')
    cmd.add_parser('lead-list',help='Show manually supplied businesses and 14-day decisions')
    add=cmd.add_parser('lead-add',help='Add ONE public business and site you personally researched; no scraping or outreach')
    add.add_argument('business');add.add_argument('website')
    stage=cmd.add_parser('lead-stage',help='Record a MANUALLY observed business relationship status')
    stage.add_argument('lead_id',type=int);stage.add_argument('status');stage.add_argument('--note',default='')
    pack=cmd.add_parser('lead-pack',help='Prepare a service proposal from an approved freelance case')
    pack.add_argument('lead_id',type=int);pack.add_argument('case_id',type=int);pack.add_argument('--review-site',action='store_true')
    seller=cmd.add_parser('seller-prep' ,help='Prepare unlisted seller drafts for existing approved products'); seller.add_argument('--limit',type=int,default=100)
    business=cmd.add_parser('business-review',help='Review ONE user-supplied public business website, respecting robots.txt');business.add_argument('url')
    ai=cmd.add_parser('brainstorm',help='Optional LOCAL Ollama brainstorming (never publishes)');ai.add_argument('subject');ai.add_argument('--model',default='gemma3:1b')
    cmd.add_parser('money-paths',help='Show launchable zero-upfront income methods, not claimed earnings')
    cmd.add_parser('account-roadmap',help='Owner-only account setup instructions; no accounts accessed')
    cmd.add_parser('partner-tools',help='Curated researched GitHub projects, not downloaded or installed')
    mk=cmd.add_parser('money-kit',help='Court-gated local launch package for a selected business technique')
    mk.add_argument('method',help='Key from money-paths')
    mk.add_argument('topic',help='Specific target customer problem')
    mk.add_argument('--sample',action='store_true',help='Generate a court-approved local video/site sample if supported')
    cmd.add_parser('money-report',help='View audit-checked local launch packages; no actual sales implied')
    studio=cmd.add_parser('viral-studio',help='Court-approved ORIGINAL story, talking-fruit, quiz and tutorial videos')
    studio.add_argument('--format',choices=['fruit-story','fictional-reddit','quick-quiz','micro-drama','tips'],default='fruit-story')
    studio.add_argument('--topic',required=True)
    studio.add_argument('--ai',action='store_true',help='Optional local Qwen/Ollama script')
    studio.add_argument('--model',default='qwen3:8b')
    studio.add_argument('--narrate',action='store_true',help='Use existing separate local Kokoro voice setup')
    studio.add_argument('--voice',default='af_sarah')
    studio.add_argument('--render',action='store_true',help='Render an MP4 with FFmpeg; never uploads')
    cmd.add_parser('ai-video-doctor',help='Check GPU, RAM, FFmpeg and local ComfyUI readiness for REAL animation; downloads nothing')
    vmplan=cmd.add_parser('ai-video-plan',help='Generate 5 consistent AI-motion prompts from a court-approved video draft')
    vmplan.add_argument('--folder',required=True,help='Existing output/viral_studio/fruit-story/<ID> folder')
    vmass=cmd.add_parser('ai-video-assemble',help='Join five real moving video clips and Kokoro narration; no slide substitutes')
    vmass.add_argument('--folder',required=True);vmass.add_argument('--clips',default='')
    vmass.add_argument('--rights-confirmed',action='store_true',help='Confirm you have commercial rights to the input clips')
    vmass.add_argument('--width',type=int,choices=[360,540,720],default=540)
    vmcomfy=cmd.add_parser('ai-video-comfy',help='Queue one REAL video generation to your own localhost ComfyUI using its API-format workflow')
    vmcomfy.add_argument('--folder',required=True);vmcomfy.add_argument('--workflow',required=True)
    vmcomfy.add_argument('--text-node',required=True,help='ID of positive CLIP/text prompt node in YOUR exported workflow')
    vmcomfy.add_argument('--scene',type=int,choices=range(1,6),required=True)
    vmfetch=cmd.add_parser('ai-video-comfy-fetch',help='Download finished video clip from the owner-queued LOCAL ComfyUI prompt')
    vmfetch.add_argument('--folder',required=True);vmfetch.add_argument('--scene',type=int,choices=range(1,6),required=True);vmfetch.add_argument('--prompt-id',required=True)
    cmd.add_parser('viral-formats',help='See original local creator formats and free GitHub references')
    cmd.add_parser('media-doctor',help='Free AI-media sources and real local render capabilities; no downloads')
    polish=cmd.add_parser('video-polish',help='Add camera motion and fades to an existing court-approved video draft using local FFmpeg')
    polish.add_argument('--folder',default='',help='Existing expansion video draft folder; default newest')
    polish.add_argument('--narration',default='',help='Optional YOUR licensed MP3/WAV/M4A narration')
    polish.add_argument('--images',default='',help='Optional YOUR licensed scene_01.png through scene_05.png from a local AI/image tool')
    polish.add_argument('--rights-confirmed',action='store_true',help='You have commercial rights to the optional imported assets')
    polish.add_argument('--width',type=int,choices=(270,540,720),default=540)
    cmd.add_parser('toolbox',help='Show reviewed open-source AI/video/website tool registry; not automatically installed')
    free=cmd.add_parser('free-tools',help='Show zero-upfront local tools and capabilities; no downloads')
    free.add_argument('--need',default='',help='Filter: videos, websites, ideas, services, audio, etc')
    cmd.add_parser('free-doctor',help='Check which $0 tools are really installed; no installs or billing')
    fp=cmd.add_parser('free-plan',help='Generate no-spend startup instructions; optional court-reviewed local sample')
    fp.add_argument('need',help='videos, websites, stickers, documents, services, research, audio, captions, ideas, content, templates')
    fp.add_argument('topic')
    fp.add_argument('--build',action='store_true',help='Create a local court-reviewed sample for supported video/website plans')
    fs=cmd.add_parser('free-scout',help='Discover unreviewed GitHub tool candidates; never downloads or runs them')
    fs.add_argument('--live',action='store_true',help='Opt in to fixed public GitHub searches with daily caching')
    cmd.add_parser('free-findings',help='View unreviewed public tool candidate evidence with audit check')
    video=cmd.add_parser('video-demo',help='Create original short or long video sample; optional FFmpeg MP4 render')
    video.add_argument('--topic',default='Create an educational short')
    video.add_argument('--format',choices=['short','youtube'],default='short')
    video.add_argument('--render',action='store_true',help='Try local FFmpeg MP4 export if installed')
    video.add_argument('--ai',action='store_true',help='Optional local Ollama script; falls back if unavailable')
    site=cmd.add_parser('site-demo',help='Build a safe, fictional, responsive business website locally')
    site.add_argument('--niche',default='local cafe')
    cmd.add_parser('expansion-run',help='Automatically create fresh court-approved local creator and website samples')
    cmd.add_parser('expansion-report',help='Review expansion drafts, provenance and audit integrity')
    return p

def main(argv=None):
    args=parser().parse_args(argv)
    home=args.home.expanduser().resolve()
    if args.command in ('ai-video-doctor','ai-video-plan','ai-video-assemble','ai-video-comfy','ai-video-comfy-fetch'):
        from .ai_video_bridge import hardware, comfy_status, plan as motion_plan, assemble as motion_assemble, comfy_queue, comfy_fetch
        if args.command=='ai-video-doctor':
            result={'hardware':hardware(),'comfyui':comfy_status(),
                    'note':'No real generative video model is bundled or silently installed. Use proper model weights and GPU.'}
        elif args.command=='ai-video-plan':result=motion_plan(args.folder)
        elif args.command=='ai-video-assemble':
            result=motion_assemble(args.folder,args.clips or None,args.rights_confirmed,args.width)
        elif args.command=='ai-video-comfy':result=comfy_queue(args.folder,args.workflow,args.text_node,args.scene)
        else:result=comfy_fetch(args.folder,args.scene,args.prompt_id)
        print(json.dumps(result,indent=2));return 0
    if args.command in ('viral-studio','viral-formats'):
        from .viral_studio import make as studio_make, doctor as studio_doctor
        result=studio_doctor(home) if args.command=='viral-formats' else studio_make(
            home,args.format,args.topic,ai=args.ai,narrate=args.narrate,
            render=args.render,voice=args.voice,model=args.model)
        print(json.dumps(result,indent=2));return 0
    if args.command in ('media-doctor','video-polish'):
        from .ai_media_lab import latest_draft, polish as polish_video, report as media_report
        if args.command=='media-doctor': result=media_report()
        else:
            draft=Path(args.folder) if args.folder else latest_draft(home)
            result=polish_video(draft,audio=args.narration or None,
                                images=args.images or None,rights_confirmed=args.rights_confirmed,
                                width=args.width)
        print(json.dumps(result,indent=2));return 0
    if args.command in ('money-paths','account-roadmap','partner-tools','money-kit','money-report'):
        from .money_studio import MoneyStudio, options, ACCOUNTS, TOOLS
        if args.command=='money-paths':result={'methods':options(),'trading':False}
        elif args.command=='account-roadmap':result={'accounts':ACCOUNTS,'connected_now':False,'owner_setup_required':True}
        elif args.command=='partner-tools':result={'tools':TOOLS,'installed_by_this_upgrade':False,'automatic_downloads':False}
        else:
            studio=MoneyStudio(home)
            result=studio.create(args.method,args.topic,make_sample=args.sample) if args.command=='money-kit' else studio.report()
        print(json.dumps(result,indent=2));return 0
    if args.command in ('free-tools','free-doctor','free-plan','free-scout','free-findings'):
        from .free_tool_hub import FreeToolHub, available_tools, free_doctor
        if args.command=='free-tools': result={'tools':available_tools(args.need), 'no_auto_install':True}
        elif args.command=='free-doctor':result=free_doctor()
        else:
            hub=FreeToolHub(home)
            if args.command=='free-plan':result=hub.plan(args.need,args.topic,execute_local=args.build)
            elif args.command=='free-scout':result=hub.scan(live=args.live)
            else:result={'unreviewed_candidates':hub.findings(),'audit_valid':hub.audit_valid()}
        print(json.dumps(result,indent=2));return 0
    if args.command in ('toolbox','video-demo','site-demo','expansion-run','expansion-report'):
        from .creator_website_wing import Wing, TOOLS
        if args.command=='toolbox':
            from .free_tool_hub import available_tools
            result={'tools':available_tools(),'auto_downloaded_or_installed':False,'policy':'curated $0-upfront tools only; paid-hosted dependencies excluded'}
        else:
            wing=Wing(home)
            if args.command=='video-demo':result=wing.create(args.format,args.topic,render=args.render,use_ai=args.ai)
            elif args.command=='site-demo':result=wing.create('website',args.niche)
            elif args.command=='expansion-run':result=wing.cycle()
            else:result=wing.overview()
        print(json.dumps(result,indent=2))
        return 0
    if args.command in ('trend-scan','trend-report'):
        from .trend_engine import TrendEngine
        engine=TrendEngine(home)
        if args.command=='trend-scan':
            result=engine.scan(live=args.live,limit=args.limit)
        else:
            with engine.connect() as conn:
                kits=[dict(x) for x in conn.execute('SELECT idea_id,method_key,path,generated_at FROM kits ORDER BY idea_id DESC LIMIT 40')]
            result={'startup_kits':kits,'source_count':len(engine.source_rows()),'audit_valid':engine.audit_valid()}
        print(json.dumps(result,indent=2))
        return 0
    if args.command.startswith('opportunity-'):
        from .opportunity_lab import OpportunityLab, METHODS
        lab=OpportunityLab(home)
        if args.command=='opportunity-scan':
            result=lab.scan(live=args.live,limit=args.limit)
        elif args.command=='opportunity-list':
            result={'overview':lab.overview(),'available_techniques':[{'key':m.key,'lane':m.lane,'offer':m.offer} for m in METHODS],
                    'recent_experiments':lab.rows(50)}
        elif args.command=='opportunity-review':
            result={'newly_retired':lab.retire_due(),'overview':lab.overview(),'audit_valid':lab.audit_valid(),
                    'research_library':lab.write_index()}
        elif args.command=='opportunity-launch':
            result={'result':lab.launch(args.idea_id,args.url),'real_world_status':'NOT_INDEPENDENTLY_VERIFIED'}
        else:
            result={'result':lab.record(args.idea_id,args.kind,args.quantity,cents(args.gross),cents(args.fee)),
                    'real_world_status':'NOT_INDEPENDENTLY_VERIFIED'}
        print(json.dumps(result,indent=2))
        return 0
    if args.command=='seller-brand':
        from .seller_ops import update_public_brand
        print('Public shop profile saved:',update_public_brand(home,args.shop_name,args.support_email,args.voice))
        return 0
    if args.command=='launch-queue':
        from .launch_workflow import export
        print(json.dumps(export(home,Store(home)),indent=2))
        return 0
    if args.command in ('lead-add','lead-list','lead-stage','lead-pack'):
        from .client_pipeline import ClientPipeline
        clients=ClientPipeline(home)
        if args.command=='lead-list':
            print(json.dumps({'leads':clients.reviews(),'audit_valid':clients.audit_valid()},indent=2))
        elif args.command=='lead-add':
            print('User-supplied lead number:',clients.add(args.business,args.website))
        elif args.command=='lead-stage':
            print('USER-REPORTED lead status:',clients.stage(args.lead_id,args.status,args.note))
        else:
            print(json.dumps(clients.pack(args.lead_id,Store(home),args.case_id,with_review=args.review_site),indent=2))
        return 0
    if args.command=='seller-prep':
        from .seller_ops import refresh_all
        store=Store(home)
        print(json.dumps(refresh_all(home,store,args.limit),indent=2))
        return 0
    if args.command=='business-review':
        from .business_scout import review_one
        print(json.dumps(review_one(home,args.url),indent=2))
        return 0
    if args.command=='roster':
        for i,b in enumerate(BOTS,1):
            print(f'{i:02d} {b.name:28} | {b.lane:25} | {b.channel}')
        print(f'{len(BOTS)} specialists; court staff are additional review roles.')
        return 0
    if args.command=='brainstorm':
        from .ollama_adapter import brainstorm
        print(brainstorm(args.subject, args.model));return 0
    if args.command=='agent-youtube-search':
        from .internet_hub import agent_reach_youtube_search
        print(json.dumps(agent_reach_youtube_search(home,args.query),indent=2));return 0
    if args.command in ('video-queue-add','video-queue-list','video-queue-run'):
        from .internet_hub import queue_video, show_queue, process_video_queue
        if args.command=='video-queue-add': result=queue_video(home,args.url)
        elif args.command=='video-queue-list':result=show_queue(home)
        else:result=process_video_queue(home,live=args.live)
        print(json.dumps(result,indent=2));return 0
    if args.command in ('internet-doctor','video-research','video-frames'):
        from .internet_hub import doctor as internet_doctor, read_public_video, inspect_local_video
        if args.command=='internet-doctor': result=internet_doctor()
        elif args.command=='video-research': result=read_public_video(home,args.url,ai=args.ai,model=args.model)
        else:result=inspect_local_video(home,args.file,ai=args.ai,model=args.model)
        print(json.dumps(result,indent=2));return 0
    if args.command=='doctor':
        print('Python:',sys.version.split()[0]);print('Project home:',home)
        print('Ollama:',shutil.which('ollama') or 'optional, not found')
        print('Agent-Reach:',shutil.which('agent-reach') or 'optional, not found')
        print('Free core: Python standard library only; no marketplace credentials required')
        print('Opportunity lab: 39 research techniques; GitHub/HN public APIs and Google Trends RSS startup kits')
        print('Creator/website expansion: original PNG/SRT, HTML/CSS, optional FFmpeg:',shutil.which('ffmpeg') or 'not installed')
        print('No marketplace publishing integrations installed. Seller drafts only; website review is opt-in.')
        from .free_tool_hub import free_doctor
        print('Free local tool report:',json.dumps(free_doctor(),sort_keys=True))
        return 0
    if args.command=='research':
        print(json.dumps(Research(home).collect(online=args.live),indent=2));return 0
    store=Store(home)
    if args.command=='init':
        print('Initialized:',store.db)
        print('Run: python -m botfarm run --max-cases 12')
        print('Then: python -m botfarm serve')
        print('For public market signals: python -m botfarm watch --live')
    elif args.command=='run':
        print(json.dumps(run_once(home,live=args.live,max_cases=args.max_cases),indent=2))
    elif args.command=='watch':
        watch(home,interval=args.interval,live=args.live,max_cases=args.max_cases)
    elif args.command=='serve':
        serve(home,args.port)
    elif args.command=='autopilot':
        from .autopilot import run_autopilot
        run_autopilot(home,interval=args.interval,live=args.live,max_cases=args.max_cases,port=args.port)
    elif args.command=='autostart-install':
        from .autopilot import install_autostart
        print('Autostart installed:',install_autostart(home))
        print('It will run only after your Windows sign-in, not while the computer is off.')
    elif args.command=='autostart-remove':
        from .autopilot import uninstall_autostart
        print('Autostart removed:',uninstall_autostart())
    elif args.command=='status':
        print(json.dumps(store.summary(),indent=2))
    elif args.command=='audit-check':
        if not store.audit_valid():
            raise RuntimeError('Evidence audit chain invalid')
        from .client_pipeline import ClientPipeline
        if not ClientPipeline(home).audit_valid(): raise RuntimeError('Client pipeline audit invalid')
        from .creator_website_wing import Wing
        if not Wing(home).audit_valid(): raise RuntimeError('Creator/website expansion audit invalid')
        from .opportunity_lab import OpportunityLab
        if not OpportunityLab(home).audit_valid(): raise RuntimeError('Opportunity research audit invalid')
        from .trend_engine import TrendEngine
        if not TrendEngine(home).audit_valid(): raise RuntimeError('Trend startup kits audit invalid')
        from .free_tool_hub import FreeToolHub
        if not FreeToolHub(home).audit_valid(): raise RuntimeError('Free-tool scout audit invalid')
        print('Farm + client + opportunity + trend startup + free-tool scout audit chains: VALID')
    elif args.command=='learning':
        print(json.dumps(recommendations(store),indent=2))
    elif args.command=='court':
        row=store.case(args.case_id)
        if not row: raise ValueError('Case not found')
        print('Case:',row['id'],row['title'],'|',row['human_status'])
        print(json.dumps(json.loads(row['case_json']),indent=2))
        print('Artifact folder:',row['artifact_dir'] or 'None')
    elif args.command=='mark-ready':
        store.approve_for_manual_publication(args.case_id,args.rights_confirmed,args.platform_reviewed)
        print('Marked ready for YOU to publish manually. Nothing was uploaded or sold.')
    elif args.command=='trial-launch':
        result=store.mark_trial_launched(args.case_id,args.url)
        print('Recorded external launch (user-supplied, NOT independently verified):',result)
    elif args.command=='experiments':
        from .lifecycle import assess
        print(json.dumps([{'case_id':r['id'],'bot_key':r['bot_key'],
             'decision':assess(r).classification,'published':bool(r['launched_at']),
             'retired':bool(r['retired_at'])} for r in store.trial_rows()],indent=2))
    elif args.command=='record':
        store.record_event(args.case_id,args.kind,args.quantity,cents(args.gross),cents(args.fee),args.note)
        print('Recorded as USER-REPORTED, UNVERIFIED data; not proof of a marketplace transaction.')
    elif args.command=='trial':
        options={
          'trademark':dict(third_party_ip=True,has_rights=False),
          'paid':dict(expenditure_usd=0.20),
          'publish':dict(action='publish_to_marketplace'),
          'inventory':dict(requires_inventory=True,inventory_confirmed=False),
          'false-income':dict(expected_revenue_claim='$1,000 guaranteed'),
          'outreach':dict(requires_outreach=True),
        }
        p=Proposal(bot_key='special_court_test',title='Risk screening scenario: '+args.scenario,**options[args.scenario])
        judgment=adjudicate(p)
        print(json.dumps(judgment.data(),indent=2))
        if args.save:
            fp=hashlib.sha256(('court-demo-v1:'+args.scenario).encode()).hexdigest()
            cid=store.add_case(fp,'demo_risk_test',p.title,0,judgment.data())
            print('Saved DEMONSTRATION rejection as court case:', cid or 'already exists')
        else:
            print('This was a court demonstration. Nothing executed or stored.')
    return 0

if __name__=='__main__':
    try: raise SystemExit(main())
    except (ValueError,RuntimeError,OSError) as exc:
        print('ERROR:',exc,file=sys.stderr);raise SystemExit(2)
