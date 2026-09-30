"""Copy only verified non-code resources from the reviewed portable release."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--resources', required=True,
                        help='Extracted v0.21 NoNestedZIP folder containing AssetLibrary and Tools')
    args = parser.parse_args()
    source = Path(args.resources).resolve()
    dest = ROOT / 'dist' / 'Dawnwalker Material Lab'
    if not (dest / 'Dawnwalker Material Lab.exe').is_file():
        raise ValueError('Build the executable first.')
    manifest = json.loads((ROOT / 'review/release-manifest.json').read_text())
    entries = [e for e in manifest['files'] if e['path'].startswith(('AssetLibrary/', 'Tools/', 'Licenses/')) or e['path'] == 'START HERE.txt']
    # Validate everything before copying. Never import user projects or runtime binaries.
    for entry in entries:
        f = source / entry['path']
        if not f.resolve().is_relative_to(source):
            raise ValueError('Resource path outside source')
        with f.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        if digest != entry['sha256']:
            raise ValueError('Resource differs from reviewed release: ' + entry['path'])
    for entry in entries:
        target = dest / entry['path']
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / entry['path'], target)
    print('Verified and copied', len(entries), 'resource files.')

if __name__ == '__main__':
    main()
