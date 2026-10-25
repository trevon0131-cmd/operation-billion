import json
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from botfarm.lifecycle import assess, choose_new_technique
from botfarm.runner import run_once
from botfarm.storage import Store

BASE=datetime(2026,10,1,12,tzinfo=timezone.utc)

def trial(**changes):
    row=dict(id=1,bot_key='study_planner',created_at=BASE.isoformat(),verdict='NOT GUILTY',
             artifact_dir='C:/fake/complete',launched_at=None,retired_at=None,views=0,
             clicks=0,sales=0,gross_cents=0,fee_cents=0)
    row.update(changes)
    return row

class LifeCycleRules(unittest.TestCase):
    def test_fresh_draft_not_retired(self):
        self.assertEqual(assess(trial(),BASE+timedelta(days=3)).classification,'NEEDS_LAUNCH')

    def test_draft_after_two_weeks_pivots_but_not_customer_failure(self):
        d=assess(trial(),BASE+timedelta(days=14))
        self.assertEqual((d.action,d.classification),('retire','UNLAUNCHED'))
        self.assertIn('No claim',d.explanation)

    def test_fresh_published_offer_clock_starts_on_launch_not_creation(self):
        t=trial(created_at=(BASE-timedelta(days=60)).isoformat(),launched_at=BASE.isoformat())
        self.assertEqual(assess(t,BASE+timedelta(days=2)).action,'keep')
        self.assertEqual(assess(t,BASE+timedelta(days=14)).classification,'INCONCLUSIVE')

    def test_early_stop_requires_actual_reach(self):
        t=trial(launched_at=BASE.isoformat(),views=99)
        self.assertEqual(assess(t,BASE+timedelta(days=8)).action,'keep')
        t['views']=100
        self.assertEqual(assess(t,BASE+timedelta(days=8)).classification,'LOW_ENGAGEMENT')
        t['clicks']=1
        self.assertEqual(assess(t,BASE+timedelta(days=8)).action,'keep')

    def test_reported_positive_results_dont_expire(self):
        t=trial(launched_at=BASE.isoformat(),views=250,sales=1,gross_cents=300,fee_cents=30)
        self.assertEqual(assess(t,BASE+timedelta(days=90)).classification,'REPORTED_POSITIVE')

    def test_never_retire_rejected_or_incomplete(self):
        self.assertEqual(assess(trial(artifact_dir=''),BASE+timedelta(days=90)).action,'none')
        self.assertEqual(assess(trial(verdict='GUILTY'),BASE+timedelta(days=90)).action,'none')

    def test_different_technique_not_same_lane(self):
        b=choose_new_technique('sticker_studio',{},())
        self.assertNotEqual(b.key,'sticker_studio')
        self.assertNotEqual(b.lane,'Digital artwork')
        self.assertGreater(b.suggested_price,0)

class DurableLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.home=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()

    def new_trial(self):
        run_once(self.home,max_cases=1)
        st=Store(self.home)
        rows=st.trial_rows()
        self.assertEqual(len(rows),1)
        return st, rows[0]['id']

    def test_live_trial_writes_audited_launch(self):
        st,cid=self.new_trial()
        self.assertTrue(st.mark_trial_launched(cid,'https://shop.example.org/item/1'))
        self.assertFalse(st.mark_trial_launched(cid,'https://shop.example.org/item/1'))
        self.assertEqual(st.lifecycle_summary()['launched'],1)
        self.assertTrue(st.audit_valid())
        with self.assertRaises(ValueError):st.mark_trial_launched(cid,'http://example.org')

    def test_full_two_week_retire_and_real_different_technique(self):
        st,cid=self.new_trial()
        old=st.case(cid)
        result=run_once(self.home,max_cases=3,now=datetime.now(timezone.utc)+timedelta(days=15))
        self.assertEqual(result['retired'][0]['case_id'],cid)
        self.assertEqual(len(result['pivots']),1)
        new=st.case(result['pivots'][0]['new_case_id'])
        self.assertNotEqual(new['bot_key'],old['bot_key'])
        self.assertEqual(new['verdict'],'NOT GUILTY')
        self.assertTrue(new['artifact_dir'])
        self.assertTrue(st.audit_valid())
        self.assertEqual(st.lifecycle_summary()['retired'],1)
        self.assertEqual(st.lifecycle_summary()['technique_pivots'],1)

    def test_no_duplicate_retirement_or_pivot_on_repeat(self):
        st,cid=self.new_trial();future=datetime.now(timezone.utc)+timedelta(days=15)
        run_once(self.home,max_cases=2,now=future)
        second=run_once(self.home,max_cases=2)
        self.assertNotIn(cid,[r['case_id'] for r in second['retired']])
        self.assertNotIn(cid,[p['old_case_id'] for p in second['pivots']])
        self.assertEqual(st.lifecycle_summary()['technique_pivots'],1)
        self.assertTrue(st.audit_valid())

    def test_cannot_fake_pivot_to_original_bot(self):
        st,cid=self.new_trial()
        self.assertTrue(st.retire_trial(cid,'UNLAUNCHED','Fourteen days unlaunched'))
        with self.assertRaises(ValueError):st.record_trial_pivot(cid,cid,'self loop')
        self.assertTrue(st.audit_valid())

    def test_tamper_retirement_record_detected(self):
        st,cid=self.new_trial();st.retire_trial(cid,'UNLAUNCHED','unlaunched')
        con = sqlite3.connect(st.db)
        try:
            con.execute("UPDATE trial_retirements SET classification='LOW_RETURN' WHERE case_id=?",(cid,))
            con.commit()
        finally:
            con.close()
        self.assertFalse(st.audit_valid())
        with self.assertRaises(RuntimeError):run_once(self.home,max_cases=1)

    def test_migration_existing_database(self):
        from botfarm.storage import SCHEMA
        st=Store(self.home)
        run_once(self.home,max_cases=2)
        before=st.summary()['cases']
        st=Store(self.home)
        self.assertEqual(st.summary()['cases'],before)
        self.assertTrue(st.audit_valid())

if __name__=='__main__':unittest.main()
