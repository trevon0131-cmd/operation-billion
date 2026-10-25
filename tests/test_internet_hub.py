"""Internet access stays read-only, bounded and explicit. No real requests."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from botfarm.internet_hub import canonical_youtube_url, _clean_vtt, read_public_video, inspect_local_video, doctor


class InternetHubTests(unittest.TestCase):
    def test_canonicalizes_public_watch(self):
        self.assertEqual(canonical_youtube_url('https://youtu.be/dQw4w9WgXcQ?t=12'),
                         ('https://www.youtube.com/watch?v=dQw4w9WgXcQ','dQw4w9WgXcQ'))
        self.assertEqual(canonical_youtube_url('https://www.youtube.com/shorts/dQw4w9WgXcQ'),
                         ('https://www.youtube.com/watch?v=dQw4w9WgXcQ','dQw4w9WgXcQ'))

    def test_rejects_arbitrary_urls_and_injection(self):
        bad = ['http://youtu.be/dQw4w9WgXcQ','https://youtube.com@127.0.0.1/watch?v=dQw4w9WgXcQ',
               'https://127.0.0.1/watch?v=dQw4w9WgXcQ','https://evil.com/watch?v=dQw4w9WgXcQ',
               'file:///etc/passwd','https://youtube.com/watch?v=evil;whoami',
               'https://youtube.com:8443/watch?v=dQw4w9WgXcQ',
               'https://youtube.com/playlist?list=PLfoo','https://youtube.com/watch?v=x%0A',
               'https://youtube.com.evil.com/watch?v=dQw4w9WgXcQ']
        for url in bad:
            with self.subTest(url=url), self.assertRaises(ValueError):canonical_youtube_url(url)

    def test_captions_are_cleaned_and_bounded(self):
        raw='WEBVTT\n\n00:00:00.000 --> 00:00:03.000\n<c>Start a service</c>\nStart a service\n\n00:00:04 --> 00:00:05\nNot guaranteed sales'
        self.assertEqual(_clean_vtt(raw),'Start a service\nNot guaranteed sales')
        self.assertLessEqual(len(_clean_vtt('a'*40000)),35000)

    def test_yt_dlp_missing_has_clear_error(self):
        with tempfile.TemporaryDirectory() as d, patch('botfarm.internet_hub._ytdlp_command',return_value=None):
            with self.assertRaisesRegex(RuntimeError,'yt-dlp'):
                read_public_video(Path(d),'https://youtu.be/dQw4w9WgXcQ')

    def test_public_video_research_saves_source_and_transcript_without_media(self):
        class Result:
            def __init__(self,out='',returncode=0,err=''):
                self.stdout=out;self.returncode=returncode;self.stderr=err
        calls=[]
        def fake_run(cmd,timeout):
            calls.append(cmd)
            self.assertNotIn('--cookies-from-browser',cmd)
            self.assertIn('--skip-download',cmd)
            self.assertIn('--no-playlist',cmd)
            if '--dump-single-json' in cmd:
                return Result(json.dumps({'title':'My free tools','duration':25,'view_count':5,'uploader':'Creator'}))
            output=Path(cmd[cmd.index('-o')+1])
            outpath=output.parent/'dQw4w9WgXcQ.en.vtt'
            outpath.write_text('WEBVTT\n00:01 --> 00:02\nAn idea is not a sale',encoding='utf-8')
            return Result()
        with tempfile.TemporaryDirectory() as d, patch('botfarm.internet_hub._ytdlp_command',return_value=['yt-dlp']), patch('botfarm.internet_hub._run',side_effect=fake_run):
            result=read_public_video(Path(d),'https://youtu.be/dQw4w9WgXcQ')
            self.assertTrue(result['transcript_available'])
            self.assertTrue((Path(result['saved_folder'])/'research_brief.md').is_file())
            self.assertIn('An idea is not a sale',(Path(result['saved_folder'])/'transcript.txt').read_text())
            self.assertFalse(result['published_or_sold'])
            self.assertEqual(len(calls),2)

    def test_subtitle_missing_works_transparently(self):
        class R:
            returncode=0;stderr='';stdout='{"title":"No captions"}'
        with tempfile.TemporaryDirectory() as d, patch('botfarm.internet_hub._ytdlp_command',return_value=['yt-dlp']),patch('botfarm.internet_hub._run',return_value=R()):
            result=read_public_video(Path(d),'https://youtu.be/dQw4w9WgXcQ',ai=True)
            self.assertFalse(result['transcript_available'])
            self.assertIn('No subtitles available',(Path(result['saved_folder'])/'research_brief.md').read_text())

    def test_doctor_does_not_install(self):
        with patch('botfarm.internet_hub._ytdlp_command',return_value=None),patch('botfarm.internet_hub.shutil.which',return_value=None):
            report=doctor()
            self.assertFalse(report['agent_reach_installed'])
            self.assertFalse(report['social_account_access']!='disabled; never auto-imports browser cookies')

    def test_local_frames_need_owner_file_and_ffmpeg(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'video.mp4';path.write_bytes(b'fake')
            with patch('botfarm.internet_hub.shutil.which',return_value=None):
                with self.assertRaisesRegex(RuntimeError,'FFmpeg'):
                    inspect_local_video(Path(d),str(path))
            with self.assertRaises(ValueError):inspect_local_video(Path(d),str(Path(d)/'not_found.mp4'))

if __name__=='__main__':unittest.main()

class InternetQueueTests(unittest.TestCase):
    def test_queue_deduplicates_and_stays_offline_by_default(self):
        from botfarm.internet_hub import queue_video, process_video_queue
        with tempfile.TemporaryDirectory() as d:
            home=Path(d)
            queue_video(home,'https://youtu.be/dQw4w9WgXcQ')
            queue_video(home,'https://www.youtube.com/watch?v=dQw4w9WgXcQ')
            with patch('botfarm.internet_hub.read_public_video') as mock:
                outcome=process_video_queue(home)
                self.assertFalse(outcome['network_called'])
                mock.assert_not_called()
            self.assertEqual(outcome['queue_count'],1)

    def test_queue_processes_one_at_a_time_when_live(self):
        from botfarm.internet_hub import queue_video, process_video_queue,show_queue
        with tempfile.TemporaryDirectory() as d:
            home=Path(d)
            queue_video(home,'https://youtu.be/dQw4w9WgXcQ')
            queue_video(home,'https://youtu.be/jNQXAC9IVRw')
            with patch('botfarm.internet_hub._ytdlp_command',return_value=['yt-dlp']), \
                 patch('botfarm.internet_hub.read_public_video',return_value={'saved_folder':'sample'}) as mock:
                outcome=process_video_queue(home,live=True)
                self.assertEqual(mock.call_count,1)
                self.assertEqual(outcome['pending'],1)
                self.assertEqual(sum(x['status']=='researched' for x in show_queue(home)['queue']),1)

class AgentReachOptionalTests(unittest.TestCase):
    def test_search_missing_tool_fails_safe(self):
        from botfarm.internet_hub import agent_reach_youtube_search
        with tempfile.TemporaryDirectory() as d,patch('botfarm.internet_hub.shutil.which',return_value=None):
            with self.assertRaisesRegex(RuntimeError,'not installed'):
                agent_reach_youtube_search(Path(d),'free tutorial')

    def test_only_public_youtube_subcommand_is_launched(self):
        from botfarm.internet_hub import agent_reach_youtube_search
        class R:
            returncode=0;stdout='{"results":[]}';stderr=''
        with tempfile.TemporaryDirectory() as d, patch('botfarm.internet_hub.shutil.which',return_value='agent-reach.exe'),patch('botfarm.internet_hub._run',return_value=R()) as run:
            result=agent_reach_youtube_search(Path(d),'small business websites')
            self.assertTrue(Path(result['saved_file']).is_file())
            self.assertEqual(run.call_args.args[0],['agent-reach.exe','youtube','search','small business websites'])
            self.assertTrue(result['unverified_research'])
