# Dependencies and provenance

## Application build/runtime

| Component | Recorded version | Source / documentation |
| --- | --- | --- |
| CPython | 3.12.14 in original build | https://github.com/python/cpython ; https://www.python.org/ |
| Tcl/Tk | 8.6.12 in original runtime | https://www.tcl.tk/software/tcltk/ |
| PyInstaller | 6.22.3 | https://github.com/pyinstaller/pyinstaller/tree/v6.22.3 ; https://pyinstaller.org/en/v6.22.3/license.html |
| tkinterdnd2 | 0.6.3 | https://pypi.org/project/tkinterdnd2/0.6.3/ ; https://github.com/Eliav2/tkinterdnd2 |
| TkDnD native extension | Runtime reports 2.10.2 | https://github.com/petasis/tkdnd (bundled by tkinterdnd2) |
| RETOC CLI | `retoc_cli 0.1.5` | https://github.com/trumank/retoc/tree/v0.1.5 ; https://github.com/trumank/retoc/releases/tag/v0.1.5 |

Transitive build dependencies are pinned in `requirements-build.txt`. Third-party
notices recovered from installed packages are in `licenses/`. Upstream sources
and notices govern those components; this is not a relicensing of them.

RETOC is an external Rust application, not code written for Material Lab. Its
recorded runtime version is 0.1.5 and the included Tools/LICENSE is MIT. Review its
tagged upstream source and instructions if independently rebuilding it. The exact
local binary's original download record was not retained; its hash is recorded
in the release manifest. An upstream version link alone is not a byte-level
attestation of that executable.

## Resources not compiled from this repository

| Resource | Role and provenance limits |
| --- | --- |
| `AssetLibrary/chunks/*` | Raw assets extracted from the game's archives; source data, not Python modules. |
| `AssetLibrary/Exports/*` | Optional local metadata cache; contents are excluded from the portable release. Import required metadata with your own item exports. |
| `AssetLibrary/package_index.json` | Lookup from package paths to archive chunk IDs. |
| `Tools/oo2core_9_win64.dll` | Existing proprietary Oodle decompression dependency supplied with the previous local tool setup. No source or verified original download record is available here. |
| `Tools/companion.pak` | Existing 347-byte companion PAK template copied next to built mod containers. It is data, not an executable. No generator source was retained. |

The Oodle DLL and game data cannot be rebuilt from this application source.
Do not label them open source or covered by RETOC's MIT license. For full-content
review, compare their individual hashes to the already submitted release and
evaluate their provenance separately. No AES keys are needed to compile the app,
and none are committed.

`assemble.py` uses an extracted copy of the submitted release as a resource
input and verifies its contents. This deliberately avoids downloading unknown
DLLs or trying to recreate game binaries during the application build.

The final release's formerly nested `Optimized.zip` is unpacked into ordinary
asset files. The Python standard library is stored as files by PyInstaller's
`noarchive=True`, so the portable release contains no nested ZIP files.
