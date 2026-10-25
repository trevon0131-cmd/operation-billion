"""New video/web factory acceptance tests: no payments, no publication, robust court."""
import json
import re
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from botfarm.creator_website_wing import Wing,TOOLS,TOPICS,write_video,write_site,png_slide,safe_text

class CreatorWebsiteWingTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.home=Path(self.tmp.name);self.wing=Wing(self.home)
    def tearDown(self):self.tmp.cleanup()
    def test_short_creates_real_png_subtitle_and_script(self):
        v=self.wing.create('short','Create an educational short')
        self.assertEqual(v['verdict'],'NOT GUILTY')
        out=Path(v['folder']);self.assertTrue((out/'captions.srt').exists())
        pngs=sorted(out.glob('scene_*.png'));self.assertEqual(len(pngs),5)
        self.assertTrue(all(p.read_bytes().startswith(b'\x89PNG\r\n\x1a\n') for p in pngs))
        self.assertIn('00:00:03,000',(out/'captions.srt').read_text())
        self.assertNotIn('guaranteed',(out/'metadata.json').read_text().lower())
        self.assertTrue(self.wing.audit_valid())
    def test_long_video_landscape(self):
        v=self.wing.create('youtube','Make a simple budget')
        data=(Path(v['folder'])/'scene_01.png').read_bytes()
        self.assertEqual(int.from_bytes(data[16:20],'big'),960)
        self.assertEqual(int.from_bytes(data[20:24],'big'),540)
    def test_business_site_uses_safe_escaped_html(self):
        v=self.wing.create('website','cafe <script>alert(1)</script>')
        content=(Path(v['folder'])/'index.html').read_text()
        self.assertIn('&lt;script&gt;',content);self.assertNotIn('<script>',content)
        self.assertIn('FICTIONAL DEMO',content)
        self.assertIn('name="viewport"',content)
        self.assertIn('No form or payment processor',content)
    def test_no_customer_emails_or_fake_performance(self):
        v=self.wing.create('website','local cafe')
        folder=Path(v['folder']);outreach=(folder/'outreach_UNSENT.txt').read_text()
        self.assertIn('[YOUR VALID POSTAL ADDRESS]',outreach)
        self.assertIn('[WORKING CONTACT AND OPT-OUT METHOD]',outreach)
        self.assertIn('No email has been sent',outreach)
        self.assertEqual(self.wing.overview()['sales_verified'],0)
        self.assertEqual(self.wing.overview()['outreach_sent'],0)
    def test_idempotence_and_unsafe_action_separate(self):
        safe=self.wing.create('short','Organize a job search')
        again=self.wing.create('short','Organize a job search')
        blocked=self.wing.create('short','Organize a job search',unsafe=True)
        self.assertEqual(again['status'],'existing')
        self.assertEqual(blocked['verdict'],'GUILTY')
        self.assertEqual(blocked['folder'],None)
        self.assertNotEqual(safe['fingerprint'],blocked['fingerprint'])
        self.assertTrue(self.wing.audit_valid())
    def test_tampered_verdict_cannot_create_more_samples(self):
        self.wing.create('website','local cafe')
        with self.wing.connect() as con:
            con.execute("UPDATE drafts SET verdict='GUILTY'")
        self.assertFalse(self.wing.audit_valid())
        with self.assertRaises(RuntimeError): self.wing.create('short','Organize a job search')
    def test_tampered_audit_chain_blocks(self):
        self.wing.create('website','local cafe')
        with self.wing.connect() as con:
            con.execute("UPDATE audit SET payload='{}'")
        self.assertFalse(self.wing.audit_valid())
    def test_tool_registry_is_sourced_and_no_paid_cloud_auto_calls(self):
        self.assertGreaterEqual(len(TOOLS),10)
        self.assertTrue(all(x['url'].startswith('https://github.com/') for x in TOOLS))
        self.assertTrue(all(x['mode'] in ('research_only','optional_local') for x in TOOLS))
    def test_autopilot_creates_both_tracks_once(self):
        with patch('botfarm.creator_website_wing.shutil.which',return_value=None):
            first=self.wing.cycle();second=self.wing.cycle()
        self.assertIn('short',first);self.assertIn('site',first)
        self.assertEqual(first['short']['status'],'created')
        self.assertEqual(second['short']['status'],'existing')
        self.assertEqual(second['site']['status'],'existing')
        self.assertTrue(self.wing.audit_valid())
    def test_no_trend_means_no_false_trending_claim(self):
        self.assertIsNone(self.wing.find_topic_evidence())
        with patch('botfarm.creator_website_wing.shutil.which',return_value=None):
            v=self.wing.cycle()
        self.assertEqual(v['content_signal']['kind'],'no_relevant_current_trend')
    def test_trend_readonly_connection_is_explicitly_closed(self):
        from unittest.mock import MagicMock
        from datetime import datetime, timezone
        db=self.home/'data'/'trend_engine.sqlite3'
        db.touch()
        connection=MagicMock()
        connection.execute.return_value.fetchall.return_value=[]
        with patch('botfarm.creator_website_wing.sqlite3.connect',return_value=connection):
            self.assertIsNone(self.wing.find_topic_evidence(now=datetime(2026,10,20,tzinfo=timezone.utc)))
        connection.close.assert_called_once()

        failed=MagicMock()
        failed.execute.side_effect=sqlite3.DatabaseError('invalid read only database')
        with patch('botfarm.creator_website_wing.sqlite3.connect',return_value=failed):
            self.assertIsNone(self.wing.find_topic_evidence())
        failed.close.assert_called_once()

    def test_optional_local_model_validated_not_executed(self):
        from botfarm.creator_website_wing import local_ai_storyboard
        response=json.dumps({'response':json.dumps(['One helpful idea','Explain the question','Check the facts','Show a useful example','Summarize honestly'])}).encode()
        words=local_ai_storyboard('Create an educational short',fetcher=lambda req:response)
        self.assertEqual(len(words),5)
        with self.assertRaises(ValueError):local_ai_storyboard('x',fetcher=lambda req:b'{"response":"[]"}')
        with self.assertRaises(ValueError):local_ai_storyboard('x',model='../../&&bad',fetcher=lambda req:response)

    def test_optional_local_ai_missing_graceful_fallback(self):
        with patch('botfarm.creator_website_wing.local_ai_storyboard',side_effect=OSError('not installed')):
            result=self.wing.create('short','Create an educational short',use_ai=True)
        self.assertEqual(result['verdict'],'NOT GUILTY')
        self.assertTrue((Path(result['folder'])/'AI_MODEL_STATUS.txt').exists())

    def test_bad_inputs_rejected(self):
        for val in ['', 'X'*101, '\x01oops']:
            with self.assertRaises(ValueError):safe_text(val)
        for mode in ['publish','post','steal','ad_campaign']:
            with self.assertRaises(ValueError):self.wing.create(mode,'local cafe')
        with self.assertRaises(ValueError):self.wing.create('short','hi',variant=100)
    def test_ffmpeg_missing_uses_static_files(self):
        with tempfile.TemporaryDirectory() as t:
            with patch('botfarm.creator_website_wing.shutil.which',return_value=None):
                result=write_video(Path(t),0,'short',render_mp4=True)
            self.assertFalse(result['mp4_rendered'])
            self.assertEqual(len(list(Path(t).glob('scene_*.png'))),5)
    def test_optional_mp4_when_ffmpeg_installed(self):
        import shutil
        if not shutil.which('ffmpeg'):self.skipTest('FFmpeg optional and not installed')
        v=self.wing.create('short','Make a simple budget',render=True)
        self.assertTrue((Path(v['folder'])/'preview.mp4').exists())
        self.assertGreater((Path(v['folder'])/'preview.mp4').stat().st_size,5000)

if __name__=='__main__':unittest.main()
