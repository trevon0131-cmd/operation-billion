"""Offline tests that never contact sellers or customers."""
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from botfarm.client_pipeline import ClientPipeline
from botfarm.launch_workflow import collect_work, export
from botfarm.runner import run_once
from botfarm.storage import Store

class TwoLaneTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.home=Path(self.tmp.name)
        self.store=Store(self.home)
    def tearDown(self):self.tmp.cleanup()
    def test_both_lanes_are_queued(self):
        run_once(self.home,live=False,max_cases=32)
        queues=collect_work(self.home,self.store)
        self.assertTrue(queues['digital'])
        self.assertTrue(queues['services'])
        result=export(self.home,self.store)
        self.assertGreater(result['digital_product_drafts'],0)
        self.assertGreater(result['service_offer_templates'],0)
        self.assertEqual(result['ready_for_unattended_sale'],0)
        self.assertTrue((self.home/'output/sales_workflow/START_HERE_TWO_TRACKS.md').is_file())
    def test_guilty_never_in_queue(self):
        run_once(self.home,live=False,max_cases=32)
        queued=collect_work(self.home,self.store)
        ids={x['case_id'] for lane in ('digital','services') for x in queued[lane]}
        for x in self.store.cases():
            if x['verdict']=='GUILTY':self.assertNotIn(x['id'],ids)
    def test_client_pipeline_deduplicates_audits_and_suppresses(self):
        c=ClientPipeline(self.home)
        lid=c.add('Example Business','https://example.com')
        self.assertEqual(lid,c.add('Duplicate Business','https://example.com'))
        self.assertEqual(c.stage(lid,'REVIEWED'),'REVIEWED')
        c.stage(lid,'DO_NOT_CONTACT')
        with self.assertRaises(ValueError):c.stage(lid,'CONTACT_RECORDED')
        self.assertTrue(c.audit_valid())
        with c.conn() as conn:
            conn.execute("UPDATE leads SET business='tampered' WHERE id=?",(lid,))
        self.assertFalse(c.audit_valid())
    def test_no_contact_without_prepared_packet(self):
        c=ClientPipeline(self.home);lid=c.add('Sample Business','https://example.org')
        with self.assertRaises(ValueError):c.stage(lid,'CONTACT_RECORDED')
        with self.assertRaises(ValueError):c.add('localhost','https://localhost/admin')
        with self.assertRaises(ValueError):c.add('Not public','http://example.com')
    def test_service_packet_requires_approved_case_and_no_sending(self):
        run_once(self.home,live=False,max_cases=32)
        case=collect_work(self.home,self.store)['services'][0]['case_id']
        c=ClientPipeline(self.home);lid=c.add('Local Business','https://example.com')
        result=c.pack(lid,self.store,case,with_review=False)
        self.assertFalse(result['contact_sent'])
        self.assertEqual(c.get(lid)['status'],'PACKET_READY')
        report=Path(result['folder'])/'EVIDENCE_AND_NEXT_STEPS.json'
        self.assertFalse(json.loads(report.read_text())['site_review_performed'])
        self.assertTrue(c.audit_valid())
    def test_client_14_day_review(self):
        c=ClientPipeline(self.home)
        lid=c.add('Sample Shop','https://example.com')
        with c.conn() as conn:
            conn.execute("UPDATE lead_steps SET created_at = datetime('now','-16 days') WHERE lead_id=?",(lid,))
        self.assertIn('UNLAUNCHED_14D',c.reviews()[0]['decision'])
    def test_non_service_case_rejected(self):
        run_once(self.home,live=False,max_cases=32)
        case=collect_work(self.home,self.store)['digital'][0]['case_id']
        c=ClientPipeline(self.home);lid=c.add('Service','https://example.org')
        with self.assertRaises(ValueError):c.pack(lid,self.store,case)
    def test_no_fake_sales(self):
        run_once(self.home,live=False,max_cases=32)
        export(self.home,self.store)
        queue=json.loads((self.home/'output/sales_workflow/DUAL_LANE_LAUNCH_QUEUE.json').read_text())
        self.assertEqual(queue['verified_sales_count'],0)
        self.assertFalse(queue['summary']['marketplace_publishing_available'])
        self.assertEqual(self.store.summary()['manual_gross_cents'],0)

if __name__=='__main__':unittest.main()

class BrandTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.home=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def test_public_brand_validates_and_writes(self):
        from botfarm.seller_ops import update_public_brand,safe_profile
        update_public_brand(self.home,'Operation Billion','hello@example.org')
        self.assertEqual(safe_profile(self.home)['shop_name'],'Operation Billion')
        self.assertEqual(safe_profile(self.home)['public_support_email'],'hello@example.org')
    def test_rejects_invalid_email(self):
        from botfarm.seller_ops import update_public_brand
        with self.assertRaises(ValueError):update_public_brand(self.home,'Store','not-an-email')
