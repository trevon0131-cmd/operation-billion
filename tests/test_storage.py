import sqlite3
import tempfile
import threading
import unittest
from pathlib import Path
from botfarm.storage import Store
from botfarm.court import Proposal, adjudicate

class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.home=Path(self.tmp.name)
        self.store=Store(self.home)
        self.judgment=adjudicate(Proposal('s','Original')).data()
    def tearDown(self): self.tmp.cleanup()
    def add(self, fingerprint='one', verdict=None):
        return self.store.add_case(fingerprint,'s','Original',0,verdict or self.judgment)
    def test_initialize(self):
        self.assertTrue(self.store.db.exists())
        self.assertTrue(self.store.audit_valid())
    def test_add_idempotent(self):
        self.assertIsNotNone(self.add())
        self.assertIsNone(self.add())
        self.assertEqual(self.store.summary()['cases'],1)
    def test_audit_tamper(self):
        self.add()
        con=sqlite3.connect(self.store.db)
        try:
            con.execute("UPDATE audit SET action='tampered'")
            con.commit()
        finally:
            con.close()
        self.assertFalse(self.store.audit_valid())
    def test_event_validated(self):
        self.add()
        with self.assertRaises(ValueError): self.store.record_event(7,'sale',gross_cents=100)
        with self.assertRaises(ValueError): self.store.record_event(1,'view',gross_cents=100)
        with self.assertRaises(ValueError): self.store.record_event(1,'sale',gross_cents=-1)
    def test_manual_revenue_is_labeled(self):
        cid=self.add()
        self.store.record_event(cid,'view',30)
        self.store.record_event(cid,'sale',1,1000,100)
        self.store.record_event(cid,'refund',1,300,20)
        row=self.store.metrics()[0]
        self.assertEqual(row['views'],30)
        self.assertEqual(row['gross_cents'],700)
        self.assertEqual(row['fee_cents'],80)
        self.assertEqual(self.store.summary()['manual_net_cents'],620)
        self.assertTrue(self.store.audit_valid())
    def test_approve_requires_artifact(self):
        cid=self.add()
        with self.assertRaises(ValueError): self.store.approve_for_manual_publication(cid,True,True)
        self.store.update_artifact(cid,'output/demo')
        with self.assertRaises(ValueError): self.store.approve_for_manual_publication(cid,False,True)
        self.store.approve_for_manual_publication(cid,True,True)
        self.assertEqual(self.store.case(cid)['human_status'],'ready_for_manual_publication')
        self.assertTrue(self.store.audit_valid())
    def test_concurrent_duplicate_single_case(self):
        ids=[]
        def job(): ids.append(Store(self.home).add_case('shared','s','Original',0,self.judgment))
        workers=[threading.Thread(target=job) for _ in range(8)]
        for t in workers:t.start()
        for t in workers:t.join()
        self.assertEqual(sum(i is not None for i in ids),1)
        self.assertEqual(self.store.summary()['cases'],1)
        self.assertTrue(self.store.audit_valid())
    def test_audit_detects_case_content_tampering(self):
        self.add()
        con=sqlite3.connect(self.store.db)
        try:
            con.execute("UPDATE cases SET case_json='{}' WHERE id=1")
            con.commit()
        finally: con.close()
        self.assertFalse(self.store.audit_valid())
    def test_audit_detects_event_tampering(self):
        cid=self.add()
        self.store.record_event(cid,'sale',gross_cents=250)
        con=sqlite3.connect(self.store.db)
        try:
            con.execute("UPDATE events SET gross_cents=25000 WHERE case_id=?",(cid,))
            con.commit()
        finally: con.close()
        self.assertFalse(self.store.audit_valid())
    def test_daily_limit_is_transactional(self):
        self.assertIsNotNone(self.store.add_case('a','s','Original',0,self.judgment,daily_cap=1))
        with self.assertRaises(ValueError):
            self.store.add_case('b','s','Second',0,self.judgment,daily_cap=1)
        self.assertEqual(self.store.summary()['cases'],1)
    def test_unfinished_can_be_found(self):
        cid=self.add()
        pending=self.store.unfinished_artifacts()
        self.assertEqual([r['id'] for r in pending],[cid])
        self.store.update_artifact(cid,'output/created')
        self.assertEqual(self.store.unfinished_artifacts(),[])
    def test_rejected_cannot_record(self):
        denied=adjudicate(Proposal('x','Paid',expenditure_usd=1)).data()
        self.add('bad',denied)
        with self.assertRaises(ValueError): self.store.record_event(1,'sale',gross_cents=100)
