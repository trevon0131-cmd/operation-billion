"""Bounded autonomous local operation: propose -> court -> repair -> create -> QC.

No platform logins, remote publication, payments, claims of sales, or customer
outreach. External selling requires a separately reviewed, authenticated adapter.
"""
import hashlib
import json
import time
from datetime import datetime, timezone
from dataclasses import replace
from pathlib import Path
from .catalog import BOTS
from .court import adjudicate
from .quality import inspect, prepare_sell_kit
from .seller_ops import package_case
from .lifecycle import assess, choose_new_technique
from .research import Research
from .storage import Store
from .strategy import MAX_VARIANTS, propose, repair
from .workshop import make_artifact, atomic_text

DAILY_CASE_CAP = 32


def candidate_fingerprint(bot, candidate, variant, is_repair=False):
    return hashlib.sha256(f'farm-v2\0{bot.key}\0{variant}\0{candidate.proposal.title}\0{is_repair}'.encode()).hexdigest()


def create_case(store, home, bot, candidate, variant, signals, is_repair=False):
    fp = candidate_fingerprint(bot,candidate,variant,is_repair)
    judgment=adjudicate(candidate.proposal, budget=0.0)
    cid=store.add_case(fp, bot.key, candidate.proposal.title, variant, judgment.data(),daily_cap=DAILY_CASE_CAP)
    if cid is None: return None
    path=''; qc={'passed':False, 'issues':['Not attempted'], 'checked_files':[]}
    if judgment.verdict == 'NOT GUILTY':
        try:
            path_obj=make_artifact(home,candidate.bot,variant,fp,signals)
            qc=inspect(path_obj)
            if qc['passed']:
                # 'research only' outputs get useful research plans, not pretended sale bundles.
                if candidate.bot.suggested_price > 0:
                    prepare_sell_kit(path_obj,candidate.bot.channel)
                if store.update_artifact(cid,str(path_obj)):
                    path=str(path_obj)
                    try:
                        package_case(home, store.case(cid))
                    except (OSError, ValueError) as exc:
                        qc['seller_operations_warning'] = str(exc)[:180]
            else:
                # Left unfinished rather than claiming a successful artifact.
                path=''
        except (OSError, ValueError, RuntimeError) as e:
            qc={'passed':False,'issues':[f'{type(e).__name__}: {str(e)[:150]}'], 'checked_files':[]}
    return {'case_id':cid,'bot':bot.name,'verdict':judgment.verdict,
            'folder':path,'variant':variant+1,'quality':qc,'idea':candidate.proposal.title}


def run_once(home: Path, live=False, max_cases=12, now=None):
    if max_cases <= 0 or max_cases > 32:
        raise ValueError('Max cases must be between 1 and 32')
    store=Store(home)
    if not store.audit_valid():
        raise RuntimeError('Audit chain invalid; execution halted until reviewed')
    # Rotate through distinct approved business paths daily, using the same local
    # court and no external account permissions. Independent of primary case cap.
    from .money_studio import MoneyStudio
    money_kit=MoneyStudio(home).daily_idea(now=now)
    recovery=[]
    for pending in store.unfinished_artifacts():
        bot=next((b for b in BOTS if b.key==pending['bot_key']),None)
        if not bot: continue
        try:
            version=replace(bot,subject=pending['title'])
            if bot.key=='ebay_sticker_scout' and pending['title']=='Zero-inventory digital sticker product alternative':
                version=replace(version,artifact='svg',suggested_price=3.0,channel='Ko-fi / Gumroad')
            path=make_artifact(home,version,pending['variant'],pending['fingerprint'],[])
            if inspect(path)['passed']:
                if version.suggested_price > 0:
                    prepare_sell_kit(path,version.channel)
                if store.update_artifact(pending['id'],str(path)):
                    try:
                        package_case(home, store.case(pending['id']))
                    except (OSError, ValueError):
                        pass  # The product still exists; seller-prep can retry later.
                    recovery.append(pending['id'])
        except (OSError, ValueError, RuntimeError):
            continue
    # Broader independent research brain: separate evidence ledger and public-source court.
    # It prepares test plans only, never executes downloaded GitHub code or sends outreach.
    from .opportunity_lab import OpportunityLab
    research_hub=OpportunityLab(home).scan(live=live,limit=3,now=now)
    from .trend_engine import TrendEngine
    startup_hub=TrendEngine(home).scan(live=live,limit=3,now=now)
    from .free_tool_hub import FreeToolHub
    free_hub=FreeToolHub(home).scan(live=live,limit=3,now=now)
    # Fetch current public sources even when the daily case cap has been reached.
    signals=Research(home).collect(online=live)
    retired=[]
    for trial in store.trial_rows():
        decision=assess(trial,now=now)
        if decision.action=='retire' and store.retire_trial(trial['id'],decision.classification,decision.explanation):
            retired.append({'case_id':trial['id'],'bot_key':trial['bot_key'],
                            'reason':decision.classification,'days':round(decision.days,1)})
    room=DAILY_CASE_CAP-store.daily_count()
    if room <= 0:
        return {'created':[],'recovered_case_ids':recovery,'repairs':[],'retired':retired,'pivots':[],
                'skipped':'Daily proposal limit reached; will resume next UTC day.',
                'signals':signals,'online':live,'money_studio':money_kit,'opportunity_lab':research_hub,'startup_hub':startup_hub,'free_tool_hub':free_hub}
    links=tuple(s['url'] for s in signals if s.get('confidence')=='weak-interest-signal-only' and s.get('url'))
    created=[];repairs=[];pivots=[]
    # Resume any retirement awaiting its next DIFFERENT business technique.
    for retired_trial in store.pending_trial_pivots():
        if len(created)>=min(room,max_cases): break
        counts=store.bot_case_counts()
        choice=choose_new_technique(retired_trial['bot_key'],counts,store.retired_bot_keys())
        if choice is None: continue  # Known techniques exhausted; no imaginary new business.
        variant=counts.get(choice.key,0)
        idea=propose(choice,variant,links)
        fp=candidate_fingerprint(choice,idea,variant)
        existing=store.case_by_fingerprint(fp)
        if existing and existing['verdict']=='NOT GUILTY' and existing['artifact_dir']:
            cid=existing['id']
        elif existing:
            continue
        else:
            trial=create_case(store,home,choice,idea,variant,signals)
            if trial is None: continue
            created.append(trial)
            if trial['verdict']!='NOT GUILTY' or not trial['folder']: continue
            cid=trial['case_id']
        reason='Switch from '+retired_trial['bot_key']+' ('+retired_trial['classification']+') to '+choice.key+'; new business lane: '+choice.lane
        if store.record_trial_pivot(retired_trial['old_case_id'],cid,reason):
            pivots.append({'old_case_id':retired_trial['old_case_id'],'new_case_id':cid,
                           'new_bot':choice.key,'different_lane':choice.lane})
    # Resume a GUILTY proposal on restart / next day rather than forgetting it.
    from .court import Judgment
    for past in store.pending_rejections():
        if len(created)>=min(room,max_cases): break
        bot=next((b for b in BOTS if b.key==past['bot_key']),None)
        if not bot or bot.key in store.retired_bot_keys(): continue  # Do not resurrect retired business techniques
        old=Judgment(**json.loads(past['case_json']))
        candidate=propose(bot,past['variant'],links)
        alternative=repair(candidate,old)
        if alternative is None: continue
        fp=candidate_fingerprint(bot,alternative,past['variant'],True)
        existing=store.case_by_fingerprint(fp)
        if existing and existing['verdict']=='NOT GUILTY' and existing['artifact_dir']:
            new_id=existing['id']
        elif existing:
            continue
        else:
            try:
                fresh=create_case(store,home,bot,alternative,past['variant'],signals,is_repair=True)
            except ValueError as err:
                if 'Daily court-case cap' in str(err): break
                raise
            if fresh is None: continue
            created.append(fresh)
            if fresh['verdict']!='NOT GUILTY' or not fresh['folder']: continue
            new_id=fresh['case_id']
        if store.record_revision(past['id'],new_id,alternative.change):
            repairs.append({'rejected_case_id':past['id'], 'replacement_case_id':new_id,
                            'change':alternative.change})
    counts=store.bot_case_counts()
    # Give all specialties a turn. Winners cannot monopolize the research loop.
    stopped_keys=store.retired_bot_keys()
    bots=sorted((b for b in BOTS if b.key not in stopped_keys),key=lambda b:(counts.get(b.key,0),BOTS.index(b)))
    measurements=store.metrics()
    for bot in bots:
        if len(created)>=min(room,max_cases): break
        variant=counts.get(bot.key,0)
        if variant>=MAX_VARIANTS: continue
        own_results=[r for r in measurements if r['bot_key']==bot.key]
        candidate=propose(bot,variant,links,own_results)
        try:
            first=create_case(store,home,bot,candidate,variant,signals)
        except ValueError as err:
            if 'Daily court-case cap' in str(err): break
            raise
        if first is None: continue
        created.append(first)
        if first['verdict']=='GUILTY':
            # Rejected actions never execute. The replacement has a NEW court case.
            old_case=store.case(first['case_id'])
            from .court import Judgment
            data=json.loads(old_case['case_json'])
            original_judgment=Judgment(**data)
            alt=repair(candidate,original_judgment)
            if not alt: continue
            try:
                second=create_case(store,home,bot,alt,variant,signals,is_repair=True)
            except ValueError as err:
                if 'Daily court-case cap' in str(err): break
                raise
            if second is None: continue
            created.append(second)
            if second['verdict']=='NOT GUILTY' and second['folder']:
                store.record_revision(first['case_id'],second['case_id'],alt.change)
                repairs.append({'rejected_case_id':first['case_id'],
                                'replacement_case_id':second['case_id'], 'change':alt.change})
    return {'created':created,'recovered_case_ids':recovery,'repairs':repairs,
            'retired':retired,'pivots':pivots,
            'signals':signals,'online':live,'money_studio':money_kit,'opportunity_lab':research_hub,'startup_hub':startup_hub,'free_tool_hub':free_hub,
            'skipped':'' if created else 'Current bounded experiments exhausted; continue reviewing real market outcomes.'}


def watch(home:Path, interval=900, live=False, max_cases=12):
    if interval<300:
        raise ValueError('Use 300 seconds or more to respect public API limits')
    print('Autonomous LOCAL workflow started. Ctrl+C stops the process.',flush=True)
    try:
        while True:
            try:
                summary=run_once(home,live=live,max_cases=max_cases)
                from .creator_website_wing import Wing
                expansion=Wing(home).cycle()   # two bounded, court-approved LOCAL samples/day
                from .viral_studio import daily_studio
                viral = daily_studio(home)  # one original style/day; local only
                from .internet_hub import process_video_queue
                internet_video = process_video_queue(home,live=live)  # max one public video per cycle if queued
                from .launch_workflow import export as export_launch_queue
                launch=export_launch_queue(home,Store(home))
                atomic_text(home/'data'/'autopilot_status.json', json.dumps({
                    'last_cycle_utc':datetime.now(timezone.utc).isoformat(timespec='seconds'),
                    'new_cases':len(summary['created']),
                    'repairs':len(summary['repairs']),
                    'retired':len(summary['retired']),
                    'technique_pivots':len(summary['pivots']),
                    'online_research_requested':bool(live),
                    'opportunity_research':summary.get('opportunity_lab',{}).get('overview',{}),
                    'trend_startup_kits':len(summary.get('startup_hub',{}).get('startup_kits_created',[])),
                    'creator_website_expansion':expansion,
                    'viral_studio_daily_local_draft':viral,
                    'free_tool_scout':summary.get('free_tool_hub',{}),
                    'opt_in_public_video_research':internet_video,
                    'sales_integrations_connected':False,
                    'external_publishing_enabled':False,
                    'digital_draft_count':launch['digital_product_drafts'],
                    'service_template_count':launch['service_offer_templates'],
                    'client_prospects_user_supplied':launch['prospects_user_supplied']
                },indent=2))
                print(json.dumps({'new_cases':len(summary['created']),
                                  'retired':summary['retired'],'technique_pivots':summary['pivots'],
                                  'repairs':summary['repairs'],
                                  'recovered':summary['recovered_case_ids'],
                                  'online':summary['online'],'research_briefs':len(summary.get('opportunity_lab',{}).get('new_plans',[])),
                                  'startup_kits':len(summary.get('startup_hub',{}).get('startup_kits_created',[])),'skipped':summary['skipped']},indent=2),flush=True)
            except RuntimeError as err:
                if 'Audit chain invalid' in str(err):
                    print('FATAL: '+str(err),flush=True)
                    break
                print('Transient worker error: '+str(err),flush=True)
            except (OSError, ValueError) as err:
                print(f'Worker error ({type(err).__name__}): {err}',flush=True)
            time.sleep(interval)
    except KeyboardInterrupt:
        print('Autopilot stopped cleanly.',flush=True)
