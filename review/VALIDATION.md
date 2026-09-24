# Local validation: 2026-09-24

- All seven application modules match the source hashes recorded for v0.19.
- Three unittest checks passed: source identity, output naming/path rejection,
  and linear/sRGB color round trips.
- Rebuilt the EXE from this repository using MaterialLab.spec and the pinned local
  build environment (Python 3.12.14, PyInstaller 6.22.3, Tcl/Tk 8.6.12).
- Standalone runtime checks passed for app-only and full-resource builds with
  development Python/Tcl variables removed and Windows-only PATH.
- TkDnD reported 2.10.2. The full build found the asset index and build tool.
- Resource assembly verified 1,643 files against the submitted release manifest.
- Full rebuilt package passed CRC verification and the no-nested-ZIP check.
- build.ps1 passed PowerShell syntax parsing. Its individual build commands were
  exercised using the already-installed pinned environment; a fresh internet
  dependency install through the wrapper was not repeated during this validation.

This is a functional build check, not an independent malware audit, a clean-VM
compatibility test, or an in-game test of every editable material.
