import contextlib
import importlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from python.pronunciation import generate, load_profile, ROOT
from python.preprocess import clean_text, convert_to_ipa
from python.get_ja_data import extract_readings
from python.model import generate as model_generate


class ToolsTest(unittest.TestCase):
    def test_reproducible_lexicon(self):
        profile = load_profile(ROOT / 'profiles/example.json')
        rows = generate(profile, 100, 7)
        self.assertEqual(rows, generate(profile, 100, 7))
        self.assertEqual(len({r['spelling'] for r in rows}), 100)
        self.assertEqual(len({r['ipa'] for r in rows}), 100)
        for row in rows:
            syllables = row['ipa'].split('.')
            self.assertTrue(syllables[-2].startswith('ˈ'))
            self.assertEqual(row['ipa'].count('ˈ'), 1)

    def test_exhausted_inventory_is_bounded(self):
        p = {'consonants': {'p': 'p'}, 'vowels': {'a': 'a'}, 'syllables': ['CV'],
             'syllable_count': [1, 1], 'stress': 'none'}
        with self.assertRaisesRegex(ValueError, 'Only 1'):
            generate(p, 2)

    def test_invalid_profile(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'profile.json'
            p = load_profile(ROOT / 'profiles/example.json')
            p['syllables'] = ['CCC']
            path.write_text(json.dumps(p))
            with self.assertRaises(ValueError):
                load_profile(path)

    def test_ipa_marks_survive(self):
        class Converter:
            def transliterate(self, text):
                return 't͡ʃãː'
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'words.txt'
            p.write_text('word\nword\n123\n!!!\n', encoding='utf-8')
            self.assertEqual(convert_to_ipa(p, Converter()), ['t͡ʃãː'])
        self.assertEqual(clean_text('abc12'), '')
        self.assertEqual(clean_text('https://example.com'), '')

    def test_unconverted_script_is_reported(self):
        class Converter:
            def transliterate(self, text):
                return 'ة'
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'words.txt'
            p.write_text('word')
            with self.assertRaisesRegex(ValueError, ':1: unconverted'):
                convert_to_ipa(p, Converter())

    def test_japanese_uses_readings(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'n5.csv'
            p.write_text('expression,reading\n漢字,かんじ\n漢字,かんじ\n空,\n', encoding='utf-8')
            self.assertEqual(extract_readings([p]), ['かんじ'])

    def test_model_validation_without_dependencies(self):
        for temp in (0, -1, float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                model_generate('a', temperature=temp)
        with self.assertRaises(ValueError):
            model_generate('☃')

    def test_imports_have_no_output(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            for name in ('model', 'get_data', 'get_ja_data', 'preprocess', 'process_ja', 'dataset'):
                importlib.reload(importlib.import_module('python.' + name))
        self.assertEqual(output.getvalue(), '')


if __name__ == '__main__':
    unittest.main()
