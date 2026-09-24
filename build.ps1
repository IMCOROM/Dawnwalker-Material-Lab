param([string]$Python = 'py', [string]$ResourceDirectory = '')
$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    if (!(Test-Path '.venv/Scripts/python.exe')) {
        if ($Python -eq 'py') { & py -3.12 -m venv .venv }
        else { & $Python -m venv .venv }
        if ($LASTEXITCODE -ne 0) { throw 'Install Python 3.12 x64 with Tcl/Tk and venv, then retry.' }
    }
    $venvPython = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
    & $venvPython -m pip install -r requirements-build.txt
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
    & $venvPython -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) { throw 'Source checks failed.' }
    & $venvPython -m PyInstaller --noconfirm --distpath dist --workpath build MaterialLab.spec
    if ($LASTEXITCODE -ne 0) { throw 'Executable build failed.' }
    if ($ResourceDirectory) {
        & $venvPython scripts/assemble.py --resources $ResourceDirectory
        if ($LASTEXITCODE -ne 0) { throw 'Resource assembly failed.' }
    }
    & $venvPython scripts/check_runtime.py
    if ($LASTEXITCODE -ne 0) { throw 'Standalone runtime check failed.' }
    & $venvPython scripts/package_release.py
    if ($LASTEXITCODE -ne 0) { throw 'Packaging failed.' }
} finally { Pop-Location }
