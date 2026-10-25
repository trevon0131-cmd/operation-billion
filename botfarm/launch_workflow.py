"""Local go-to-market operations for two simultaneous zero-upfront-cost lanes.

No external publication, seller logins, payment processing or made-up validation.
"""
import json
from pathlib import Path
from .catalog import BY_KEY
from .quality import inspect
from .seller_ops import package_case
from .client_pipeline import ClientPipeline
from .lifecycle import assess
from .workshop import atomic_text


def collect_work(home, store, limit=100):
    """Ground queue in existing approved, non-retired real artifacts."""
    root=(Path(home)/'output').resolve()
    statuses={x['id']:x for x in store.trial_rows()}
    digital=[];services=[];excluded=[]
    for case in store.cases(limit):
        if case['verdict']!='NOT GUILTY' or not case['artifact_dir']:
            continue
        bot=BY_KEY.get(case['bot_key'])
        if not bot or bot.suggested_price<=0:continue
        trial=statuses.get(case['id'])
        if trial is None or trial.get('retired_at'):
            continue
        path=Path(case['artifact_dir']).resolve()
        if not path.is_relative_to(root) or not inspect(path)['passed']:
            excluded.append({'case_id':case['id'],'reason':'product fails QC or escapes output tree'})
            continue
        lane='services' if bot.channel=='Freelance delivery' else 'digital'
        result={'case_id':case['id'],'bot':bot.name,'product':case['title'],
            'lane':lane,'template_folder':str(path),'channel_hint':bot.channel,
            'suggested_price_usd':round(bot.suggested_price,2),
            'published':bool(trial.get('launched_at')),'trial_url_user_reported':trial.get('listing_url') or '',
            'decision':assess(trial).classification,'evidence_source':'LOCAL_DRAFT / USER_REPORTED',
            'external_account_connected':False}
        if lane=='services':services.append(result)
        else:digital.append(result)
    return {'digital':digital, 'services':services, 'excluded':excluded,
            'connected_store_accounts':0,'verified_sales_count':0}


def export(home, store, limit=100):
    if not store.audit_valid():raise RuntimeError('Farm audit invalid; workflow paused')
    if not (1<=limit<=1000):raise ValueError('Limit must be between 1 and 1000')
    home=Path(home)
    queue=collect_work(home,store,limit)
    out=home/'output'/'sales_workflow'
    out.mkdir(parents=True,exist_ok=True)
    errors=[]
    for lane in ('digital','services'):
        for item in queue[lane]:
            row=store.case(item['case_id'])
            try:package_case(home,row)
            except (ValueError,OSError,KeyError) as exc:
                errors.append({'case_id':item['case_id'],'problem':str(exc)[:180]})
    c=ClientPipeline(home)
    if not c.audit_valid():raise RuntimeError('Client-pipeline audit invalid; workflow paused')
    queue['client_pipeline']=c.reviews()
    stagnant=[x for x in queue['client_pipeline'] if x['decision'].startswith(('NO_REPORTED_RESPONSE_14D','UNLAUNCHED_14D'))]
    queue['service_pivot_review']=[{'lead_id':x['lead_id'], 'decision':x['decision'],
       'alternatives':[{'case_id':q['case_id'],'technique':q['bot']} for q in queue['services'][:3]],
       'claim':'Suggestions only, not court re-approvals or customer results'} for x in stagnant]
    queue['preparation_errors']=errors
    count_digital=len(queue['digital']);count_services=len(queue['services'])
    queue['summary']={'digital_product_drafts':count_digital,'service_offer_templates':count_services,
                      'prospects_user_supplied':len(queue['client_pipeline']),
                      'ready_for_unattended_sale':0,'marketplace_publishing_available':False}
    atomic_text(out/'DUAL_LANE_LAUNCH_QUEUE.json',json.dumps(queue,indent=2))
    digital_lines=[f"- Case #{x['case_id']}: {x['product']} — ${x['suggested_price_usd']:.2f} hypothesis; {x['decision']}" for x in queue['digital'][:20]]
    service_lines=[f"- Case #{x['case_id']}: {x['product']} — service template; {x['decision']}" for x in queue['services'][:20]]
    markdown=(
        '# OPERATION BILLION — REAL-WORLD VALIDATION QUEUE\n\n'
        '**Nothing in this file was posted or sold. Sales are not verified.**\n\n'
        '## Lane 1 — Digital products (manual first listing, then measure)\n\n'
        + ('\n'.join(digital_lines) or 'No court-approved digital products yet.') + '\n\n'
        '1. Choose one original, useful, quality-checked product and review its files.\n'
        '2. Open your own Ko-fi shop, complete payment and seller verification and review fees/rights.\n'
        '3. Copy CHANNEL_LISTING_DRAFT.md and upload the appropriate contents of PRODUCT_PACKAGE.zip.\n'
        '4. Preview the actual marketplace listing; do not promise physical shipment of digital files.\n'
        '5. After publishing personally, use `py -3 -m botfarm trial-launch CASE_ID https://actual-listing-url`.\n'
        '6. Record real observed views/clicks/sales without inventing figures. Outcome thresholds: 7 days + 100 views/0 clicks; 14 days without positive net outcome.\n'
        '7. The autonomous worker retires poor trials and suggests a DIFFERENT business technique.\n\n'
        '## Lane 2 — Local business services (prospect → proposal → client)\n\n'
        + ('\n'.join(service_lines) or 'No court-approved service templates yet.') + '\n\n'
        '1. Identify one real business using a permitted source, and verify its actual public website.\n'
        '2. Add it: `py -3 -m botfarm lead-add "Business Name" https://their-actual-public-website`.\n'
        '3. Prepare a proposal tied to a court-approved service case: `py -3 -m botfarm lead-pack LEAD_ID CASE_ID`.\n'
        '4. Optionally review the site by using `--review-site` (respect robots; report is heuristic only).\n'
        '5. Review the outreach draft yourself; no automated sending, bulk email or contact scraping.\n'
        '6. If you personally contacted the business, record `py -3 -m botfarm lead-stage LEAD_ID CONTACT_RECORDED`.\n'
        '7. Record real replies; no reply after 14 days triggers a review/pivot rather than repeated spam.\n\n'
        '## Rules for the farm\n\n'
        '- GUILTY: do not execute the rejected action; develop another lawfully free proposal.\n'
        '- NOT GUILTY: produce local files, validate quality, prepare sales packet automatically.\n'
        '- If no store or human-authenticated outreach exists: **UNLAUNCHED**, never label it market failure.\n'
        '- No connected e-commerce APIs, card handling, outside spending, CAPTCHA bypass or autonomous message sending.\n'
        '- Suggested prices are not proven demand. Customer and revenue data is user-reported until independently linked to a service.\n'
    )
    atomic_text(out/'START_HERE_TWO_TRACKS.md',markdown)
    atomic_text(out/'SERVICE_PIVOT_REVIEW.md', '# Service strategy reviews — not automatic customer contact\n\n'+
        ('\n'.join(f'- Lead #{r["lead_id"]}: {r["decision"]}. Consider another approved service type, or new prospect with verified need.' for r in queue['service_pivot_review']) or 'No stalled client experiments currently reported.')+'\n')
    return {'folder':str(out),**queue['summary'],'errors':errors}
