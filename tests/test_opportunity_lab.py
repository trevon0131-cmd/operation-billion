"""Offline, real file/SQLite tests for the new income-method research hub."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import sqlite3
import tempfile
import unittest
from botfarm.opportunity_lab import (
    METHODS, OpportunityLab, collect_public, source_json, trusted_url,
)
from botfarm.court import Proposal, adjudicate
from botfarm.runner import run_once


GITHUB = 'https://api.github.com/search/repositories'
HN = 'https://hn.algolia.com/api/v1/search'


def fake_json(url):
    if url.startswith(GITHUB):
        return json.dumps({'items':[
            {'full_name':'acme/website-audit', 'description':'Open-source website accessibility SEO tools',
             'html_url':'https://github.com/acme/website-audit'},
            {'full_name':'acme/fake', 'description':'bad link',
             'html_url':'http://not-secure.invalid/repo'},
        ]}).encode()
    if url.startswith(HN):
        return json.dumps({'hits':[{'objectID':'12345','title':'Show HN: a free newsletter maker'},
                                    {'objectID':'oops','title':'Fake record'}]}).encode()
    raise AssertionError('Unexpected external endpoint '+url)


def fake_rss(url):
    assert url == 'https://github.blog/feed/'
    return b'<rss><channel><item><title>Software tools for developers</title><link>https://github.blog/news/tooling/</link></item></channel></rss>'


class OpportunityTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.home=Path(self.tmp.name)
        self.lab=OpportunityLab(self.home)

    def tearDown(self):
        self.tmp.cleanup()

    def test_all_methods_distinct_zero_cost_local_and_not_trading(self):
        keys=[m.key for m in METHODS]
        self.assertEqual(len(keys),39)
        self.assertEqual(len(keys),len(set(keys)))
        self.assertNotIn('trading',' '.join(m.lane.lower() for m in METHODS))
        self.assertTrue(all(m.deliverable and m.buyer and m.test and m.prerequisite for m in METHODS))

    def test_public_connectors_are_bounded_and_filter_untrusted_links(self):
        items, errors=collect_public(fetcher=fake_json,rss_fetcher=fake_rss,slot=0)
        self.assertEqual(errors,[])
        self.assertEqual(len(items),3)
        self.assertTrue(all(x['url'].startswith('https://') for x in items))
        self.assertTrue(any(x['source']=='github_blog_rss' for x in items))
        self.assertTrue(any('news.ycombinator.com/item' in x['url'] for x in items))
        self.assertFalse(any('not-secure' in x['url'] for x in items))

    def test_unapproved_host_and_oversized_source_blocked(self):
        self.assertFalse(trusted_url('https://github.com.attacker.example/x', {'github.com'}))
        self.assertFalse(trusted_url('http://github.com/a', {'github.com'}))
        with self.assertRaises(ValueError):
            source_json('https://evil.example/x','api.github.com',lambda url:b'{}')
        with self.assertRaises(ValueError):
            source_json('https://api.github.com/search/repositories','api.github.com',lambda url:b'0'*180001)

    def test_xml_entities_rejected_and_other_sources_continue(self):
        _, errors=collect_public(fetcher=fake_json, rss_fetcher=lambda url:b'<!DOCTYPE rss [<!ENTITY x "boom">]><rss/>')
        self.assertEqual(errors[0]['source'],'github_blog_rss')

    def test_offline_plan_no_network_and_court_allows_local_only(self):
        result=self.lab.scan(live=False,limit=3)
        self.assertEqual(result['public_observations_added'],0)
        self.assertEqual(len(result['new_plans']),3)
        self.assertTrue(all(i['verdict']=='NOT GUILTY' for i in result['new_plans']))
        self.assertTrue((self.home/'output'/'opportunity_research'/'RESEARCH_LIBRARY.md').is_file())
        files=list((self.home/'output'/'opportunity_research').glob('idea_*/VALIDATION_BRIEF.md'))
        self.assertEqual(len(files),3)
        self.assertIn('Zero verified buyers',files[0].read_text())
        guilty=adjudicate(Proposal('test','Publish a product without seller approval',action='publish_to_marketplace'))
        self.assertEqual(guilty.verdict,'GUILTY')
        self.assertTrue(self.lab.audit_valid())

    def test_sources_saved_deduped_and_linked_to_local_plan(self):
        observations,_=collect_public(fetcher=fake_json,rss_fetcher=fake_rss)
        self.assertEqual(self.lab.ingest(observations),3)
        self.assertEqual(self.lab.ingest(observations),0)
        result=self.lab.scan(live=False,limit=8)
        self.assertEqual(result['overview']['public_observations'],3)
        with self.lab.connect() as c:
            associated=c.execute('SELECT COUNT(*) FROM ideas WHERE source_id IS NOT NULL').fetchone()[0]
        self.assertGreaterEqual(associated,1)
        self.assertTrue(self.lab.audit_valid())

    def test_public_live_fetch_with_fixture_and_no_repeat(self):
        first=self.lab.scan(live=True,limit=2,fetcher=fake_json,rss_fetcher=fake_rss)
        second=self.lab.scan(live=True,limit=2,fetcher=fake_json,rss_fetcher=fake_rss)
        self.assertEqual(first['public_observations_added'],3)
        self.assertEqual(second['public_observations_added'],0)
        self.assertEqual(len(second['new_plans']),2)
        self.assertEqual(first['overview']['methods_catalogued'],39)

    def test_two_week_unlaunched_retirement_triggers_new_lanes(self):
        first=self.lab.scan(live=False,limit=1)
        plan=first['new_plans'][0]
        future=datetime.now(timezone.utc)+timedelta(days=15)
        old=self.lab.retire_due(now=future)
        self.assertEqual(old[0]['reason'],'UNLAUNCHED')
        second=self.lab.scan(live=False,limit=2)
        self.assertTrue(second['new_plans'])
        self.assertNotEqual(second['new_plans'][0]['method'],plan['method'])
        self.assertEqual(self.lab.rows()[-1]['status'],'RETIRED')
        self.assertTrue(self.lab.audit_valid())

    def test_metrics_reported_only_after_launch_and_retire_7_days(self):
        p=self.lab.scan(live=False,limit=1)['new_plans'][0]['id']
        with self.assertRaises(ValueError):self.lab.record(p,'view',5)
        with self.assertRaises(ValueError):self.lab.launch(p,'http://example.org')
        self.assertEqual(self.lab.launch(p,'https://example.org/valid'),'USER_REPORTED_LAUNCH_NOT_VERIFIED')
        self.lab.record(p,'view',100)
        # A simulated forward clock makes this an early-retirement review, not proof of demand.
        old=self.lab.retire_due(now=datetime.now(timezone.utc)+timedelta(days=8))
        self.assertEqual(old[0]['reason'],'LOW_ENGAGEMENT')
        self.assertTrue(self.lab.audit_valid())

    def test_reported_positive_prevents_14_day_retire(self):
        p=self.lab.scan(live=False,limit=1)['new_plans'][0]['id']
        self.lab.launch(p,'https://example.org/sale')
        self.lab.record(p,'sale',1,1000,100)
        self.assertEqual(self.lab.retire_due(now=datetime.now(timezone.utc)+timedelta(days=16)),[])
        self.assertTrue(self.lab.audit_valid())

    def test_detects_tampering_with_source_and_court_record(self):
        self.lab.ingest([{'source':'github_public_repos','title':'Website SEO tool','url':'https://github.com/example/foo'}])
        self.lab.scan(limit=1)
        with self.lab.connect() as c:
            c.execute('UPDATE observations SET title=? WHERE id=1',('Untruthful change',))
        self.assertFalse(self.lab.audit_valid())
        with self.assertRaises(RuntimeError):self.lab.scan(limit=1)

    def test_tampered_metrics_cannot_be_reported_as_sales(self):
        iid=self.lab.scan(limit=1)['new_plans'][0]['id']
        self.lab.launch(iid,'https://example.org/product')
        self.lab.record(iid,'sale',1,500,50)
        self.assertTrue(self.lab.audit_valid())
        with self.lab.connect() as c:
            c.execute('UPDATE ideas SET gross_cents=9999999 WHERE id=?',(iid,))
        self.assertFalse(self.lab.audit_valid())
        with self.assertRaises(RuntimeError):self.lab.scan(limit=1)

    def test_unclassified_sources_saved_not_automatically_executed(self):
        self.lab.ingest([{'source':'github_public_repos', 'title':'Nebulous zyxw qplmn',
                         'url':'https://github.com/example/unclassified', 'note':'unmapped'}])
        self.lab.scan(limit=1)
        text=(self.home/'output'/'opportunity_research'/'RESEARCH_LIBRARY.md').read_text()
        self.assertIn('Unclassified new signals',text)
        self.assertIn('Nebulous zyxw qplmn',text)
        self.assertNotIn('automatically installed',text)

    def test_fourteen_day_live_trial_retired_if_no_tracked_activity(self):
        iid=self.lab.scan(limit=1)['new_plans'][0]['id']
        self.lab.launch(iid,'https://example.org/launch')
        old=self.lab.retire_due(now=datetime.now(timezone.utc)+timedelta(days=15))
        self.assertEqual(old[0]['reason'],'INCONCLUSIVE')
        self.assertTrue(self.lab.audit_valid())

    def test_malicious_public_title_never_executes_code(self):
        sig=[{'source':'github_public_repos','title':'$(touch /tmp/farmbad) newsletter project',
              'url':'https://github.com/example/untrusted'}]
        self.lab.ingest(sig)
        self.lab.scan(limit=1)
        self.assertTrue(self.lab.audit_valid())
        self.assertFalse(Path('/tmp/farmbad').exists())

    def test_repeat_scan_not_duplicate_and_no_unlimited_expansion(self):
        for _ in range(5):
            self.lab.scan(limit=8)
        last=self.lab.scan(limit=8)
        self.assertEqual(last['new_plans'],[])
        self.assertEqual(last['overview']['experiment_plans'],39)

    def test_existing_runner_adds_research_not_made_up_sales(self):
        summary=run_once(self.home,live=False,max_cases=2)
        self.assertIn('opportunity_lab',summary)
        self.assertTrue(self.lab.audit_valid())
        self.assertTrue((self.home/'output'/'opportunity_research'/'RESEARCH_LIBRARY.md').exists())
        self.assertEqual(summary['opportunity_lab']['online_requested'],False)
        self.assertEqual(summary['opportunity_lab']['overview']['public_observations'],0)


if __name__=='__main__':unittest.main()
