import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from botfarm.viral_studio import FORMATS, _clean, _script_fallback, make, doctor
from botfarm.storage import Store

class ViralStudioTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.home=Path(self.tmp.name)
    def tearDown(self):
        self.tmp.cleanup()
    def test_all_five_formats_produce_original_scenes_and_pass_court(self):
        for fmt in FORMATS:
            with self.subTest(fmt=fmt):
                result=make(self.home,fmt,'A new idea for college students')
                self.assertEqual(result['court_verdict'],'NOT GUILTY')
                path=Path(result['folder'])
                self.assertEqual(len(list(path.glob('scene_*.png'))),5)
                self.assertEqual((path/'scene_01.png').read_bytes()[:8],b'\x89PNG\r\n\x1a\n')
                meta=json.loads((path/'metadata.json').read_text())
                self.assertFalse(meta['published'])
                self.assertFalse(meta['paid_services_called'])
                self.assertTrue(meta['no_external_content_copied'])
        self.assertTrue(Store(self.home).audit_valid())
    def test_no_copying_reddit_posts(self):
        text=' '.join(_script_fallback('fictional-reddit','New challenge'))
        self.assertIn('FICTIONAL STORY',text)
        self.assertNotIn('r/',text)
    def test_no_duplicate_or_court_spam(self):
        first=make(self.home,'fruit-story','School cafeteria')
        second=make(self.home,'fruit-story','School cafeteria')
        self.assertEqual(second['status'],'already_created')
        self.assertEqual(first['folder'],second['folder'])
        self.assertEqual(len(Store(self.home).cases()),1)
    def test_reject_invalid_format_or_topic(self):
        with self.assertRaises(ValueError):make(self.home,'copied-reddit','A valid subject')
        with self.assertRaises(ValueError):make(self.home,'fruit-story','')
        with self.assertRaises(ValueError):make(self.home,'fruit-story','x'*111)
    def test_ollama_fallback_is_reported(self):
        with patch('botfarm.viral_studio._local_ai',return_value=(None,'Timed out')):
            result=make(self.home,'micro-drama','Unexpected kindness',ai=True)
        meta=json.loads((Path(result['folder'])/'metadata.json').read_text())
        self.assertFalse(meta['ai_script_used'])
        self.assertEqual(meta['ai_note'],'Timed out')
    def test_missing_voice_assets_is_an_explicit_error(self):
        with self.assertRaises(RuntimeError):make(self.home,'fruit-story','Banana detective',narrate=True)
    def test_doctor_never_claims_auto_posting(self):
        data=doctor(self.home)
        self.assertFalse(data['automatic_posting'])
        self.assertTrue(data['no_paid_apis'])
        self.assertEqual(len(data['formats']),5)
    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'Optional FFmpeg unavailable')
    def test_actual_mp4_render_no_narration(self):
        result=make(self.home,'fruit-story','Orange detective mystery',render=True)
        video=Path(result['render']['path'])
        self.assertGreater(video.stat().st_size,3000)
        self.assertGreaterEqual(result['render']['seconds'],15)

if __name__=='__main__':unittest.main()

class ViralStudioExtraTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.home=Path(self.tmp.name)
    def tearDown(self):
        self.tmp.cleanup()
    def test_daily_studio_is_local_bounded_and_deduplicated(self):
        from botfarm.viral_studio import daily_studio
        from datetime import datetime, timezone
        when=datetime(2026,10,25,tzinfo=timezone.utc)
        with patch('botfarm.viral_studio.shutil.which',return_value=None):
            first=daily_studio(self.home,when)
            second=daily_studio(self.home,when)
        self.assertEqual(first['output']['status'],'created')
        self.assertEqual(second['output']['status'],'already_created')
        self.assertFalse(first['external_posted'])
        self.assertEqual(len(Store(self.home).cases()),1)
    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'Optional FFmpeg unavailable')
    def test_audio_longer_than_15_seconds_is_not_clipped(self):
        import wave
        from botfarm.viral_studio import _render
        from botfarm.viral_studio import _paint_png
        folder=self.home/'audio_project'
        folder.mkdir()
        source=[]
        for i in range(1,6):
            p=folder/f'scene_{i:02d}.png'
            _paint_png(p,'This is a test scene','fruit-story','Music quiz',i)
            source.append(p)
        wav=folder/'long.wav'
        with wave.open(str(wav),'wb') as w:
            w.setnchannels(1);w.setsampwidth(2);w.setframerate(8000)
            w.writeframes(b'\x00\x00'*(8000*20))
        result=_render(source,folder/'preview.mp4',audio=wav)
        self.assertGreater(result['seconds'],20)
        self.assertGreater(Path(result['path']).stat().st_size,3000)
