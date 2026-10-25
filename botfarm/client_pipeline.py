"""Human-owned lead pipeline; independent tamper-evident local ledger.

No Google Maps scraping, automatic outbound mail, personal contacts, or sales claims.
Lead status is always user-reported, not independently verified.
"""
import hashlib
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from .business_scout import validate_public_url, review_one
from .catalog import BY_KEY
from .quality import inspect
from .workshop import atomic_text

SCHEMA = '''
PRAGMA journal_mode=WAL;
PRAGMA busy_timeout=15000;
CREATE TABLE IF NOT EXISTS leads (
 id INTEGER PRIMARY KEY AUTOINCREMENT, business TEXT NOT NULL, website TEXT NOT NULL UNIQUE,
 created_at TEXT NOT NULL DEFAULT (datetime('now')),
 source TEXT NOT NULL DEFAULT 'user_supplied'
);
CREATE TABLE IF NOT EXISTS lead_steps (
 id INTEGER PRIMARY KEY AUTOINCREMENT, lead_id INTEGER NOT NULL REFERENCES leads(id),
 status TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT (datetime('now')),
 note TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS lead_audit (
 seq INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT NOT NULL, payload TEXT NOT NULL,
 prev_hash TEXT NOT NULL, digest TEXT NOT NULL
);
'''
STAGES = ('SCOUTED','REVIEWED','PACKET_READY','CONTACT_RECORDED','RESPONDED','CUSTOMER_REPORTED','DECLINED','DO_NOT_CONTACT')
TRANSITIONS = {
 'SCOUTED': {'REVIEWED','PACKET_READY','DO_NOT_CONTACT'},
 'REVIEWED': {'PACKET_READY','DO_NOT_CONTACT'},
 'PACKET_READY': {'CONTACT_RECORDED','DO_NOT_CONTACT'},
 'CONTACT_RECORDED': {'RESPONDED','DECLINED','DO_NOT_CONTACT'},
 'RESPONDED': {'CUSTOMER_REPORTED','DECLINED','DO_NOT_CONTACT'},
 'CUSTOMER_REPORTED': {'DO_NOT_CONTACT'},
 'DECLINED': {'DO_NOT_CONTACT'},
 'DO_NOT_CONTACT': set(),
}

class ClientPipeline:
    def __init__(self, home):
        self.home=Path(home)
        self.db=self.home/'data'/'client_pipeline.sqlite3'
        self.db.parent.mkdir(parents=True,exist_ok=True)
        with self.conn() as c: c.executescript(SCHEMA)

    @contextmanager
    def conn(self):
        connection=sqlite3.connect(self.db, timeout=15, isolation_level=None)
        connection.row_factory=sqlite3.Row
        try:
            connection.execute('PRAGMA foreign_keys=ON')
            connection.execute('PRAGMA busy_timeout=15000')
            yield connection
        finally: connection.close()

    @staticmethod
    def append(con, action, payload):
        raw=json.dumps(payload,sort_keys=True,separators=(',',':'),ensure_ascii=True)
        last=con.execute('SELECT digest FROM lead_audit ORDER BY seq DESC LIMIT 1').fetchone()
        prev=last['digest'] if last else 'GENESIS'
        digest=hashlib.sha256((prev+'\n'+action+'\n'+raw).encode()).hexdigest()
        con.execute('INSERT INTO lead_audit(action,payload,prev_hash,digest) VALUES (?,?,?,?)',(action,raw,prev,digest))

    def audit_valid(self):
        with self.conn() as c:
            prev='GENESIS';lead_ids=set();step_ids=set()
            for a in c.execute('SELECT * FROM lead_audit ORDER BY seq'):
                if a['prev_hash']!=prev or hashlib.sha256((prev+'\n'+a['action']+'\n'+a['payload']).encode()).hexdigest()!=a['digest']:
                    return False
                try:
                    p=json.loads(a['payload'])
                    if a['action']=='lead_added':
                        lead=c.execute('SELECT * FROM leads WHERE id=?',(p['lead_id'],)).fetchone()
                        if not lead or lead['business']!=p['business'] or lead['website']!=p['website'] or lead['created_at']!=p['created_at'] or lead['source']!='user_supplied': return False
                        lead_ids.add(p['lead_id'])
                    elif a['action']=='lead_step':
                        step=c.execute('SELECT * FROM lead_steps WHERE id=?',(p['step_id'],)).fetchone()
                        if not step or any(step[k]!=p[k] for k in ('lead_id','status','note','created_at')): return False
                        step_ids.add(p['step_id'])
                    else: return False
                except (KeyError,TypeError,ValueError):return False
                prev=a['digest']
            return lead_ids=={r[0] for r in c.execute('SELECT id FROM leads')} and step_ids=={r[0] for r in c.execute('SELECT id FROM lead_steps')}

    def add(self, business, website):
        if not isinstance(business,str) or not (2<=len(business.strip())<=120) or any(x in business for x in ('\r','\n')):
            raise ValueError('Provide a short public business name')
        validate_public_url(website)
        if not self.audit_valid():raise RuntimeError('Client lead audit invalid; stopped')
        with self.conn() as c:
            c.execute('BEGIN IMMEDIATE')
            row=c.execute('SELECT id FROM leads WHERE website=?',(website,)).fetchone()
            if row:c.execute('COMMIT');return row['id']
            lead_id=c.execute('INSERT INTO leads(business,website) VALUES (?,?)',(business.strip(),website)).lastrowid
            step_id=c.execute('INSERT INTO lead_steps(lead_id,status) VALUES (?,?)',(lead_id,'SCOUTED')).lastrowid
            created=c.execute('SELECT created_at FROM leads WHERE id=?',(lead_id,)).fetchone()['created_at']
            step_created=c.execute('SELECT created_at FROM lead_steps WHERE id=?',(step_id,)).fetchone()['created_at']
            self.append(c,'lead_added',{'lead_id':lead_id,'business':business.strip(),'website':website,'created_at':created})
            self.append(c,'lead_step',{'step_id':step_id,'lead_id':lead_id,'status':'SCOUTED','note':'','created_at':step_created})
            c.execute('COMMIT');return lead_id

    def list(self):
        with self.conn() as c:
            rows=c.execute('''SELECT l.*,s.status,s.created_at AS status_at,s.note
                    FROM leads l JOIN lead_steps s ON s.id=(SELECT id FROM lead_steps WHERE lead_id=l.id ORDER BY id DESC LIMIT 1)
                    ORDER BY l.id''').fetchall()
            return [dict(r) for r in rows]

    def get(self, lead_id):
        return next((x for x in self.list() if x['id']==lead_id),None)

    def stage(self, lead_id, new_status, note=''):
        new_status=new_status.upper()
        if new_status not in STAGES:raise ValueError('Unknown status')
        if not isinstance(note,str) or len(note)>400 or '\n' in note or '\r' in note:raise ValueError('Short single-line note only')
        if not self.audit_valid():raise RuntimeError('Client lead audit invalid; stopped')
        with self.conn() as c:
            c.execute('BEGIN IMMEDIATE')
            prior=c.execute('SELECT status FROM lead_steps WHERE lead_id=? ORDER BY id DESC LIMIT 1',(lead_id,)).fetchone()
            if not prior or new_status not in TRANSITIONS[prior['status']]:
                c.execute('ROLLBACK');raise ValueError('Invalid lead stage transition')
            sid=c.execute('INSERT INTO lead_steps(lead_id,status,note) VALUES (?,?,?)',(lead_id,new_status,note)).lastrowid
            stamp=c.execute('SELECT created_at FROM lead_steps WHERE id=?',(sid,)).fetchone()['created_at']
            self.append(c,'lead_step',{'step_id':sid,'lead_id':lead_id,'status':new_status,'note':note,'created_at':stamp})
            c.execute('COMMIT')
        return new_status

    def reviews(self, now=None):
        now=now or datetime.now(timezone.utc)
        rows=self.list();result=[]
        for item in rows:
            status=item['status']
            when=datetime.fromisoformat(item['status_at'].replace(' ','T')).replace(tzinfo=timezone.utc)
            days=max(0.,(now-when).total_seconds()/86400)
            if status=='CONTACT_RECORDED' and days>=14: advice='NO_REPORTED_RESPONSE_14D — consider retiring this approach; do not spam repeat messages'
            elif status in ('SCOUTED','REVIEWED','PACKET_READY') and days>=14: advice='UNLAUNCHED_14D — research or contact never completed; not proof of rejection'
            elif status=='DO_NOT_CONTACT': advice='SUPPRESSED — never contact automatically'
            elif status in ('CUSTOMER_REPORTED','DECLINED'): advice='CLOSED — user-reported status'
            else: advice='IN_PROGRESS — await evidence'
            result.append({'lead_id':item['id'],'business':item['business'],'status':status,'days_in_stage':round(days,1),'decision':advice})
        return result

    def pack(self, lead_id, store, case_id, with_review=False, reviewer=review_one):
        if not self.audit_valid() or not store.audit_valid():raise RuntimeError('One of the audit ledgers is invalid')
        lead=self.get(lead_id)
        if lead is None or lead['status']=='DO_NOT_CONTACT':raise ValueError('Lead missing or suppressed')
        row=store.case(case_id)
        if not row or row['verdict']!='NOT GUILTY' or not row['artifact_dir']:
            raise ValueError('Approved completed court case required')
        bot=BY_KEY.get(row['bot_key'])
        if not bot or bot.channel!='Freelance delivery':raise ValueError('Choose an approved local service case, not a sticker or other product')
        root=(self.home/'output').resolve()
        product=Path(row['artifact_dir']).resolve()
        if not product.is_relative_to(root) or not inspect(product)['passed']:
            raise ValueError('Service template must be quality checked inside the project')
        actual={}
        if with_review:
            actual=reviewer(self.home,lead['website'])['report']
        folder=self.home/'output'/'client_packets'/f'lead_{lead_id:04d}_case_{case_id:04d}'
        folder.mkdir(parents=True,exist_ok=True)
        findings=actual.get('potential_improvements',[])
        bullets=('\n'.join('- Potential HTML-only observation: '+s for s in findings) if findings else
                 '- No website findings have been verified; request permission for a full audit before making claims.')
        proposal=(f'# BUSINESS SERVICE PROPOSAL — UNSENT DRAFT\n\nBusiness: {lead["business"]}\nWebsite: {lead["website"]}\n'
                  f'Court-approved service template: {bot.name} (case #{case_id})\n\n'
                  f'Service option: {bot.pitch}\nProposed STARTING price: ${bot.suggested_price:.2f} (estimate, not agreed).\n\n'
                  f'## Items to discuss or verify\n{bullets}\n\n'
                  '## Scope before accepting work\nConfirm requirements, assets, timeline, exclusions, revisions, payment terms, and permission to modify any website.\n'
                  'No claims of a full performance test, working relationship, completed paid work or client interest.\n')
        message=(f'# OUTREACH DRAFT — DO NOT SEND AUTOMATICALLY\n\n'
                 f'Hello {lead["business"]} team,\n\n'
                 f'I offer {bot.pitch.lower()} and prepared a preliminary service idea based on your public website. '
                 'Would you be interested in discussing whether it could be useful? '
                 'I can share a clearly scoped proposal if so.\n\n'
                 'Thank you.\n\n'
                 'Only send personally to appropriate public business channels if permitted; comply with opt-out requests and applicable marketing rules. '
                 'Do not imply these observations were verified beyond the methods described.\n')
        atomic_text(folder/'PROPOSAL_DRAFT.md',proposal)
        atomic_text(folder/'OUTREACH_DRAFT.md',message)
        atomic_text(folder/'EVIDENCE_AND_NEXT_STEPS.json',json.dumps({'lead_id':lead_id,'case_id':case_id,
          'lead_origin':'user_supplied','status':'UNSENT','offer_price_is_estimate':True,
          'site_review_performed':bool(with_review),'observations':findings,'sales_verified':False,
          'next_actions':['Review service proposal', 'Verify business information and rights',
                          'Personally approve and send outreach if lawful','Record contact or response truthfully']},indent=2))
        if lead['status']=='SCOUTED' and with_review: self.stage(lead_id,'REVIEWED','Website reviewed with heuristic HTML inspection; no contact')
        if self.get(lead_id)['status'] in ('SCOUTED','REVIEWED'): self.stage(lead_id,'PACKET_READY','Proposal prepared; not sent; website inspection='+str(with_review))
        return {'folder':str(folder),'lead_id':lead_id,'case_id':case_id,'contact_sent':False,
                'site_review_performed':bool(with_review)}
