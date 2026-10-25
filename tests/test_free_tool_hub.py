import json
import sqlite3
import tempfile
import unittest
from datetime import datetime,timedelta,timezone
from pathlib import Path
from unittest.mock import patch
from botfarm.free_tool_hub import (FreeToolHub,available_tools,free_doctor,fetch_github,
    SEARCH_QUERIES,TOOL_MAP,canonical_need)


def sample(url='https://github.com/example/my-free-tool',description='Useful original toolkit'):
    return json.dumps({'items':[{'full_name':'example/my-free-tool','html_url':url,
         'description':description,'archived':False,'private':False,'disabled':False,
         'license':{'spdx_id':'MIT'},'language':'Python'}]}).encode()


class FreeHubTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home=Path(self.tmp.name)

    def test_free_tools_do_not_advertise_paid_api(self):
        self.assertGreaterEqual(len(TOOL_MAP),15)
        for item in TOOL_MAP.values():
            self.assertIn(item.kind, ('built_in','free_local_optional'))
            self.assertIn('no paid API',item.cost)
            self.assertTrue(item.repo.startswith(('local://','https://')))

    def test_hardware_absence_has_stable_fallback(self):
        found=available_tools('videos',which=lambda _:None)
        self.assertEqual(found[0]['key'],'farm')
        self.assertTrue(found[0]['currently_usable'])
        self.assertFalse(next(x for x in found if x['key']=='ffmpeg')['currently_usable'])
        self.assertFalse(any(x['downloaded_by_farm'] for x in found))

    def test_detection_is_not_model_download(self):
        row=free_doctor(which=lambda tool:'C:/bin/'+tool+'.exe')
        self.assertFalse(row['paid_api_required'])
        self.assertEqual(row['model_weights_and_commercial_rights'],'MUST_CHECK_SEPARATELY')
        self.assertFalse(row['automatically_installed'])

    def test_invalid_need_rejected(self):
        with self.assertRaises(ValueError):available_tools('guaranteed passive cash')
        with self.assertRaises(ValueError):FreeToolHub(self.home).plan('free money','test')

    def test_plan_stays_local_and_writes_file(self):
        h=FreeToolHub(self.home)
        r=h.plan('services','mobile website audits')
        self.assertTrue(Path(r['saved_to']).is_file())
        self.assertFalse((self.home/'data'/'creator_website_wing.sqlite3').exists())
        self.assertEqual(r['revenue_verified_usd'],0)
        self.assertIn('not',r['stage'].lower())

    def test_video_builder_goes_through_court(self):
        h=FreeToolHub(self.home)
        r=h.plan('tiktok','Create an educational short',execute_local=True)
        self.assertEqual(r['local_builder_result']['verdict'],'NOT GUILTY')
        self.assertEqual(r['need'],'videos')
        folder=Path(r['local_builder_result']['folder'])
        self.assertTrue((folder/'script.txt').exists())
        self.assertTrue((folder/'captions.srt').exists())
        self.assertFalse(any((folder/name).exists() for name in ('published.json','sent.json','payment.json')))

    def test_website_builder_local_only(self):
        h=FreeToolHub(self.home)
        r=h.plan('website','local tutoring',execute_local=True)
        self.assertEqual(r['local_builder_result']['verdict'],'NOT GUILTY')
        self.assertTrue((Path(r['local_builder_result']['folder'])/'index.html').exists())

    def test_other_method_build_not_claimed(self):
        h=FreeToolHub(self.home)
        r=h.plan('audio','Original voiceover',execute_local=True)
        self.assertIn('No direct local builder',r['execution'])
        self.assertNotIn('local_builder_result',r)

    def test_empty_plan_rejected(self):
        with self.assertRaises(ValueError):FreeToolHub(self.home).plan('videos','  ')

    def test_fixed_search_no_arbitrary_url(self):
        with self.assertRaises(ValueError):fetch_github('secret arbitrary scraping',fetcher=lambda _:sample())

    def test_github_result_is_unreviewed_never_enabled(self):
        res=fetch_github(SEARCH_QUERIES[0],fetcher=lambda _:sample())
        self.assertEqual(len(res),1)
        self.assertFalse(res[0]['can_auto_execute'])
        self.assertFalse(res[0]['rights_verified'])
        self.assertFalse(res[0]['cost_verified'])

    def test_github_rejects_invalid_and_offdomain_urls(self):
        for url in ('https://evil.example/repo','http://github.com/example/my-free-tool',
                    'https://github.com/example/my-free-tool/../../payload'):
            self.assertEqual(fetch_github(SEARCH_QUERIES[0],fetcher=lambda _:sample(url)),[])

    def test_github_rejects_oversized_response(self):
        with self.assertRaises(ValueError):fetch_github(SEARCH_QUERIES[0],fetcher=lambda _:b'a'*240001)

    def test_github_injection_is_just_plain_source_data(self):
        malicious='<script>alert(1)</script> & powershell Invoke-Expression'
        res=fetch_github(SEARCH_QUERIES[0],fetcher=lambda _:sample(description=malicious))
        self.assertEqual(res[0]['description'],malicious)
        self.assertFalse(res[0]['can_auto_execute'])

    def test_daily_cache_and_audit(self):
        h=FreeToolHub(self.home)
        t=datetime(2026,10,19,20,tzinfo=timezone.utc)
        calls=[]
        def fetch(url): calls.append(url);return sample()
        one=h.scan(live=True,now=t,fetcher=fetch)
        self.assertEqual(one['attempted_queries'],3)
        self.assertEqual(one['new_candidates'],3)
        self.assertEqual(len(h.findings()),3)
        self.assertTrue(h.audit_valid())
        two=h.scan(live=True,now=t+timedelta(hours=1),fetcher=fetch)
        self.assertEqual(two['attempted_queries'],0)
        self.assertEqual(len(calls),3)
        three=h.scan(live=True,now=t+timedelta(hours=25),fetcher=fetch)
        self.assertEqual(three['attempted_queries'],3)
        self.assertEqual(three['new_candidates'],0)
        self.assertEqual(len(h.findings()),3)

    def test_offline_scanning_does_not_touch_network(self):
        with patch('urllib.request.urlopen',side_effect=AssertionError('network used')):
            h=FreeToolHub(self.home)
            self.assertFalse(h.scan(live=False)['online'])
            self.assertEqual(h.findings(),[])

    def test_tamper_detection(self):
        h=FreeToolHub(self.home)
        h.scan(live=True,fetcher=lambda _:sample())
        # sqlite3.Connection.__exit__ commits/rolls back but DOES NOT close.
        # Explicitly close before TemporaryDirectory cleanup, especially on Windows.
        con = sqlite3.connect(h.db)
        try:
            con.execute("UPDATE findings SET payload='{}' WHERE id=1")
            con.commit()
        finally:
            con.close()
        self.assertFalse(h.audit_valid())
        with self.assertRaisesRegex(RuntimeError,'audit invalid'):h.scan(live=True,fetcher=lambda _:sample())

    def test_free_tool_database_context_releases_handle(self):
        h=FreeToolHub(self.home)
        with h.connect() as connection:
            self.assertEqual(connection.execute('SELECT COUNT(*) FROM findings').fetchone()[0],0)
        with self.assertRaises(sqlite3.ProgrammingError):
            connection.execute('SELECT 1')

    def test_bounded_limits(self):
        h=FreeToolHub(self.home)
        with self.assertRaises(ValueError):h.scan(live=True,limit=4,fetcher=lambda _:sample())
        with self.assertRaises(ValueError):h.scan(live=True,limit=0,fetcher=lambda _:sample())

    def test_network_error_does_not_create_fake_findings(self):
        h=FreeToolHub(self.home)
        r=h.scan(live=True,fetcher=lambda _:(_ for _ in ()).throw(OSError('offline')))
        self.assertEqual(r['new_candidates'],0)
        self.assertEqual(len(r['failed_queries']),3)
        self.assertTrue(h.audit_valid())

    def test_persistence_preserves_previous_evidence(self):
        h=FreeToolHub(self.home)
        h.scan(live=True,fetcher=lambda _:sample())
        h2=FreeToolHub(self.home)
        self.assertEqual(len(h2.findings()),3)
        self.assertTrue(h2.audit_valid())

if __name__=='__main__':unittest.main()
