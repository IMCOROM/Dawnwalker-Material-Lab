"""Extend the local cache from a user's installed vanilla archive."""
import json
import os
import re
import subprocess
from pathlib import Path

def collect(project,archive,key,progress=lambda text:None):
    archive=Path(archive)
    if not archive.is_file():raise ValueError('Select the vanilla .utoc file')
    if not re.fullmatch(r'(?:0x)?[0-9a-fA-F]{64}',key):raise ValueError('Expected a 256-bit AES key')
    exe=project.app_dir/'Tools'/'retoc.exe'
    missing=[pkg for pkg,status in project.dependencies.items() if status=='missing']
    unresolved=[];copied=0
    for i,pkg in enumerate(missing):
        progress(f'Collecting shared assets {i+1}/{len(missing)}')
        entries=project.index.get(pkg,[])
        if not entries:unresolved.append(pkg);continue
        for e in entries:
            if not re.fullmatch('[0-9a-f]{24}',e['id']):raise ValueError('Invalid package index')
            out=project.library/'chunks'/e['id'];out.parent.mkdir(exist_ok=True)
            if out.exists():continue
            temp=out.with_suffix('.download')
            r=subprocess.run([str(exe),'-a',key,'get',str(archive),e['id'],str(temp)],capture_output=True,text=True,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
            if r.returncode:
                temp.unlink(missing_ok=True)
                raise ValueError('Could not extract '+pkg+'. Check the archive and key. Existing cache was preserved.')
            os.replace(temp,out);copied+=1
    project.collect_dependencies()
    (project.work/'import_report.json').write_text(json.dumps(project.report(),indent=2))
    return copied,unresolved
