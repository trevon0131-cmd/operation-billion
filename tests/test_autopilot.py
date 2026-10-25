import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from botfarm.autopilot import SingleInstance, startup_file
from botfarm.catalog import BY_KEY
from botfarm.quality import inspect, prepare_sell_kit
from botfarm.runner import run_once, create_case
from botfarm.storage import Store
from botfarm.strategy import MAX_VARIANTS, propose, repair
from botfarm.court import adjudicate
from botfarm.workshop import make_artifact

class AutonomousTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.home=Path(self.tmp.name)
    def tearDown(self): self.tmp.cleanup()

    def test_rejected_physical_sale_gets_a_new_allowed_trial(self):
        b=BY_KEY['ebay_sticker_scout']
        bad=propose(b,0)
        ruling=adjudicate(bad.proposal)
        self.assertEqual(ruling.verdict,'GUILTY')
        fix=repair(bad,ruling)
        self.assertEqual(adjudicate(fix.proposal).verdict,'NOT GUILTY')
        self.assertEqual(fix.bot.artifact,'svg')
        self.assertGreater(fix.bot.suggested_price,0)
        self.assertNotEqual(bad.proposal.action,fix.proposal.action)

    def test_affiliate_publication_replaced_with_local_only(self):
        b=BY_KEY['affiliate_review']
        original=propose(b,0)
        fix=repair(original,adjudicate(original.proposal))
        self.assertEqual(adjudicate(original.proposal).verdict,'GUILTY')
        self.assertEqual(fix.proposal.action,'generate_local_draft')
        self.assertEqual(adjudicate(fix.proposal).verdict,'NOT GUILTY')

    def test_normal_bot_proposal_needs_no_repair(self):
        c=propose(BY_KEY['study_planner'],0)
        self.assertIsNone(repair(c,adjudicate(c.proposal)))

    def test_high_quality_sticker_package_created(self):
        b=BY_KEY['sticker_studio']
        folder=make_artifact(self.home,b,0,'a'*64,[])
        self.assertTrue(inspect(folder)['passed'])
        pack=prepare_sell_kit(folder,b.channel)
        self.assertTrue(Path(pack['zip']).is_file())
        self.assertIn('NOT LISTED',(folder/'SELLING_CHECKLIST.md').read_text())
        self.assertEqual(json.loads((folder/'metadata.json').read_text())['publication_status'],'DRAFT_ONLY')

    def test_bad_png_fails_qa(self):
        b=BY_KEY['sticker_studio']
        folder=make_artifact(self.home,b,0,'a'*64,[])
        (folder/'sticker_transparent.png').write_bytes(b'broken data'*100)
        self.assertFalse(inspect(folder)['passed'])
        with self.assertRaises(ValueError):prepare_sell_kit(folder,b.channel)

    def test_end_to_end_guilty_then_new_repaired_case(self):
        r=run_once(self.home,max_cases=32)
        self.assertEqual(len(r['repairs']),2)
        self.assertEqual(len(r['created']),31)
        self.assertEqual(len([x for x in r['created'] if x['verdict']=='GUILTY']),2)
        st=Store(self.home)
        self.assertTrue(st.audit_valid())
        self.assertEqual(st.summary()['revisions'],2)
        for fix in r['repairs']:
            self.assertEqual(st.case(fix['rejected_case_id'])['verdict'],'GUILTY')
            self.assertEqual(st.case(fix['replacement_case_id'])['verdict'],'NOT GUILTY')
            self.assertIsNotNone(st.case(fix['replacement_case_id'])['artifact_dir'])

    def test_revisions_are_tamper_evident(self):
        run_once(self.home,max_cases=32)
        st=Store(self.home)
        con = sqlite3.connect(st.db)
        try:
            con.execute("UPDATE revisions SET lesson='hacked' WHERE id=1")
            con.commit()
        finally:
            con.close()
        self.assertFalse(st.audit_valid())
        with self.assertRaises(RuntimeError):run_once(self.home,max_cases=1)

    def test_daily_budget_safely_stops(self):
        first=run_once(self.home,max_cases=32)
        second=run_once(self.home,max_cases=32)
        self.assertEqual(len(first['created']),31)
        self.assertLessEqual(len(second['created']),1)
        self.assertLessEqual(Store(self.home).daily_count(),32)

    def test_crash_after_rejection_resumes_repair(self):
        b=BY_KEY['ebay_sticker_scout']
        first=create_case(Store(self.home),self.home,b,propose(b,0),0,[])
        self.assertEqual(first['verdict'],'GUILTY')
        r=run_once(self.home,max_cases=1)
        self.assertEqual(len(r['repairs']),1)
        self.assertEqual(r['repairs'][0]['rejected_case_id'],first['case_id'])
        self.assertTrue(Store(self.home).audit_valid())

    def test_duplicate_single_instance_is_rejected(self):
        with SingleInstance(self.home/'data'/'test.lock'):
            with self.assertRaises(RuntimeError):
                with SingleInstance(self.home/'data'/'test.lock'):
                    pass
        with SingleInstance(self.home/'data'/'test.lock'):
            pass

    def test_safe_cap_and_no_platform_authorization(self):
        self.assertGreaterEqual(MAX_VARIANTS,8)
        st=Store(self.home)
        self.assertEqual(st.summary()['manual_net_cents'],0)
        self.assertTrue(st.audit_valid())

    def test_windows_only_autostart(self):
        import os
        if os.name!='nt':
            with self.assertRaises(ValueError):startup_file()

if __name__=='__main__':unittest.main()
