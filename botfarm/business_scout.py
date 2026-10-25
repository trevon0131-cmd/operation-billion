"""Opt-in, non-Google business website review.

Only user-selected public company website, no Maps scraping or personal contact
harvesting. Respect robots.txt; no login, redirects, CAPTCHA circumvention or
outreach. Reports are heuristic drafts, not a Lighthouse audit.
"""
import ipaddress
import json
import re
import socket
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from .workshop import atomic_text

USER_AGENT='OperationBillionResearch/0.3 (polite website evaluation; no contact harvesting)'

class PageHints(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_title=False;self.title='';self.meta_description='';self.viewport=False;self.h1=0;self.image_missing_alt=0
    def handle_starttag(self,tag,attrs):
        props=dict(attrs)
        if tag=='title':self.in_title=True
        if tag=='h1':self.h1+=1
        if tag=='meta' and props.get('name','').lower()=='description':self.meta_description=props.get('content','')[:300]
        if tag=='meta' and props.get('name','').lower()=='viewport':self.viewport=True
        if tag=='img' and not props.get('alt','').strip():self.image_missing_alt+=1
    def handle_endtag(self,tag):
        if tag=='title':self.in_title=False
    def handle_data(self,data):
        if self.in_title:self.title=(self.title+data)[:200]


def validate_public_url(value):
    parsed=urllib.parse.urlsplit(value)
    if parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password or parsed.port not in (None,443):
        raise ValueError('Only public HTTPS websites on port 443, without credentials, are permitted')
    if parsed.hostname in ('localhost',) or parsed.hostname.endswith(('.local','.internal','.test')):
        raise ValueError('Local/intranet addresses are not public business sites')
    try:
        ipaddress.ip_address(parsed.hostname)
        raise ValueError('Use a public domain name, not an IP address')
    except ValueError as exc:
        if str(exc).startswith('Use a public'): raise
    if parsed.fragment or len(value)>700:
        raise ValueError('URL fragment or excessive length not permitted')
    return parsed


def check_host_public(host):
    answers=socket.getaddrinfo(host,443,proto=socket.IPPROTO_TCP)
    addresses={ipaddress.ip_address(answer[4][0]) for answer in answers}
    if not addresses or not all(ip.is_global for ip in addresses):
        raise ValueError('Hostname resolves to a non-public address')


class NoRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        raise ValueError('Redirects are not followed automatically; provide the final business URL explicitly')

OPENER=urllib.request.build_opener(NoRedirects())


def fetch_site(url):
    parsed=validate_public_url(url)
    check_host_public(parsed.hostname)
    robots_url=f'https://{parsed.hostname}/robots.txt'
    from urllib.robotparser import RobotFileParser
    bot=RobotFileParser();bot.set_url(robots_url)
    request=urllib.request.Request(robots_url,headers={'User-Agent':USER_AGENT})
    try:
        with OPENER.open(request,timeout=8) as response:
            robots=response.read(200_000).decode('utf-8','replace')
        bot.parse(robots.splitlines())
    except urllib.error.HTTPError as exc:
        if exc.code not in (404,410):
            raise ValueError('Could not confirm robots permission') from exc
        bot.parse([])
    except (OSError,ValueError) as exc:
        raise ValueError('Robots check unavailable; skipping site') from exc
    if not bot.can_fetch(USER_AGENT,url):
        raise ValueError('robots.txt disallows this page')
    check_host_public(parsed.hostname)
    req=urllib.request.Request(url,headers={'User-Agent':USER_AGENT,'Accept':'text/html'})
    with OPENER.open(req,timeout=10) as response:
        typ=response.headers.get('Content-Type','').lower()
        if 'text/html' not in typ:
            raise ValueError('Site is not an HTML webpage')
        raw=response.read(524_289)
        if len(raw)>524_288:
            raise ValueError('Page exceeds the safe size limit')
    return raw.decode('utf-8','replace')


def analyze_html(url, markup):
    validate_public_url(url)
    if not isinstance(markup,str) or len(markup)>550_000:
        raise ValueError('HTML input must be short text')
    p=PageHints();p.feed(markup)
    items=[]
    if not p.title.strip():items.append('No page title detected in the retrieved HTML')
    if not p.meta_description.strip():items.append('No meta description detected in the retrieved HTML')
    if not p.viewport:items.append('No mobile viewport meta tag detected in the retrieved HTML')
    if not p.h1:items.append('No H1 heading detected in the retrieved HTML')
    if p.image_missing_alt:items.append(f'{p.image_missing_alt} image element(s) missing descriptive alt text')
    return {'website':url,'method':'HTML-only heuristic (NOT Google Maps or Lighthouse)',
            'title':p.title.strip(),'potential_improvements':items,
            'limitations':'Dynamic content, actual accessibility, speed, SEO impact and client needs are unverified.',
            'no_outreach_sent':True,'no_personal_contact_data_collected':True}


def review_one(home,url,fetcher=fetch_site):
    markup=fetcher(url)
    report=analyze_html(url,markup)
    import hashlib
    ident=hashlib.sha256(url.encode()).hexdigest()[:12]
    dest=Path(home)/'output'/'business_scout'/ident
    dest.mkdir(parents=True,exist_ok=True)
    atomic_text(dest/'BUSINESS_WEBSITE_REVIEW_DRAFT.json',json.dumps(report,indent=2))
    brief=('# Website improvement opportunity — UNVERIFIED DRAFT\n\n'
       f'Website reviewed: {url}\n\n'
       'Potential items to verify manually:\n'+ ''.join('- '+x+'\n' for x in report['potential_improvements'])+
       '\nNot a client, no outreach sent, no sale, no verified performance metrics.\n'
       'Do not claim a full Lighthouse audit; use a proper full audit before offering services.\n')
    atomic_text(dest/'REPORT_DRAFT.md',brief)
    return {'report_folder':str(dest),'report':report}
