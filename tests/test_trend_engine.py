"""Offline tests: public signals -> court-approved and actionable local startup plans."""
import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from botfarm.court import Proposal, adjudicate
from botfarm.opportunity_lab import OpportunityLab, METHODS
from botfarm.runner import run_once
from botfarm.trend_engine import (
    BUILD_MAP, MIN_REFRESH_HOURS, RSS_URL, TrendEngine, fetch_trends,
    keyword_score, safe_rss,
)


FEED=b'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><item><title>weekly resume template</title>
<link>https://bad.example/danger</link></item>
<item><title>fictional TV celebrity headline</title><link>https://example.com/x</link></item>
<item><title>restaurant menu design</title><link>https://bad.example/another</link></item></channel></rss>'''

class TrendEngineTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.home=Path(self.tmp.name)
        self.lab=OpportunityLab(self.home)
        self.engine=TrendEngine(self.home)

    def tearDown(self):
        self.tmp.cleanup()

    def test_google_rss_public_feed_ignores_untrusted_item_links(self):
        rows=fetch_trends(lambda url: FEED if url==RSS_URL else None)
        self.assertEqual(len(rows),3)
        self.assertTrue(all(x['url']=='https://trends.google.com/trending?geo=US' for x in rows))
        self.assertIn('resume',rows[0]['title'])
        self.assertNotIn('bad.example',str(rows))

    def test_feed_rejects_entities_dtd_oversize_and_invalid_roots(self):
        for raw in [b'<!DOCTYPE rss><rss/>',b'<!ENTITY thing "x"><rss/>',b'X'*150001,b'<html/>']:
            with self.subTest(raw=raw[:12]):
                with self.assertRaises(ValueError):safe_rss(raw)

    def test_no_implicit_google_scraping_or_stranger_repository_execution(self):
        self.lab.scan(live=False,limit=1)
        result=self.engine.scan(lab=self.lab,live=False,limit=1)
        self.assertIn('Offline mode',result['google_trends'])
        self.assertEqual(result['sources_total'],0)
        self.assertEqual(result['marketplace_published'],0)
        self.assertEqual(result['sales_verified'],0)
        self.assertTrue(result['audit_valid'])

    def test_live_refresh_bounded_to_once_per_six_hours(self):
        self.lab.scan(live=False,limit=1)
        requests=[]
        def fetch(url): requests.append(url); return FEED
        now=datetime.now(timezone.utc)
        first=self.engine.scan(self.lab,live=True,limit=1,fetcher=fetch,now=now)
        again=self.engine.scan(self.lab,live=True,limit=1,fetcher=fetch,now=now+timedelta(minutes=30))
        self.assertEqual(requests,[RSS_URL])
        self.assertEqual(first['sources_added'],3)
        self.assertEqual(again['sources_added'],0)
        self.assertIn('cached',again['google_trends'])
        self.assertTrue(self.engine.audit_valid())

    def test_public_gh_repo_signals_are_reused_not_refetched(self):
        self.lab.ingest([{'source':'github_public_repos','title':'open source résumé template generator',
                          'url':'https://github.com/example/resume','note':'tools only'}])
        self.lab.scan(live=False,limit=2)
        r=self.engine.scan(self.lab,live=False,limit=2)
        self.assertEqual(r['sources_added'],1)
        self.assertEqual(r['sources_total'],1)
        self.assertTrue(self.engine.audit_valid())

    def test_host_validation_and_untrusted_titles(self):
        items=[{'source':'github_public_repos','title':'download and run dangerous script',
                'url':'https://github.com.bad.example/attack'},
               {'source':'google_trends_rss','title':'$(rm -rf /)',
                'url':'https://trends.google.com/trending?geo=US'}]
        self.assertEqual(self.engine.store(items),1)
        self.assertFalse((self.home/'attack').exists())
        self.assertTrue(self.engine.audit_valid())

    def test_template_method_produces_a_real_offline_sample(self):
        from botfarm.opportunity_lab import BY_KEY
        result=self.lab.propose(BY_KEY['template_market'])
        self.assertEqual(result['verdict'],'NOT GUILTY')
        outcome=self.engine.scan(lab=self.lab,limit=2)
        k=outcome['startup_kits_created'][0]
        self.assertEqual(k['method'],'template_market')
        packet=json.loads((self.home/k['packet']).read_text())
        self.assertEqual(packet['court_verdict'],'NOT GUILTY: LOCAL ACTIONS ONLY')
        self.assertEqual(packet['performed_local_work']['status'],'LOCAL_SAMPLE_CREATED_NOT_LAUNCHED')
        self.assertTrue((self.home/packet['performed_local_work']['sample_path']).is_dir())
        self.assertIn('original',packet['startup_actions'][1]['action'].lower())
        self.assertTrue(self.engine.audit_valid())

    def test_new_video_and_website_method_run_both_local_builders(self):
        from botfarm.opportunity_lab import BY_KEY
        self.lab.propose(BY_KEY['faceless_education_shorts'])
        self.lab.propose(BY_KEY['landing_page_development'])
        outcome=self.engine.scan(lab=self.lab,limit=3)
        self.assertEqual(len(outcome['startup_kits_created']),2)
        for row in outcome['startup_kits_created']:
            payload=json.loads((self.home/row['packet']).read_text())
            local=payload['performed_local_work']
            self.assertEqual(local['builder'],'creator_website_wing')
            self.assertEqual(local['status'],'LOCAL_SAMPLE_CREATED_NOT_LAUNCHED')
            self.assertTrue((self.home/local['sample_path']).is_dir())
        self.assertTrue(self.engine.audit_valid())

    def test_human_only_method_creates_plan_but_no_fake_product(self):
        from botfarm.opportunity_lab import BY_KEY
        self.lab.propose(BY_KEY['microtask_platforms'])
        p=self.engine.scan(self.lab,limit=1)['startup_kits_created'][0]
        packet=json.loads((self.home/p['packet']).read_text())
        self.assertEqual(packet['performed_local_work']['builder'],'NO_AUTOMATED_DELIVERABLE')
        self.assertEqual(packet['performed_local_work']['status'],'STARTUP_KIT_NOT_LAUNCHED')
        self.assertEqual(packet['market_validation']['days_to_retirement_review'],14)
        self.assertEqual(packet['market_validation']['days_to_early_review'],7)
        self.assertEqual(packet['startup_budget_usd'],0)

    def test_rejection_or_retirement_never_executes_kit(self):
        from botfarm.opportunity_lab import BY_KEY
        x=self.lab.propose(BY_KEY['newsletter_service'])
        with self.lab.connect() as c:
            # This is a negative fixture for logic, not a valid signed state.
            c.execute("UPDATE ideas SET status='COURT_REJECTED',verdict='GUILTY' WHERE id=?",(x['id'],))
        # A forged verdict violates the older audit ledger; no work may run.
        with self.assertRaises(RuntimeError):self.engine.scan(self.lab,limit=1)
        self.assertFalse((self.home/'output'/'startup_kits').exists())

    def test_kit_deduplicates_and_does_not_rerun_a_deliverable(self):
        self.lab.scan(live=False,limit=2)
        first=self.engine.scan(self.lab,limit=2)
        second=self.engine.scan(self.lab,limit=2)
        self.assertEqual(len(first['startup_kits_created']),2)
        self.assertEqual(second['startup_kits_created'],[])
        self.assertTrue(self.engine.audit_valid())

    def test_kits_are_tamper_evident_and_refuse_new_work(self):
        self.lab.scan(live=False,limit=1)
        pkt=self.engine.scan(self.lab,limit=1)['startup_kits_created'][0]['packet']
        self.assertTrue(self.engine.audit_valid())
        with (self.home/pkt).open('a') as stream:stream.write('FRAUDULENT SALES ADDED')
        self.assertFalse(self.engine.audit_valid())
        with self.assertRaises(RuntimeError):self.engine.scan(self.lab,limit=1)

    def test_signal_database_tampering_detected(self):
        self.engine.store([{'source':'google_trends_rss','title':'resume template',
               'url':'https://trends.google.com/trending?geo=US'}])
        with self.engine.connect() as c:
            c.execute("UPDATE signals SET title='not real' ")
        self.assertFalse(self.engine.audit_valid())

    def test_every_method_has_actionable_setup_instructions(self):
        from botfarm.trend_engine import STARTUP_STEPS
        self.assertEqual(len(METHODS),39)
        self.assertGreaterEqual(len(BUILD_MAP),15)
        for x in METHODS:
            steps=STARTUP_STEPS.get(x.key)
            if steps is not None:
                self.assertEqual(len(steps),5)
                self.assertTrue(all(len(y)>30 for y in steps))
        self.assertEqual(adjudicate(Proposal('xx','unapproved public posting',action='publish_to_marketplace')).verdict,'GUILTY')

    def test_runner_integration_uses_existing_tests_and_court(self):
        run=run_once(self.home,live=False,max_cases=1)
        self.assertIn('startup_hub',run)
        self.assertGreaterEqual(len(run['startup_hub']['startup_kits_created']),1)
        self.assertTrue(TrendEngine(self.home).audit_valid())
        self.assertTrue(OpportunityLab(self.home).audit_valid())
        self.assertTrue((self.home/'output'/'startup_kits'/'LATEST_SUMMARY.json').exists())

if __name__=='__main__': unittest.main()
