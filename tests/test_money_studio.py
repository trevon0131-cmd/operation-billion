import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from botfarm.money_studio import MoneyStudio, METHODS, TOOLS, ACCOUNTS, options
from botfarm.creator_website_wing import Wing, write_video, local_ai_storyboard

class MoneyStudioTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.home=Path(self.temp.name)
        self.studio=MoneyStudio(self.home)
    def tearDown(self):self.temp.cleanup()
    def test_methods_diverse_and_trade_free(self):
        self.assertGreaterEqual(len(METHODS),16)
        self.assertIn('original_shorts',METHODS)
        self.assertIn('virtual_assistant',METHODS)
        self.assertNotIn('trading',METHODS)
        self.assertGreaterEqual(len(TOOLS),12)
        self.assertTrue(all(x['url'].startswith('https://github.com/') for x in TOOLS))
    def test_owner_only_account_checklist(self):
        self.assertTrue(all(a['connected'] is False for a in ACCOUNTS))
        self.assertFalse(any('password' in str(a).lower() for a in ACCOUNTS))
    def test_court_approved_kit_no_sale(self):
        result=self.studio.create('printable_planners','A planner for college life')
        self.assertEqual(result['verdict'],'NOT GUILTY')
        content=json.loads((Path(result['folder'])/'LAUNCH_PLAN.json').read_text())
        self.assertEqual(content['cost_limit_usd'],0)
        self.assertEqual(content['revenue_verified_usd'],0)
        self.assertEqual(content['publishing'],'NOT PERFORMED')
        self.assertFalse(content['market_demand_verified'])
        self.assertTrue(self.studio.audit_ok())
    def test_sample_video_using_shared_court(self):
        result=self.studio.create('original_shorts','Simple savings for students',True)
        self.assertEqual(result['sample']['status'],'local_only')
        metadata=json.loads((Path(result['sample']['folder'])/'metadata.json').read_text())
        self.assertEqual(metadata['topic'],'Simple savings for students')
        self.assertEqual(metadata['requested_topic'],'Simple savings for students')
        self.assertTrue(self.studio.audit_ok())
    def test_sample_website(self):
        result=self.studio.create('website_service','Fictional neighborhood bakery',True)
        self.assertEqual(result['sample']['kind'],'website')
        self.assertTrue((Path(result['sample']['folder'])/'index.html').exists())
        self.assertTrue(Wing(self.home).audit_valid())
    def test_existing_does_not_generate_again(self):
        a=self.studio.create('creator_thumbnails','Original series packaging')
        b=self.studio.create('creator_thumbnails','Original series packaging')
        self.assertEqual(b['status'],'existing')
        self.assertEqual(len(self.studio.report()['kits']),1)
    def test_tampering_blocks_new_kits(self):
        self.studio.create('creator_thumbnails','Original series packaging')
        with self.studio.connect() as con:
            con.execute("UPDATE kits SET topic='hacked'")
        self.assertFalse(self.studio.audit_ok())
        with self.assertRaises(RuntimeError):self.studio.create('resume_templates','New idea')
    def test_unsafe_topic_and_method_rejected(self):
        with self.assertRaises(ValueError):self.studio.create('not_found','Any business topic')
        with self.assertRaises(ValueError):self.studio.create('original_shorts','X'*101)
    def test_custom_video_topic_no_substitution(self):
        with tempfile.TemporaryDirectory() as d:
            v=write_video(Path(d),0,'short',requested_topic='How to find a book club')
            self.assertEqual(v['topic'],'How to find a book club')
            self.assertIn('How to find a book club',(Path(d)/'script.txt').read_text())
    def test_qwen_storyboard_disables_extra_thinking_and_bounded_output(self):
        reqs=[]
        def reader(req):
            reqs.append(json.loads(req.data))
            return json.dumps({'response':json.dumps(['Start this project','Create an example','Test the layout','Measure real results','Improve the draft'])}).encode()
        result=local_ai_storyboard('Budget basics',model='qwen3:8b',fetcher=reader)
        self.assertEqual(len(result),5)
        self.assertEqual(reqs[0]['think'],False)
        self.assertLessEqual(reqs[0]['options']['num_predict'],180)
    def test_daily_rotation_deduplicated_and_switches_method(self):
        from datetime import datetime, timezone, timedelta
        day=datetime(2026,10,20,tzinfo=timezone.utc)
        a=self.studio.daily_idea(day)
        b=self.studio.daily_idea(day)
        c=self.studio.daily_idea(day+timedelta(days=1))
        self.assertEqual(a['status'],'created')
        self.assertEqual(b['status'],'existing')
        self.assertEqual(c['status'],'created')
        self.assertNotEqual(a['fingerprint'],c['fingerprint'])
        self.assertTrue(self.studio.audit_ok())

    def test_reused_video_render_original_topic(self):
        wing=Wing(self.home)
        x=wing.create('short','Better recipes for new students',render=False)
        with patch('botfarm.creator_website_wing.shutil.which',return_value=None):
            wing.create('short','Better recipes for new students',render=True)
        meta=json.loads((Path(x['folder'])/'metadata.json').read_text())
        self.assertEqual(meta['topic'],'Better recipes for new students')

if __name__=='__main__': unittest.main()
