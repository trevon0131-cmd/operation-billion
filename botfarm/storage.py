"""SQLite evidence room: durable transactions, duplicate suppression, hash-chain audit."""
import hashlib
from contextlib import contextmanager
import json
import sqlite3
import time
from pathlib import Path

SCHEMA = '''
PRAGMA journal_mode=WAL;
PRAGMA busy_timeout=15000;
CREATE TABLE IF NOT EXISTS cases (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 fingerprint TEXT NOT NULL UNIQUE,
 bot_key TEXT NOT NULL,
 title TEXT NOT NULL,
 variant INTEGER NOT NULL,
 created_at TEXT NOT NULL DEFAULT (datetime('now')),
 verdict TEXT NOT NULL,
 decision TEXT NOT NULL,
 case_json TEXT NOT NULL,
 artifact_dir TEXT NOT NULL DEFAULT '',
 human_status TEXT NOT NULL DEFAULT 'not_submitted'
);
CREATE INDEX IF NOT EXISTS idx_cases_bot ON cases(bot_key);
CREATE TABLE IF NOT EXISTS events (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 case_id INTEGER NOT NULL REFERENCES cases(id),
 created_at TEXT NOT NULL DEFAULT (datetime('now')),
 kind TEXT NOT NULL CHECK(kind IN ('view','click','sale','refund')),
 quantity INTEGER NOT NULL DEFAULT 1 CHECK(quantity > 0),
 gross_cents INTEGER NOT NULL DEFAULT 0 CHECK(gross_cents >= 0),
 fee_cents INTEGER NOT NULL DEFAULT 0 CHECK(fee_cents >= 0),
 source TEXT NOT NULL CHECK(source IN ('user_reported')),
 note TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS revisions (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 rejected_case_id INTEGER NOT NULL UNIQUE REFERENCES cases(id),
 replacement_case_id INTEGER NOT NULL UNIQUE REFERENCES cases(id),
 lesson TEXT NOT NULL,
 created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS trial_launches (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 case_id INTEGER NOT NULL UNIQUE REFERENCES cases(id),
 url TEXT NOT NULL,
 created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS trial_retirements (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 case_id INTEGER NOT NULL UNIQUE REFERENCES cases(id),
 classification TEXT NOT NULL,
 reason TEXT NOT NULL,
 created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS trial_pivots (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 retired_case_id INTEGER NOT NULL UNIQUE REFERENCES cases(id),
 new_case_id INTEGER NOT NULL UNIQUE REFERENCES cases(id),
 reason TEXT NOT NULL,
 created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS audit (
 seq INTEGER PRIMARY KEY AUTOINCREMENT,
 created_at TEXT NOT NULL DEFAULT (datetime('now')),
 action TEXT NOT NULL,
 payload TEXT NOT NULL,
 prev_hash TEXT NOT NULL,
 digest TEXT NOT NULL
);
'''

class Store:
    def __init__(self, home: Path):
        db = home / 'data' / 'farm.sqlite3'
        db.parent.mkdir(parents=True, exist_ok=True)
        self.db = db
        with self.connect() as c:
            c.executescript(SCHEMA)

    @contextmanager
    def connect(self):
        con = sqlite3.connect(self.db, timeout=15, isolation_level=None)
        try:
            con.row_factory = sqlite3.Row
            con.execute('PRAGMA foreign_keys=ON')
            con.execute('PRAGMA busy_timeout=15000')
            yield con
        finally:
            con.close()

    @staticmethod
    def _audit(con, action, payload):
        payload_json = json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=True)
        last = con.execute('SELECT digest FROM audit ORDER BY seq DESC LIMIT 1').fetchone()
        prev = last['digest'] if last else 'GENESIS'
        digest = hashlib.sha256((prev + '\n' + action + '\n' + payload_json).encode()).hexdigest()
        con.execute('INSERT INTO audit (action,payload,prev_hash,digest) VALUES (?,?,?,?)',
                    (action,payload_json,prev,digest))

    def add_case(self, fingerprint, bot_key, title, variant, judgment, artifact_dir='', daily_cap=32):
        with self.connect() as con:
            con.execute('BEGIN IMMEDIATE')
            existing=con.execute('SELECT id FROM cases WHERE fingerprint=?',(fingerprint,)).fetchone()
            if existing:
                con.execute('COMMIT')
                return None
            today=con.execute("SELECT COUNT(*) AS n FROM cases WHERE date(created_at)=date('now')").fetchone()['n']
            if today >= daily_cap:
                con.execute('ROLLBACK')
                raise ValueError('Daily court-case cap reached')
            cur = con.execute('''INSERT OR IGNORE INTO cases
              (fingerprint,bot_key,title,variant,verdict,decision,case_json,artifact_dir)
              VALUES(?,?,?,?,?,?,?,?)''',
              (fingerprint,bot_key,title,variant,judgment['verdict'],
               judgment['decision'],json.dumps(judgment,sort_keys=True),artifact_dir))
            if cur.rowcount == 0:
                con.execute('COMMIT')
                return None
            case_id = cur.lastrowid
            self._audit(con, 'case_opened', {'case_id':case_id,'fingerprint':fingerprint,
                                            'verdict':judgment['verdict'],
                                            'judgment_sha256':hashlib.sha256(json.dumps(judgment,sort_keys=True).encode()).hexdigest()})
            con.execute('COMMIT')
            return case_id

    def update_artifact(self, case_id, artifact_dir):
        with self.connect() as con:
            con.execute('BEGIN IMMEDIATE')
            row = con.execute('SELECT verdict,artifact_dir FROM cases WHERE id=?',(case_id,)).fetchone()
            if not row or row['verdict']!='NOT GUILTY' or row['artifact_dir']:
                con.execute('ROLLBACK')
                return False
            con.execute('UPDATE cases SET artifact_dir=? WHERE id=?',(str(artifact_dir),case_id))
            self._audit(con, 'artifact_attached', {'case_id':case_id,'path':str(artifact_dir)})
            con.execute('COMMIT')
            return True

    def unfinished_artifacts(self):
        with self.connect() as con:
            return [dict(r) for r in con.execute("SELECT * FROM cases WHERE verdict='NOT GUILTY' AND artifact_dir='' ORDER BY id")]

    def case(self, cid):
        with self.connect() as con:
            r=con.execute('SELECT * FROM cases WHERE id=?',(cid,)).fetchone()
            return dict(r) if r else None

    def cases(self, limit=100):
        with self.connect() as con:
            return [dict(r) for r in con.execute('SELECT * FROM cases ORDER BY id DESC LIMIT ?', (limit,))]

    def bot_case_counts(self):
        with self.connect() as con:
            rows = con.execute('SELECT bot_key, COUNT(*) AS n FROM cases GROUP BY bot_key').fetchall()
            return {r['bot_key']:r['n'] for r in rows}

    def daily_count(self):
        with self.connect() as con:
            r=con.execute("SELECT COUNT(*) AS n FROM cases WHERE date(created_at)=date('now')").fetchone()
            return r['n']

    def audit_valid(self):
        """Check the chain AND the referenced durable rows for accidental changes."""
        with self.connect() as con:
            prev='GENESIS'
            seen_cases=set()
            seen_events=set()
            seen_revisions=set()
            seen_launches=set()
            seen_retirements=set()
            seen_pivots=set()
            for r in con.execute('SELECT action,payload,prev_hash,digest FROM audit ORDER BY seq'):
                if r['prev_hash'] != prev:
                    return False
                digest=hashlib.sha256((prev+'\n'+r['action']+'\n'+r['payload']).encode()).hexdigest()
                if digest!=r['digest']:
                    return False
                try:
                    payload=json.loads(r['payload'])
                    if r['action']=='case_opened':
                        cid=payload['case_id']
                        row=con.execute('SELECT * FROM cases WHERE id=?',(cid,)).fetchone()
                        if not row or row['fingerprint']!=payload['fingerprint'] or row['verdict']!=payload['verdict']:
                            return False
                        if hashlib.sha256(row['case_json'].encode()).hexdigest()!=payload['judgment_sha256']:
                            return False
                        seen_cases.add(cid)
                    elif r['action']=='artifact_attached':
                        row=con.execute('SELECT artifact_dir FROM cases WHERE id=?',(payload['case_id'],)).fetchone()
                        if not row or row['artifact_dir']!=payload['path']:
                            return False
                    elif r['action']=='user_reported_event':
                        eid=payload['event_id']
                        row=con.execute('SELECT * FROM events WHERE id=?',(eid,)).fetchone()
                        if not row or any(row[field]!=payload[field] for field in ('case_id','kind','quantity','gross_cents','fee_cents')):
                            return False
                        seen_events.add(eid)
                    elif r['action']=='strategy_revision':
                        rid=payload['revision_id']
                        row=con.execute('SELECT * FROM revisions WHERE id=?',(rid,)).fetchone()
                        if not row or any(row[field]!=payload[field] for field in
                                          ('rejected_case_id','replacement_case_id','lesson')):
                            return False
                        seen_revisions.add(rid)
                    elif r['action']=='trial_launched':
                        rid=payload['launch_id']
                        row=con.execute('SELECT * FROM trial_launches WHERE id=?',(rid,)).fetchone()
                        if not row or any(row[k]!=payload[k] for k in ('case_id','url')): return False
                        seen_launches.add(rid)
                    elif r['action']=='trial_retired':
                        rid=payload['retirement_id']
                        row=con.execute('SELECT * FROM trial_retirements WHERE id=?',(rid,)).fetchone()
                        if not row or any(row[k]!=payload[k] for k in ('case_id','classification','reason')): return False
                        seen_retirements.add(rid)
                    elif r['action']=='trial_pivoted':
                        rid=payload['pivot_id']
                        row=con.execute('SELECT * FROM trial_pivots WHERE id=?',(rid,)).fetchone()
                        if not row or any(row[k]!=payload[k] for k in ('retired_case_id','new_case_id','reason')): return False
                        seen_pivots.add(rid)
                    elif r['action']=='human_acknowledged_manual_publish':
                        row=con.execute('SELECT human_status FROM cases WHERE id=?',(payload['case_id'],)).fetchone()
                        if not row or row['human_status']!='ready_for_manual_publication':
                            return False
                    else:
                        return False
                except (ValueError, KeyError, TypeError):
                    return False
                prev=digest
            actual_cases={r['id'] for r in con.execute('SELECT id FROM cases')}
            actual_events={r['id'] for r in con.execute('SELECT id FROM events')}
            actual_revisions={r['id'] for r in con.execute('SELECT id FROM revisions')}
            actual_launches={r['id'] for r in con.execute('SELECT id FROM trial_launches')}
            actual_retirements={r['id'] for r in con.execute('SELECT id FROM trial_retirements')}
            actual_pivots={r['id'] for r in con.execute('SELECT id FROM trial_pivots')}
            return (seen_cases==actual_cases and seen_events==actual_events and
                    seen_revisions==actual_revisions and seen_launches==actual_launches and
                    seen_retirements==actual_retirements and seen_pivots==actual_pivots)

    def record_revision(self, rejected_case_id, replacement_case_id, lesson):
        if not lesson or len(lesson) > 500:
            raise ValueError('A concise improvement reason is required')
        with self.connect() as con:
            con.execute('BEGIN IMMEDIATE')
            old=con.execute('SELECT verdict FROM cases WHERE id=?',(rejected_case_id,)).fetchone()
            new=con.execute('SELECT verdict FROM cases WHERE id=?',(replacement_case_id,)).fetchone()
            if not old or old['verdict']!='GUILTY' or not new or new['verdict']!='NOT GUILTY':
                con.execute('ROLLBACK')
                raise ValueError('A rejected trial and distinct allowed replacement are required')
            existing=con.execute('SELECT id FROM revisions WHERE rejected_case_id=?', (rejected_case_id,)).fetchone()
            if existing:
                con.execute('COMMIT')
                return False
            cur=con.execute('INSERT INTO revisions (rejected_case_id,replacement_case_id,lesson) VALUES (?,?,?)',
                            (rejected_case_id,replacement_case_id,lesson))
            self._audit(con,'strategy_revision',{'revision_id':cur.lastrowid,
                 'rejected_case_id':rejected_case_id,'replacement_case_id':replacement_case_id,'lesson':lesson})
            con.execute('COMMIT')
            return True

    def pending_rejections(self, limit=100):
        """Find rejected ideas whose court-approved alternative was not recorded."""
        sql = ("SELECT c.* FROM cases c LEFT JOIN revisions r ON r.rejected_case_id=c.id "
               "WHERE c.verdict='GUILTY' AND r.id IS NULL ORDER BY c.id LIMIT ?")
        with self.connect() as con:
            return [dict(r) for r in con.execute(sql,(limit,))]

    def case_by_fingerprint(self, fingerprint):
        with self.connect() as con:
            row=con.execute('SELECT * FROM cases WHERE fingerprint=?',(fingerprint,)).fetchone()
            return dict(row) if row else None

    def revisions(self, limit=100):
        with self.connect() as con:
            return [dict(r) for r in con.execute('SELECT * FROM revisions ORDER BY id DESC LIMIT ?', (limit,))]

    def mark_trial_launched(self, case_id, url):
        """Record a public launch; does not publish or independently verify it."""
        from urllib.parse import urlsplit
        if not isinstance(url,str) or len(url)>1000:
            raise ValueError('Public HTTPS URL required')
        parsed=urlsplit(url)
        if parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError('Public HTTPS listing URL without credentials required')
        with self.connect() as con:
            con.execute('BEGIN IMMEDIATE')
            row=con.execute('SELECT verdict,artifact_dir FROM cases WHERE id=?',(case_id,)).fetchone()
            if not row or row['verdict']!='NOT GUILTY' or not row['artifact_dir']:
                raise ValueError('A completed NOT GUILTY case is required')
            if con.execute('SELECT 1 FROM trial_retirements WHERE case_id=?',(case_id,)).fetchone():
                raise ValueError('Cannot launch a retired case')
            if con.execute('SELECT 1 FROM trial_launches WHERE case_id=?',(case_id,)).fetchone():
                con.execute('COMMIT');return False
            cur=con.execute('INSERT INTO trial_launches(case_id,url) VALUES (?,?)',(case_id,url))
            self._audit(con,'trial_launched',{'launch_id':cur.lastrowid,'case_id':case_id,'url':url})
            con.execute('COMMIT');return True

    def trial_rows(self):
        """Launch clock begins when external launch is confirmed; otherwise draft clock."""
        by_id={r['id']:dict(r) for r in self.metrics()}
        with self.connect() as con:
            sql="""SELECT c.id,c.bot_key,c.created_at,c.verdict,c.artifact_dir,
              l.created_at AS launched_at,l.url AS listing_url,
              r.created_at AS retired_at,r.classification AS retirement_class
              FROM cases c LEFT JOIN trial_launches l ON l.case_id=c.id
              LEFT JOIN trial_retirements r ON r.case_id=c.id
              WHERE c.verdict='NOT GUILTY' AND c.artifact_dir!='' ORDER BY c.id"""
            rows=con.execute(sql).fetchall()
        return [{**dict(row), **{k:v for k,v in by_id.get(row['id'],{}).items()
                                      if k in ('views','clicks','sales','gross_cents','fee_cents')}} for row in rows]

    def retire_trial(self, case_id, classification, reason):
        if classification not in ('UNLAUNCHED','INCONCLUSIVE','LOW_RETURN','LOW_ENGAGEMENT'):
            raise ValueError('Invalid retirement category')
        if not isinstance(reason,str) or not reason or len(reason)>500:
            raise ValueError('Short retirement reason required')
        with self.connect() as con:
            con.execute('BEGIN IMMEDIATE')
            row=con.execute('SELECT verdict,artifact_dir FROM cases WHERE id=?',(case_id,)).fetchone()
            if not row or row['verdict']!='NOT GUILTY' or not row['artifact_dir']:
                raise ValueError('Cannot retire an incomplete or rejected case')
            if con.execute('SELECT id FROM trial_retirements WHERE case_id=?',(case_id,)).fetchone():
                con.execute('COMMIT');return False
            cur=con.execute('INSERT INTO trial_retirements(case_id,classification,reason) VALUES (?,?,?)',
                            (case_id,classification,reason))
            self._audit(con,'trial_retired',{'retirement_id':cur.lastrowid,
                'case_id':case_id,'classification':classification,'reason':reason})
            con.execute('COMMIT');return True

    def pending_trial_pivots(self):
        with self.connect() as con:
            return [dict(r) for r in con.execute("""SELECT r.case_id AS old_case_id,c.bot_key,r.classification
                FROM trial_retirements r JOIN cases c ON c.id=r.case_id
                LEFT JOIN trial_pivots p ON p.retired_case_id=r.case_id
                WHERE p.id IS NULL ORDER BY r.id""")]

    def retired_bot_keys(self):
        with self.connect() as con:
            return {r['bot_key'] for r in con.execute("""SELECT DISTINCT c.bot_key FROM trial_retirements r
                JOIN cases c ON r.case_id=c.id""")}

    def record_trial_pivot(self, old_case_id, new_case_id, reason):
        if not reason or len(reason)>500:
            raise ValueError('Short strategy change reason required')
        with self.connect() as con:
            con.execute('BEGIN IMMEDIATE')
            old=con.execute('SELECT c.bot_key FROM cases c JOIN trial_retirements r ON r.case_id=c.id WHERE c.id=?',
                            (old_case_id,)).fetchone()
            new=con.execute('SELECT bot_key,verdict,artifact_dir FROM cases WHERE id=?',(new_case_id,)).fetchone()
            if not old or not new or old['bot_key']==new['bot_key'] or new['verdict']!='NOT GUILTY' or not new['artifact_dir']:
                raise ValueError('A different approved, completed business technique is required')
            if con.execute('SELECT id FROM trial_pivots WHERE retired_case_id=?',(old_case_id,)).fetchone():
                con.execute('COMMIT');return False
            cur=con.execute('INSERT INTO trial_pivots(retired_case_id,new_case_id,reason) VALUES (?,?,?)',
                            (old_case_id,new_case_id,reason))
            self._audit(con,'trial_pivoted',{'pivot_id':cur.lastrowid,
                'retired_case_id':old_case_id,'new_case_id':new_case_id,'reason':reason})
            con.execute('COMMIT');return True

    def lifecycle_summary(self):
        with self.connect() as con:
            return {'launched':con.execute('SELECT COUNT(*) FROM trial_launches').fetchone()[0],
                    'retired':con.execute('SELECT COUNT(*) FROM trial_retirements').fetchone()[0],
                    'technique_pivots':con.execute('SELECT COUNT(*) FROM trial_pivots').fetchone()[0],
                    'awaiting_pivot':con.execute("""SELECT COUNT(*) FROM trial_retirements r LEFT JOIN
                      trial_pivots p ON r.case_id=p.retired_case_id WHERE p.id IS NULL""").fetchone()[0]}

    def record_event(self, case_id, kind, quantity=1, gross_cents=0, fee_cents=0, note=''):
        if kind not in ('view','click','sale','refund'):
            raise ValueError('Unknown event type')
        if quantity < 1 or gross_cents<0 or fee_cents<0:
            raise ValueError('Quantity and amounts cannot be negative')
        if len(note)>400:
            raise ValueError('Note too long')
        if kind not in ('sale','refund') and (gross_cents or fee_cents):
            raise ValueError('Money amounts only accepted for sale/refund')
        with self.connect() as con:
            con.execute('BEGIN IMMEDIATE')
            row=con.execute('SELECT id,verdict FROM cases WHERE id=?',(case_id,)).fetchone()
            if not row or row['verdict']!='NOT GUILTY':
                con.execute('ROLLBACK')
                raise ValueError('Case is missing or rejected')
            cur=con.execute('''INSERT INTO events
              (case_id,kind,quantity,gross_cents,fee_cents,source,note)
              VALUES(?,?,?,?,?,'user_reported',?)''', (case_id,kind,quantity,gross_cents,fee_cents,note))
            self._audit(con,'user_reported_event',{'event_id':cur.lastrowid,'case_id':case_id,
                'kind':kind,'quantity':quantity,'gross_cents':gross_cents,'fee_cents':fee_cents})
            con.execute('COMMIT')

    def approve_for_manual_publication(self, cid, rights_ack, platform_ack):
        if not (rights_ack and platform_ack):
            raise ValueError('Rights and platform fee/terms acknowledgments are required')
        with self.connect() as con:
            con.execute('BEGIN IMMEDIATE')
            row=con.execute('SELECT verdict,artifact_dir,human_status FROM cases WHERE id=?',(cid,)).fetchone()
            if not row or row['verdict'] != 'NOT GUILTY' or not row['artifact_dir']:
                con.execute('ROLLBACK')
                raise ValueError('Only completed, allowed drafts can be marked ready')
            if row['human_status'] == 'ready_for_manual_publication':
                con.execute('COMMIT')
                return
            con.execute('UPDATE cases SET human_status=? WHERE id=?',('ready_for_manual_publication',cid))
            self._audit(con,'human_acknowledged_manual_publish',{'case_id':cid})
            con.execute('COMMIT')

    def metrics(self):
        with self.connect() as con:
            rows = con.execute('''SELECT c.id,c.bot_key,c.title,
             COALESCE(SUM(CASE WHEN e.kind='view' THEN e.quantity ELSE 0 END),0) AS views,
             COALESCE(SUM(CASE WHEN e.kind='click' THEN e.quantity ELSE 0 END),0) AS clicks,
             COALESCE(SUM(CASE WHEN e.kind='sale' THEN e.quantity ELSE 0 END),0) AS sales,
             COALESCE(SUM(CASE WHEN e.kind='sale' THEN e.gross_cents WHEN e.kind='refund'
                  THEN -e.gross_cents ELSE 0 END),0) AS gross_cents,
             COALESCE(SUM(CASE WHEN e.kind='sale' THEN e.fee_cents WHEN e.kind='refund'
                  THEN -e.fee_cents ELSE 0 END),0) AS fee_cents
             FROM cases c LEFT JOIN events e ON e.case_id=c.id
             GROUP BY c.id ORDER BY c.id DESC''').fetchall()
            return [dict(r) for r in rows]

    def summary(self):
        cases=self.cases(100000)
        metrics=self.metrics()
        return {'cases':len(cases), 'allowed':sum(x['verdict']=='NOT GUILTY' for x in cases),
                'rejected':sum(x['verdict']=='GUILTY' for x in cases),
                'manual_gross_cents':sum(m['gross_cents'] for m in metrics),
                'manual_fees_cents':sum(m['fee_cents'] for m in metrics),
                'manual_net_cents':sum(m['gross_cents']-m['fee_cents'] for m in metrics),
                'audit_valid':self.audit_valid(), 'revisions':len(self.revisions(100000)),
                'lifecycle':self.lifecycle_summary()}
