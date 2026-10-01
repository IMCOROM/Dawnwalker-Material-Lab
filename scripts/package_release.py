"""Package a clean portable build and reject nested ZIPs."""
import hashlib
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
base = root / 'dist/Dawnwalker Material Lab'
if not (base / 'Dawnwalker Material Lab.exe').is_file():
    raise SystemExit('Build the executable first.')
files = []
for f in sorted(base.rglob('*')):
    if not f.is_file():
        continue
    rel = f.relative_to(base)
    if rel.parts[:2] == ('AssetLibrary', 'Exports'):
        continue
    if rel.parts[0] in ('Projects', '__pycache__') or rel.name in ('recent_garments.json', 'appearance_settings.json'):
        continue
    if f.suffix.lower() == '.zip':
        raise ValueError('Nested ZIP detected: ' + str(rel))
    files.append(f)
out = root / 'release'
out.mkdir(exist_ok=True)
full = (base / 'AssetLibrary/package_index.json').is_file() and (base / 'Tools/retoc.exe').is_file()
name = 'Dawnwalker_Material_Lab_v0.19_' + ('Full' if full else 'AppOnly') + '_Rebuilt.zip'
archive = out / name
with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for f in files:
        z.write(f, Path(base.name) / f.relative_to(base))
with zipfile.ZipFile(archive) as z:
    if z.testzip() is not None:
        raise RuntimeError('ZIP verification failed')
with archive.open('rb') as stream:
    digest = hashlib.file_digest(stream, 'sha256').hexdigest()
Path(str(archive) + '.sha256').write_text(digest + '  ' + archive.name + '\n')
print(archive)
