# Build on Windows

## Requirements

Use Windows x64 with **Python 3.12 x64**, including Tcl/Tk, pip and venv. A normal
[python.org Windows installation](https://www.python.org/downloads/windows/)
provides these components. Do not use the embeddable Python distribution without
adding Tk. These are developer requirements; users of the resulting EXE need no
Python installation.

The original artifact was built on Windows 11 with Python **3.12.14**, Tcl/Tk
**8.6.12**, PyInstaller **6.22.3**, and tkinterdnd2 **0.6.3** (TkDnD reported
**2.10.2** at runtime). All installed build package versions are pinned in
`requirements-build.txt`. Other Python patch versions can produce different
binaries; do not expect a byte-identical EXE or ZIP from a different environment.

## Build the application from source

Open PowerShell in the repository root and run:

```powershell
.\build.ps1
```

If the Python launcher is unavailable, specify your Python executable:

```powershell
.\build.ps1 -Python 'C:\Path\To\Python312\python.exe'
```

If PowerShell blocks local scripts, review the script first. You can run the
manual commands below without changing the machine's execution policy.

The script creates a local `.venv`, installs pinned dependencies from PyPI, runs
source tests, builds the EXE, tests it with development runtime variables removed,
and creates `release/Dawnwalker_Material_Lab_v0.21_AppOnly_Rebuilt.zip`.
It uses no administrator privileges. Use a writable checkout folder.

Result: `dist/Dawnwalker Material Lab/Dawnwalker Material Lab.exe`.
Keep `_internal` beside it. An app-only build can open the UI, but does not include
the shared asset cache, RETOC, decompression DLL or companion PAK needed for the
full editing/build workflow.

## Assemble the full portable edition

Extract the submitted `Dawnwalker_Material_Lab_v0.21_Full_Rebuilt.zip` to a
separate directory. Supply the folder that directly contains `AssetLibrary` and
`Tools` (not the outer ZIP or its parent):

```powershell
.\build.ps1 -ResourceDirectory 'C:\Review\Dawnwalker Material Lab'
```

`scripts/assemble.py` validates each copied resource against the original release
manifest **before** copying anything. It copies only `AssetLibrary`, `Tools`,
`Licenses`, and `START HERE.txt`. It does not reuse the old EXE, `_internal`, user
projects, appearance preferences, or recent paths. The runtime is rebuilt from
source. Output is `release/Dawnwalker_Material_Lab_v0.21_Full_Rebuilt.zip`.

The original resource pack is still needed to reproduce the *full* content: this
repository does not contain the game asset binaries or Oodle's source. See
DEPENDENCIES.md. The application executable can be reviewed and built independently.

## Equivalent manual commands

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --distpath dist --workpath build MaterialLab.spec
# Optional: assemble resources for the full edition
.\.venv\Scripts\python.exe scripts/assemble.py --resources 'C:\Review\Dawnwalker Material Lab'
.\.venv\Scripts\python.exe scripts/check_runtime.py
.\.venv\Scripts\python.exe scripts/package_release.py
```

Run source directly with `.\.venv\Scripts\python.exe src/desktop_main.py`.
In source mode the app uses `src/` as its data root; in frozen mode it uses the
EXE's directory. Put optional `AssetLibrary` and `Tools` there for source-mode
editing. Generated `Projects` and settings are local to that same directory.

## Verification

The build runtime check launches the real EXE with `PYTHONHOME`, `PYTHONPATH`,
`TCL_LIBRARY` and `TK_LIBRARY` removed and a Windows-only PATH. It checks frozen
execution, Tk startup, and TkDnD loading. `asset_library` and `build_tool` may be
false for an app-only build; they should be true for the full build.

Optional import smoke test with your own supported FModel export:

```powershell
$exe = (Resolve-Path '.\dist\Dawnwalker Material Lab\Dawnwalker Material Lab.exe').Path
$p = Start-Process -FilePath $exe -ArgumentList '--self-test "C:\Review\smoke.json" "C:\Exports\ItemFolder"' -Wait -PassThru
Get-Content 'C:\Review\smoke.json'
$p.ExitCode
```

The optional import test creates a project and recent-path setting in the build
folder. Packaging excludes these. A successful import is not an in-game test.
The previously distributed EXE passed a 23-control weapon import and a 12-control
clothing fixture import on the development machine. Manual mod testing remains
dependent on an appropriate game version and exported assets.

`package_release.py` rejects any nested `.zip` file, verifies ZIP CRCs and writes
a SHA-256 sidecar. No code signing certificate or installer is required or included.
The build spec retains the original `upx=True` setting, but UPX was not installed
for the original build. Leave UPX off PATH to match that condition.

Build in a fresh checkout for review. PyInstaller's `--noconfirm` may replace its
own prior output; do not keep user projects in the `dist` build directory.
