import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class IdParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids=[]
    def handle_starttag(self, tag, attrs):
        self.ids.extend(value for key,value in attrs if key=='id')

class MockupRebuildTests(unittest.TestCase):
    def test_sections_and_unique_ids(self):
        html=(ROOT/'web/index.html').read_text()
        parser=IdParser()
        parser.feed(html)
        self.assertEqual(len(parser.ids),len(set(parser.ids)))
        for required in ('page-overview','overview-disks','overview-containers',
                         'overview-vms','overview-networks','overview-catalog','overview-stacks',
                         'page-catalog','page-billing','cpu-chart'):
            self.assertIn(required,parser.ids)

    def test_no_fake_values_from_mockup(self):
        html=(ROOT/'web/index.html').read_text()
        self.assertNotIn('192.168.1.100',html)
        self.assertNotIn('124,80',html)
        self.assertNotIn('12.4 TB',html)
        self.assertNotIn('Windows 11',html)
        self.assertIn('—',html)
        self.assertIn('leitura',html)

    def test_read_only_browser(self):
        js=(ROOT/'web/app.js').read_text()
        self.assertIn('/api/overview',js)
        self.assertIn('Promise.allSettled',js)
        self.assertNotIn('fetch("/var/run/docker.sock"',js)
        self.assertNotIn('docker run',js)

    def test_self_hosted_hero(self):
        css=(ROOT/'web/style.css').read_text()
        self.assertIn('/hero.webp',css)
        self.assertTrue((ROOT/'web/hero.webp').is_file())

if __name__=='__main__':
    unittest.main()
