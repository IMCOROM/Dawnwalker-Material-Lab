import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from Material_Lab import output_stem
from color_controls import hex_to_linear_rgb, linear_rgb_to_hex

class SourceTests(unittest.TestCase):
    def test_release_source_identity(self):
        manifest = json.loads((ROOT / 'review/source-sha256.json').read_text())
        for name, expected in manifest.items():
            self.assertEqual(hashlib.sha256((ROOT / 'src' / name).read_bytes()).hexdigest(), expected, name)

    def test_output_names_and_path_rejection(self):
        for name in ('LEGS', 'zzz_LEGS_P', 'zzz_zzz_LEGS_P_P'):
            self.assertEqual(output_stem(name), 'zzz_LEGS_P')
        for name in ('', '../file', 'a/b', 'a\\b', 'x:y'):
            with self.assertRaises(ValueError):
                output_stem(name)

    def test_srgb_roundtrip(self):
        for color in ('#000000', '#ffffff', '#00ffff', '#804020'):
            self.assertEqual(linear_rgb_to_hex(hex_to_linear_rgb(color)).lower(), color)

if __name__ == '__main__':
    unittest.main()
