"""Read-only, loopback-only status board. No publishing or commerce buttons."""
import html
import json
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from pathlib import Path
from .catalog import BOTS
from .experiments import recommendations
from .storage import Store

STYLE = '''
:root{color-scheme:dark}*{box-sizing:border-box}body{margin:0;background:#0b1220;color:#e7eefb;font:15px/1.6 system-ui,-apple-system,Segoe UI,sans-serif}a{color:#a4d6ff}header{padding:45px max(5%,calc((100% - 1220px)/2));background:radial-gradient(circle at 80% 20%,#173f51,#101e38 55%,#0b1220)}.eyebrow{letter-spacing:.2em;text-transform:uppercase;font-size:12px;color:#88ffca}h1{font-size:clamp(30px,5vw,60px);margin:8px 0;line-height:1.1}p{color:#b9c6d9}main{max-width:1220px;margin:auto;padding:28px 20px 70px}h2{margin-top:35px}section{margin:28px 0}.kpis,.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px}.tile,.panel{background:#141f31;border:1px solid #304159;border-radius:16px;padding:20px}.num{font-size:30px;font-weight:750}.sub{color:#93a8c5;font-size:12px;text-transform:uppercase;letter-spacing:.08em}.pill{display:inline-block;border:1px solid #52756b;padding:3px 9px;border-radius:999px;color:#aaf3c5;font-size:12px}.bad{color:#ffa5a5;border-color:#a85555}.mute{color:#9fafc6}.toolbar{display:flex;justify-content:space-between;flex-wrap:wrap;align-items:center;gap:16px}table{width:100%;border-collapse:collapse;min-width:680px}th{text-align:left;color:#a8b9d3;font-size:12px;text-transform:uppercase}td,th{padding:12px 10px;border-bottom:1px solid #29384f}tr:hover{background:#1a2a41}.tablewrap{overflow:auto}.small{font-size:12px;color:#9bacc5}pre{white-space:pre-wrap;word-break:break-word;background:#0c1523;padding:12px;border-radius:10px}.hash{font-family:monospace;word-break:break-all}strong{color:white}code{color:#a8ddf5}.footer{margin-top:45px;font-size:12px;color:#a5b5ca}button{background:#25465c;color:white;border:1px solid #426887;padding:9px 16px;border-radius:8px}
'''


def esc(obj): return html.escape(str(obj),quote=True)

def page(home:Path):
    st=Store(home); s=st.summary(); cases=st.cases(100); insight=recommendations(st)
    from .opportunity_lab import OpportunityLab, METHODS
    opp=OpportunityLab(home)
    overview=opp.overview()
    recent_opportunities=opp.rows(12)
    from .trend_engine import TrendEngine
    trend=TrendEngine(home)
    with trend.connect() as con:
        startup_kit_count=con.execute('SELECT COUNT(*) FROM kits').fetchone()[0]
        trend_signal_count=con.execute('SELECT COUNT(*) FROM signals').fetchone()[0]
    from .client_pipeline import ClientPipeline
    from .launch_workflow import collect_work
    client=ClientPipeline(home)
    dual=collect_work(home,st)
    leads=client.reviews()
    seller_ready=sum(1 for c in cases if c['verdict']=='NOT GUILTY' and c['artifact_dir'] and (Path(c['artifact_dir'])/'SELLER_OPERATIONS.json').is_file())
    from .creator_website_wing import Wing
    wing=Wing(home)
    expansion=wing.overview()
    creator_count=sum(x['kind'] in ('short','youtube') and x['verdict']=='NOT GUILTY' for x in expansion['drafts'])
    website_count=sum(x['kind']=='website' and x['verdict']=='NOT GUILTY' for x in expansion['drafts'])
    expansion_preview=''.join('<li>'+esc(x['kind'])+': '+esc(x['subject'])+' — LOCAL DRAFT</li>' for x in expansion['drafts'][:8]) or '<li>No samples yet; start the autopilot.</li>'
    from .free_tool_hub import FreeToolHub,free_doctor,TOOLS as FREE_TOOLS
    free_hub=FreeToolHub(home)
    free_status=free_doctor()
    free_findings=free_hub.findings(6)
    free_preview=''.join('<li>'+esc(x['name'])+': UNREVIEWED GITHUB CANDIDATE</li>' for x in free_findings) or '<li>No new GitHub candidates yet (run autopilot --live).</li>'
    free_audit=free_hub.audit_valid()
    kpis=[('Creator video drafts',creator_count),('Website demo drafts',website_count),('Startup playbooks created',startup_kit_count),('Trend and source signals',trend_signal_count),('Curated free local tools',len(FREE_TOOLS)),('Income research methods',len(METHODS)),('Research observations',overview['public_observations']),('Court-reviewed research plans',overview['experiment_plans']),('Retired research plans',overview['retired_plans']),('Digital drafts',len(dual['digital'])),('Service offers',len(dual['services'])),('User-supplied prospects',len(leads)),('Seller drafts (not live)',seller_ready),('Stores connected',0),('Specialist bots',len(BOTS)),('Court cases',s['cases']),('Allowed local drafts',s['allowed']),('Rejected',s['rejected']),('Court strategy repairs',s.get('revisions',0)),('Retired experiments',s['lifecycle']['retired']),('Business-technique pivots',s['lifecycle']['technique_pivots']),('Reported net','$'+format(s['manual_net_cents']/100,',.2f')),('Moonshot goal','$1,000,000,000')]
    stats=''.join(f'<div class="tile"><div class="sub">{esc(k)}</div><div class="num">{esc(v)}</div></div>' for k,v in kpis)
    case_rows=[]
    for c in cases:
        verdict='guilty' if c['verdict']=='GUILTY' else 'not guilty'
        color='bad' if c['verdict']=='GUILTY' else ''
        files=('<a href="/case/'+str(c['id'])+'">Inspect evidence</a>')
        case_rows.append(f'<tr><td>#{c["id"]}</td><td>{esc(c["bot_key"].replace("_"," ").title())}</td><td>{esc(c["title"])}</td><td><span class="pill {color}">{esc(verdict.upper())}</span></td><td>{esc(c["human_status"].replace("_"," "))}</td><td>{files}</td></tr>')
    status_path=home/'data'/'autopilot_status.json'
    runtime={}
    if status_path.is_file():
        try: runtime=json.loads(status_path.read_text(encoding='utf-8'))
        except (ValueError,OSError): pass
    runtime_line=('Last autonomous cycle (UTC): '+esc(runtime['last_cycle_utc']) if runtime.get('last_cycle_utc')
                  else 'Autonomous worker has not reported a cycle yet; run start_autopilot_windows.bat.')
    repair_rows=''.join(f'<li>Rejected case #{x["rejected_case_id"]} → approved alternative #{x["replacement_case_id"]}: {esc(x["lesson"])}</li>'
                        for x in st.revisions(10)) or '<li>No revised strategies have completed yet.</li>'
    lifeline=f"Experiments actually launched: {s['lifecycle']['launched']} · Retired: {s['lifecycle']['retired']} · Different-technique pivots: {s['lifecycle']['technique_pivots']} · Awaiting a different idea: {s['lifecycle']['awaiting_pivot']}"
    digital_preview=''.join(f'<li>Case #{x["case_id"]}: {esc(x["product"])} — {esc(x["decision"])} (NOT LIVE)</li>' for x in dual['digital'][:8]) or '<li>No approved digital drafts yet.</li>'
    service_preview=''.join(f'<li>Case #{x["case_id"]}: {esc(x["product"])} — not a client order</li>' for x in dual['services'][:8]) or '<li>No approved service drafts yet.</li>'
    client_preview=''.join(f'<li>{esc(x["business"])} — {esc(x["status"])} / {esc(x["decision"])}</li>' for x in leads[:10]) or '<li>No user-supplied business prospects yet.</li>'
    opportunity_preview=''.join(f'<li>#{o["id"]}: {esc(o["method_key"].replace("_"," ").title())} — {esc(o["status"])} ({esc(o["verdict"])})</li>' for o in recent_opportunities) or '<li>No research briefs yet.</li>'
    bot_cards=''.join(f'<div class="tile"><div class="sub">{esc(b.lane)}</div><strong>{esc(b.name)}</strong><p>{esc(b.pitch)}</p><div class="small">Proposed: {esc(b.channel)} · Starter price: ${b.suggested_price:.2f}</div></div>' for b in BOTS)
    insights=''.join(f'<p><strong>{esc(r["bot"].replace("_"," "))}:</strong> {esc(r["detail"])}</p>' for r in insight[:12]) or '<p>Start the farm to generate trials.</p>'
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="refresh" content="45"><title>Zero-Cost Bot Farm</title><style>{STYLE}</style></head><body><header><div class="eyebrow">Operation Billion · Research Mode</div><h1>Bot Farm Command Center</h1><p>{len(BOTS)} original product specialists plus {len(METHODS)} research method templates. Five-person jury, witnesses, prosecutor, defense and judge. Local generation only. <strong>No sales are implied.</strong></p><span class="pill">Autonomous local tasks · External publication unconnected</span></header><main><div class="kpis">{stats}</div><section><div class="panel"><strong>Autopilot and selling status</strong><p>{runtime_line}</p><p>The Seller Operations Manager prepares titles, descriptions, prices, packages and customer-reply drafts. Store accounts, payments and public listings are <strong>NOT CONNECTED</strong>. Nothing is marketed or sold automatically.</p><p>{esc(lifeline)}</p><p>14-day draft/live trial limits. An unlaunched draft is retired as UNLAUNCHED, not as a failed sale; trials need real observations before interpreting demand.</p></div></section><section class="toolbar"><div><h2>Live Court Docket</h2><p>Generated local cases. Refreshes every 45 seconds.</p></div><span class="pill {'bad' if not s['audit_valid'] else ''}">Audit chain: {'VALID' if s['audit_valid'] else 'INVALID / HALTED'}</span></section><div class="panel tablewrap"><table><thead><tr><th>Case</th><th>Specialist</th><th>Proposal</th><th>Verdict</th><th>Human gate</th><th>Evidence</th></tr></thead><tbody>{''.join(case_rows) or '<tr><td colspan="6">No cases yet. Run the setup command.</td></tr>'}</tbody></table></div><h2>Rejected ideas → revised alternatives</h2><div class="panel"><ul>{repair_rows}</ul></div><h2>Bounded Improvement Lab</h2><div class="panel"><p>Uses court lessons, original design variants, product format checks, and optional user-reported impressions and sales. It does not rewrite its own executable code or invent evidence of demand.</p>{insights}</div><h2>Two-track real-world validation</h2><div class="grid"><div class="panel"><strong>Lane 1 — Digital products</strong><p>Prepare Ko-fi drafts and manually publish after seller setup. Never claim sales without evidence.</p><ul>{digital_preview}</ul></div><div class="panel"><strong>Lane 2 — Local services</strong><p>Service offers, website assessment, proposals. No automatic outreach.</p><ul>{service_preview}</ul><strong>User-supplied prospects</strong><ul>{client_preview}</ul></div></div><div class="panel"><p>Export the launch queue with <code>py -3 -m botfarm launch-queue</code>. Output: <code>output/sales_workflow/START_HERE_TWO_TRACKS.md</code>. Client evidence ledger: {'VALID' if client.audit_valid() else 'INVALID — STOP'}.</p><p>Actual store publishing and payments require a connected supported seller account. The bot farm cannot create accounts, bypass verification or message prospects by itself.</p></div><h2>Website Opportunity Scout</h2><div class="panel"><p>Optional, user-selected public website review (not Google Maps scraping). Run <code>py -3 -m botfarm business-review https://example.com</code> for one legitimate business URL. Does not send email or gather personal contact details.</p></div><h2>Google Trends + GitHub Startup Laboratory</h2><div class="panel"><p>Official Google Trends RSS, GitHub and Hacker News public metadata inform court-approved startup kits. A trending search is <strong>not a confirmed sale</strong>. The farm generates original LOCAL samples when a tested builder exists.</p><p>Startup kits saved: {startup_kit_count}. Public signals saved: {trend_signal_count}. Review <code>output/startup_kits/</code> for startup instructions and sample files. Research audit: {'VALID' if trend.audit_valid() else 'INVALID / HALTED'}.</p><p>No search-engine results scraping, auto-signups, customer contact or store publishing.</p></div><h2>Opportunity Intelligence Hub · More Ways to Earn</h2><div class="panel"><p>Scouts use public GitHub repositories, Hacker News discussions and GitHub Blog RSS to explore {len(METHODS)} distinct zero-upfront business hypotheses. A popular repository or social post is NOT proof of buyers. The courtroom approves local briefs only.</p><p>Sources saved: {overview['public_observations']} · Research cases: {overview['experiment_plans']} · Retired: {overview['retired_plans']} · Evidence audit: {'VALID' if overview['audit_valid'] else 'INVALID — STOP'}</p><ul>{opportunity_preview}</ul><p>Run <code>py -3 -m botfarm opportunity-scan --live</code> or open <code>output/opportunity_research/RESEARCH_LIBRARY.md</code>. Autopilot also researches automatically.</p><p>New techniques include creator services, software utilities, ethical affiliate research, educational materials, language services, data cleanup, newsletters, games and more. Launch, payments, and outreach still require authorized connections.</p></div><h2>FREE-ONLY Tool Finder · Real software, no paid APIs</h2><div class="panel"><p>Curated $0-subscription local software entries: {len(FREE_TOOLS)}. Ready binaries / built-in: {len(free_status['ready_local'])}. Optional tools are NOT installed automatically; licenses for AI weights, voice models and media must be checked separately. No cloud API keys or billing required by this local core.</p><p>Tool-scout evidence audit: {'VALID' if free_audit else 'INVALID — STOP'}. All GitHub search results stay UNREVIEWED until permission, licenses, dependencies and commercial use are checked; no random GitHub code is run.</p><ul>{free_preview}</ul><p>Run <code>py -3 -m botfarm free-doctor</code>, <code>py -3 -m botfarm free-tools --need videos</code>, <code>py -3 -m botfarm free-plan websites &quot;independent tutor&quot; --build</code>, or <code>py -3 -m botfarm free-scout --live</code>. Read <code>docs/ALL_FREE_AI_OPTIONS.md</code>.</p></div><h2>New: Creator & Website Factories</h2><div class="panel"><p>Original short-form video slides (PNG + SRT), original landing-page website demos, and optional FFmpeg MP4 output. Script ideas may be based on fresh Google Trends matches, but are never assumed to have an audience or to sell. AI image/video models and seller accounts are not installed or connected.</p><p>Expansion audit: {'VALID' if expansion['audit_valid'] else 'INVALID / HALTED'} · Local creator samples: {creator_count} · Website demos: {website_count}. None published or emailed.</p><ul>{expansion_preview}</ul><p>Commands: <code>py -3 -m botfarm expansion-run</code>, <code>py -3 -m botfarm video-demo --format short</code>, <code>py -3 -m botfarm site-demo --niche "local cafe"</code> and <code>py -3 -m botfarm toolbox</code>.</p></div><h2>Specialist Roster</h2><div class="grid">{bot_cards}</div><div class="footer">Read-only local dashboard. No passwords or marketplace publishing integrations. Revenue figures above are user-reported and unverified; zero is shown until entered. Your PC must remain on for continuous research.</div></main></body></html>'''

def case_page(home:Path,cid:int):
    st=Store(home); row=st.case(cid)
    if row is None: return '<h1>Case not found</h1>'
    data=json.loads(row['case_json']); parts=[]
    parts.append(f'<h1>Case #{cid}: {esc(row["title"])}</h1><p><a href="/">Back to command center</a></p>')
    parts.append(f'<h2>Judge verdict: {esc(data["verdict"])}</h2><p>{esc(data["decision"])}</p>')
    for title,key in [('Prosecutor charges','prosecution'),('Defense arguments','defense'),('Judge reasoning','judge')]:
        parts.append(f'<h2>{title}</h2><ul>'+''.join('<li>'+esc(x)+'</li>' for x in data[key])+'</ul>')
    parts.append('<h2>Expert witnesses</h2><ul>'+''.join(f'<li><strong>{esc(k)}:</strong> {esc(v)}</li>' for k,v in data['witnesses'].items())+'</ul>')
    parts.append('<h2>Five jurors</h2><ul>'+''.join(f'<li>{esc(v["juror"])} — {esc(v["vote"])}</li>' for v in data['jury'])+'</ul>')
    parts.append('<h2>Evidence</h2><ul>'+''.join(f'<li>{esc(v["source"])}: {esc(v["detail"])}</li>' for v in data['evidence'])+'</ul>')
    parts.append(f'<h2>Artifact folder</h2><pre>{esc(row["artifact_dir"] or "Not produced")}</pre><p>Status: {esc(row["human_status"])}</p>')
    return f'<!doctype html><html><head><meta charset="utf-8"><title>Court case {cid}</title><style>{STYLE}main{{max-width:950px}}</style></head><body><main>{"".join(parts)}</main></body></html>'

def serve(home:Path, port=8765):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            loc=urlparse(self.path).path
            if loc=='/':
                raw=page(home);code=200
            elif loc.startswith('/case/') and loc[6:].isdigit():
                raw=case_page(home,int(loc[6:]));code=200
            else:raw='<h1>Not found</h1>';code=404
            body=raw.encode('utf-8')
            self.send_response(code)
            self.send_header('Content-Type','text/html; charset=utf-8')
            self.send_header('Content-Length',str(len(body)))
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Content-Security-Policy',"default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; frame-ancestors 'none'")
            self.end_headers();self.wfile.write(body)
        def log_message(self,fmt,*args):pass
    with ThreadingHTTPServer(('127.0.0.1',port),Handler) as server:
        print(f'Local command center: http://127.0.0.1:{port}/')
        print('Read-only. Press Ctrl+C to stop.')
        server.serve_forever()
