"""Bounded, public-only market-signal collector. Signals are NEVER evidence of sales."""
import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path

class Research:
    def __init__(self, home: Path):
        self.cache = home / 'data' / 'signals_cache.json'
        self.cache.parent.mkdir(parents=True, exist_ok=True)

    def collect(self, online=False):
        if not online:
            return [{'source':'offline', 'title':'No external market research performed',
                     'url':'', 'confidence':'none', 'at':0}]
        try:
            if self.cache.exists() and time.time() - self.cache.stat().st_mtime < 1800:
                return json.loads(self.cache.read_text(encoding='utf-8'))
        except (OSError, json.JSONDecodeError):
            pass
        signals = []
        # Two unauthenticated, public sources. No HTML scraping, browser login, or proxies.
        endpoints = [
            ('GitHub', 'https://api.github.com/search/repositories?' + urllib.parse.urlencode({
                'q':'digital product template generator', 'sort':'updated', 'order':'desc', 'per_page':'3'})),
            ('Hacker News', 'https://hn.algolia.com/api/v1/search?' + urllib.parse.urlencode({
                'query':'printable template', 'tags':'story', 'hitsPerPage':'3'})),
        ]
        for source, url in endpoints:
            try:
                request = urllib.request.Request(url, headers={
                    'User-Agent':'ZeroCostBotFarm/0.1 (research only)', 'Accept':'application/json'})
                with urllib.request.urlopen(request, timeout=8) as response:
                    # Cap bytes; no unbounded downloads.
                    raw = response.read(150_001)
                if len(raw) > 150_000:
                    raise ValueError('Response exceeded limit')
                data = json.loads(raw)
                rows = data.get('items', []) if source == 'GitHub' else data.get('hits', [])
                for row in rows[:3]:
                    title = (row.get('full_name') or row.get('title') or '').strip()
                    link = row.get('html_url') or row.get('url') or row.get('story_url') or ''
                    if not title or not str(link).startswith('https://'):
                        continue
                    signals.append({'source':source, 'title':title[:130], 'url':link,
                                    'confidence':'weak-interest-signal-only', 'at':int(time.time())})
            except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
                signals.append({'source':source, 'title':f'No data: {type(exc).__name__}',
                                'url':'', 'confidence':'none', 'at':int(time.time())})
        # Cache refresh even for failures to avoid hammering public services.
        tmp = self.cache.with_suffix('.tmp')
        tmp.write_text(json.dumps(signals, indent=2), encoding='utf-8')
        os.replace(tmp, self.cache)
        return signals
