import json
import struct
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from botfarm.catalog import BOTS, BY_KEY
from botfarm.runner import run_once
from botfarm.workshop import make_artifact, make_sticker_png, svg_art, document_html, csv_product
from botfarm.storage import Store
from botfarm.__main__ import cents

class ProductsTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.home=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def test_roster_unique(self):
        self.assertEqual(len(BOTS),29)
        self.assertEqual(len(BY_KEY),len(BOTS))
    def test_all_products_construct(self):
        for bot in BOTS:
            path=make_artifact(self.home,bot,0,'a'*64,[])
            self.assertTrue((path/'metadata.json').exists(),bot.key)
            meta=json.loads((path/'metadata.json').read_text())
            self.assertIsNone(meta['revenue_usd'])
            self.assertEqual(meta['publication_status'],'DRAFT_ONLY')
            if bot.artifact=='svg': ET.fromstring((path/'product.svg').read_text())
            elif bot.artifact=='html': self.assertIn('<!doctype html>',(path/'product.html').read_text())
            elif bot.artifact=='csv':self.assertIn('USD',(path/'product.csv').read_text())
            else:self.assertIn('Original editable starter',(path/'product.md').read_text())
    def test_png_signature_dimensions(self):
        path=self.home/'test.png';make_sticker_png(path,0)
        data=path.read_bytes()
        self.assertEqual(data[:8],b'\x89PNG\r\n\x1a\n')
        self.assertEqual(struct.unpack('!II',data[16:24]),(640,640))
        self.assertGreater(len(data),1000)
    def test_evaluation_produces_drafts(self):
        a=run_once(self.home,live=False,max_cases=4)
        self.assertEqual(len(a['created']),4)
        self.assertTrue(all(x['verdict']=='NOT GUILTY' for x in a['created']))
        self.assertTrue(Store(self.home).audit_valid())
    def test_round_robin(self):
        a=run_once(self.home, max_cases=12)
        b=run_once(self.home, max_cases=12)
        self.assertEqual(len(a['created']),12)
        self.assertEqual(len(b['created']),12)
        self.assertNotEqual(a['created'][0]['bot'],b['created'][0]['bot'])
    def test_no_fictitious_revenue(self):
        self.assertEqual(Store(self.home).summary()['manual_gross_cents'],0)
    def test_dollar_parser(self):
        self.assertEqual(cents('0.015'),2)
        with self.assertRaises(ValueError):cents('nan')
        with self.assertRaises(ValueError):cents('-1')
    def test_max_cases_bounded(self):
        with self.assertRaises(ValueError):run_once(self.home,max_cases=100)
