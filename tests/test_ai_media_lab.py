import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from botfarm.ai_media_lab import latest_draft, polish, report
from botfarm.creator_website_wing import write_video


class FreeMediaUpgradeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name)
        self.folder = self.home/'output'/'expansion_wing'/'short'/'draft01'
        write_video(self.folder, 1, 'short', requested_topic='Budget tips for students')

    def tearDown(self):
        self.temp.cleanup()

    def test_three_suggested_repositories_listed(self):
        found = report()
        names = [x['name'] for x in found['catalogued_sources']]
        for name in ('zebbern/no-cost-ai','12britz/awesome-free-models','Anil-matcha/Open-Generative-AI'):
            self.assertIn(name,names)
        self.assertFalse(found['conditions']['third_party_code_installed'])
        self.assertFalse(found['conditions']['AI_generated_footage_built_in'])

    def test_newest_folder_detected(self):
        self.assertEqual(self.folder, latest_draft(self.home))

    def test_no_video_folder_refuses(self):
        with self.assertRaises(ValueError):latest_draft(self.home/'unused')

    def test_media_must_be_draft(self):
        with self.assertRaises(ValueError):polish(self.home)
        (self.folder/'metadata.json').write_text('{}',encoding='utf-8')
        with self.assertRaises(ValueError):polish(self.folder)

    def test_import_requires_rights_confirmation(self):
        with self.assertRaises(ValueError):polish(self.folder, images=self.folder)
        with self.assertRaises(ValueError):polish(self.folder, audio='private.wav')

    def test_bad_images_refused_without_running(self):
        images=self.home/'images'
        images.mkdir()
        for i in range(1,6):
            (images/f'scene_{i:02d}.png').write_bytes(b'not a png')
        with self.assertRaises(ValueError):polish(self.folder,images=images,rights_confirmed=True)

    def test_invalid_dimensions_refused(self):
        with self.assertRaises(ValueError):polish(self.folder,width=253)

    def test_missing_ffmpeg_refused(self):
        with patch('botfarm.ai_media_lab.shutil.which',return_value=None):
            with self.assertRaises(RuntimeError):polish(self.folder)

    def test_import_owned_artwork_produces_provenance(self):
        if not shutil.which('ffmpeg'):
            self.skipTest('Optional FFmpeg is not installed on this machine')
        from botfarm.creator_website_wing import png_slide
        images=self.home/'my_owned_images'
        images.mkdir()
        for i in range(1,6):
            png_slide(images/f'scene_{i:02d}.png', f'Original idea {i}', 'Licensed locally',True)
        result=polish(self.folder,images=images,rights_confirmed=True,width=270,fps=12)
        self.assertTrue(result['ai_visuals_imported'])
        provenance=json.loads(Path(result['provenance']).read_text(encoding='utf-8'))
        self.assertTrue(provenance['rights_confirmed_by_owner_for_imported_media'])
        self.assertNotIn('cloud',provenance['render'])

    def test_free_cpu_motion_render_and_provenance(self):
        if not shutil.which('ffmpeg'):
            self.skipTest('Optional FFmpeg is not installed on this machine')
        result=polish(self.folder,width=270,fps=12)
        output=Path(result['video'])
        self.assertTrue(output.is_file())
        self.assertGreater(output.stat().st_size,3000)
        metadata=json.loads(Path(result['provenance']).read_text(encoding='utf-8'))
        self.assertEqual(metadata['render']['duration_seconds'],15)
        self.assertEqual(metadata['verified_income'],0)
        self.assertFalse(metadata['generative_video_model_executed'])
        self.assertEqual(len(metadata['source_images']),5)
        self.assertFalse(metadata['published'])
        self.assertEqual(json.loads((self.folder/'metadata.json').read_text())['requested_topic'], 'Budget tips for students')


if __name__=='__main__':unittest.main()
