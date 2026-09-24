"""Launch the actual EXE without a development Python/Tcl environment."""
import json
import os
import subprocess
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
exe = root / 'dist/Dawnwalker Material Lab/Dawnwalker Material Lab.exe'
env = os.environ.copy()
for key in ('PYTHONHOME', 'PYTHONPATH', 'TCL_LIBRARY', 'TK_LIBRARY'):
    env.pop(key, None)
windows = os.environ['SYSTEMROOT']
env['PATH'] = windows + r'\System32;' + windows
with tempfile.TemporaryDirectory() as directory:
    report = Path(directory) / 'result.json'
    result = subprocess.run([str(exe), '--self-test', str(report)], env=env, timeout=90)
    if result.returncode:
        raise RuntimeError(report.read_text() if report.exists() else 'EXE failed without a report')
    data = json.loads(report.read_text())
    if not data.get('ok') or not data.get('frozen') or not data.get('drag_drop'):
        raise RuntimeError(data)
    print(json.dumps(data, indent=2))
