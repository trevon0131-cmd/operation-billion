"""Seller Operations Manager: local listing/reply files, never external actions.

No seller account creation, publishing, outreach, payment or identity collection.
Only quality-checked, court-approved artifacts are eligible for preparations.
"""
import json
import re
from dataclasses import dataclass
from pathlib import Path
from .catalog import BY_KEY
from .quality import inspect
from .workshop import atomic_text

CHANNELS = ('ko-fi', 'gumroad', 'freelance')


def normalize_channel(channel, price):
    if channel == 'Freelance delivery':
        return 'freelance'
    if price > 0 and ('Ko-fi' in channel or 'Gumroad' in channel):
        return 'ko-fi'
    return 'research-only'


def safe_profile(home):
    """Read an optional public BRAND profile; never accept bank or identity fields."""
    p = Path(home) / 'config' / 'store_public_profile.json'
    if not p.is_file():
        return {'shop_name':'[Your shop name]', 'public_support_email':'[Support email]',
                'brand_voice':'clear and useful'}
    value = json.loads(p.read_text('utf-8'))
    allowed = {'shop_name','public_support_email','brand_voice'}
    if not isinstance(value,dict) or not set(value).issubset(allowed):
        raise ValueError('Store profile accepts public shop_name, public_support_email, brand_voice only; never passwords or payouts')
    result = {}
    for field in allowed:
        data = value.get(field,'')
        if not isinstance(data,str) or len(data)>120 or '\n' in data or '\r' in data:
            raise ValueError('Invalid public seller profile field: '+field)
        result[field]=data.strip()
    result.setdefault('shop_name','[Your shop name]')
    result.setdefault('public_support_email','[Support email]')
    result.setdefault('brand_voice','clear and useful')
    return result


def package_case(home, row):
    """Create storefront-ready *drafts* for an already adjudicated case.

    No requests, no credentials, no upload. Path containment prevents a corrupted
    case record from writing outside this project's output directory.
    """
    root = (Path(home)/'output').resolve()
    if row['verdict']!='NOT GUILTY' or not row['artifact_dir']:
        raise ValueError('Court-approved finished artifact required')
    target = Path(row['artifact_dir']).resolve()
    if not target.is_relative_to(root):
        raise ValueError('Product location is outside the controlled output directory')
    qc=inspect(target)
    if not qc['passed']:
        raise ValueError('Product must pass quality inspection before seller preparation')
    bot=BY_KEY.get(row['bot_key'])
    if bot is None:
        return {'status':'RESEARCH_ONLY','files':[]}
    meta = json.loads((target/'metadata.json').read_text('utf-8'))
    price_value = meta.get('suggested_price_usd',0)
    if not isinstance(price_value,(int,float)) or isinstance(price_value,bool) or price_value <= 0 or price_value > 100000:
        return {'status':'RESEARCH_ONLY','files':[]}
    channel=normalize_channel(str(meta.get('suggested_channel','')), price_value)
    if channel=='research-only':
        return {'status':'RESEARCH_ONLY','files':[]}
    profile=safe_profile(home)
    display_title = str(meta.get('subject',bot.subject))[:78]
    if not re.search('[A-Za-z0-9]',display_title):
        raise ValueError('Empty/unusable listing title')
    price=f'{price_value:.2f}'
    product_file=next((target/f for f in qc['checked_files'] if f.startswith('product.')),None)
    if product_file is None:
        raise ValueError('No printable/editable product file')
    data={
      'status':'WAITING_FOR_AUTHORIZED_SELLER_ACCOUNT',
      'court_case_id':int(row['id']), 'bot_key':bot.key,
      'preferred_channel':channel,
      'other_possible_channels':['gumroad'] if channel=='ko-fi' else [],
      'title_draft':display_title,
      'asking_price_suggestion_usd':price,
      'price_is_market_validated':False,
      'shop_name':profile['shop_name'],
      'product_file':product_file.name,
      'file_package':'PRODUCT_PACKAGE.zip',
      'publication_permitted':False,
      'external_requests_made':0,
      'verified_sales_count':0,
      'seller_account_connected':False,
      'requires_human_actions':['set up eligible seller account', 'complete platform/identity/payout verification',
           'review design rights', 'review listing accuracy and category restrictions',
           'accept actual fees and terms', 'approve first publication'],
      'note':'Generated listing drafts do NOT constitute listings or orders.'
    }
    title=display_title
    shop=profile['shop_name'] or '[Your shop name]'
    digital=channel=='ko-fi'
    body=(f'# {title} — UNPUBLISHED DRAFT\n\n'
          f'Store: {shop}\n\n'
          f'Proposed price: ${price} USD (NOT market validated, fees/taxes not included)\n\n'
          f'Intended channel: {channel}\n\n'
          f'Product: {bot.pitch}.\n\n'
          f'Files: {product_file.name}; packaged as PRODUCT_PACKAGE.zip.\n\n'
          'Please review and customize every claim and image. No customers or sales are implied.\n\n'
          'What buyers receive: only the files in PRODUCT_PACKAGE.zip; no physical shipment unless separately arranged.\n\n'
          'Review: originality, image rights, category rules, payout eligibility, actual fees, platform-accepted file formats.\n\n'
          'Publication and customer delivery: NOT CONFIGURED.\n')
    if not digital:
        body += '\nThis is a service proposal template, not a promise that any work has been completed for a client.\n'
    response=(f'# Customer message drafts — {title}\n\n'
              '**Question about what is included:** Thanks for your interest. The product is a digital file package; please check the listing before buying.\n\n'
              '**Request for custom changes:** Thanks for reaching out. Please describe the changes and timeline. I will confirm availability and pricing before agreeing.\n\n'
              '**Delivery problem:** Thanks for letting us know. Please use the platform order/help features. Do not share passwords, payment details, or verification codes.\n\n'
              'UNSENT DRAFTS ONLY. Confirm facts and account policy before replying.\n')
    atomic_text(target/'SELLER_OPERATIONS.json',json.dumps(data,indent=2))
    atomic_text(target/'CHANNEL_LISTING_DRAFT.md',body)
    atomic_text(target/'CUSTOMER_REPLY_DRAFTS.md',response)
    return {'status':data['status'],'files':['SELLER_OPERATIONS.json','CHANNEL_LISTING_DRAFT.md','CUSTOMER_REPLY_DRAFTS.md']}


def refresh_all(home, store, limit=100):
    """Regenerate only local preparations; no publication, sends or logins."""
    if not store.audit_valid():
        raise RuntimeError('Audit chain invalid; seller preparation stopped')
    completed=[];skipped=[]
    for row in store.cases(limit):
        if row['verdict']!='NOT GUILTY' or not row['artifact_dir']:
            continue
        try:
            result=package_case(home,row)
            if result['files']:
                completed.append(row['id'])
            else:
                skipped.append(row['id'])
        except (ValueError,OSError) as exc:
            skipped.append({'case_id':row['id'],'reason':str(exc)[:180]})
    return {'drafts_prepared':completed,'not_prepared':skipped,'external_publications':0,'accounts_connected':0}


def update_public_brand(home, name, support_email='', voice='clear and useful'):
    """Save only non-secret, public shop branding; never payments or credentials."""
    from email.utils import parseaddr
    for label, item in [('shop name',name),('support email',support_email),('brand voice',voice)]:
        if not isinstance(item,str) or len(item)>120 or any(ord(c)<32 for c in item):
            raise ValueError('Invalid public '+label)
    if len(name.strip())<2:
        raise ValueError('Public shop name required')
    if support_email and (parseaddr(support_email)[1]!=support_email or '@' not in support_email or '.' not in support_email.rsplit('@',1)[-1]):
        raise ValueError('Public support email invalid')
    if len(voice.strip())<3:raise ValueError('Short public brand voice required')
    target=Path(home)/'config'/'store_public_profile.json'
    if target.exists():
        safe_profile(home)  # Refuse to overwrite a malformed file containing possible secrets.
    atomic_text(target,json.dumps({'shop_name':name.strip(),'public_support_email':support_email.strip(),
                                   'brand_voice':voice.strip()},indent=2))
    return target
