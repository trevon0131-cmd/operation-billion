import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from botfarm.runner import run_once
from botfarm.storage import Store
from botfarm.seller_ops import package_case, refresh_all, safe_profile
from botfarm.business_scout import analyze_html, validate_public_url, review_one

class SellerOperationsTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.home=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def test_automatic_prep_for_first_court_approved_product(self):
        summary=run_once(self.home,max_cases=1)
        row=Store(self.home).case(summary['created'][0]['case_id'])
        self.assertEqual(row['verdict'],'NOT GUILTY')
        out=Path(row['artifact_dir'])
        data=json.loads((out/'SELLER_OPERATIONS.json').read_text('utf-8'))
        self.assertEqual(data['external_requests_made'],0)
        self.assertFalse(data['publication_permitted'])
        self.assertEqual(data['status'],'WAITING_FOR_AUTHORIZED_SELLER_ACCOUNT')
        self.assertTrue((out/'CUSTOMER_REPLY_DRAFTS.md').exists())
        self.assertTrue(Store(self.home).audit_valid())
    def test_refuse_guilty_and_outside_project_paths(self):
        run_once(self.home,max_cases=1)
        row=Store(self.home).cases(1)[0]
        with self.assertRaises(ValueError):package_case(self.home,{**row,'verdict':'GUILTY'})
        with self.assertRaises(ValueError):package_case(self.home,{**row,'artifact_dir':str(self.home.parent)})
    def test_revised_sticker_alternative_receives_seller_draft(self):
        run_once(self.home,max_cases=32)
        st=Store(self.home)
        for rev in st.revisions():
            new=st.case(rev['replacement_case_id'])
            if new['bot_key']=='ebay_sticker_scout':
                folder=Path(new['artifact_dir'])
                info=json.loads((folder/'SELLER_OPERATIONS.json').read_text('utf-8'))
                self.assertEqual(info['preferred_channel'],'ko-fi')
                self.assertEqual(info['asking_price_suggestion_usd'],'3.00')
                return
        self.fail('Missing court-approved digital sticker alternative')

    def test_public_profile_rejects_sensitive_fields(self):
        p=self.home/'config'/'store_public_profile.json';p.parent.mkdir()
        p.write_text(json.dumps({'shop_name':'Example','bank_account':'NEVER'}))
        with self.assertRaises(ValueError):safe_profile(self.home)
    def test_existing_cases_are_reprepared_without_sales(self):
        run_once(self.home,max_cases=2)
        st=Store(self.home)
        ans=refresh_all(self.home,st)
        self.assertEqual(len(ans['drafts_prepared']),2)
        self.assertEqual(ans['external_publications'],0)
        self.assertTrue(st.audit_valid())

class BusinessScoutTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.home=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def test_website_heurstics_not_google_maps(self):
        x=analyze_html('https://example.com','<html><head><title>Example Business</title></head><body><img src="a.png"><h1>Test</h1></body></html>')
        self.assertIn('No meta description detected in the retrieved HTML',x['potential_improvements'])
        self.assertTrue(x['no_outreach_sent'])
        self.assertEqual(x['title'],'Example Business')
    def test_local_urls_rejected(self):
        for url in ['http://example.com','https://127.0.0.1','https://localhost','https://example.com:1234','https://user:pass@example.com']:
            with self.subTest(url=url):
                with self.assertRaises(ValueError):validate_public_url(url)
    def test_opt_in_fetcher_and_draft_only(self):
        out=review_one(self.home,'https://example.com',fetcher=lambda x:'<html><h1>Welcome</h1></html>')
        self.assertTrue(Path(out['report_folder'],'REPORT_DRAFT.md').exists())
        self.assertTrue(out['report']['no_outreach_sent'])
        self.assertFalse((self.home/'data').exists())

if __name__=='__main__':unittest.main()
