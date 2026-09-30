# Review guide for v0.21

## Code entry points

| Source file | Purpose |
| --- | --- |
| `desktop_main.py` | Windows entry point, startup error dialog, optional `--self-test` |
| `Material_Lab.py` | UI, import orchestration, color controls, preview export and mod build |
| `garment_import.py` | Material/mesh parsing, layer discovery, validated asset reads and writes |
| `weapon_support.py` | Weapon material metadata normalization and serialized vector identification |
| `color_controls.py` | RGB entry, swatches, sRGB/linear conversions |
| `appearance.py` | Light/dark styles and local appearance persistence |
| `library_tools.py` | Optional extraction of missing assets from a user-selected local archive |

All seven files are the source for the v0.21 desktop build. `review/source-sha256.json` records their hashes. The build helpers, docs
and tests were added for review after that release; they were not in the original
EXE. The included spec is the noarchive spec used for the final no-nested-ZIP build.

## Runtime behavior

- No first-party telemetry, account login, updater, network listener, scheduled
  task, registry installation, service, injection or startup registration.
- Reads the item folder selected by the user, bundled `AssetLibrary`, and its
  index. JSON files are data, not Python code to execute.
- Writes working material copies, reports, JSON previews and built mod files to
  `Projects` beside the EXE. Writes `recent_garments.json` and
  `appearance_settings.json` in that directory.
- The user copies the built `.pak`, `.utoc`, `.ucas` files into the game's mods
  directory; the v0.21 app does not automatically install them.
- Invokes local `Tools/retoc.exe` with explicit argument lists, without a shell:
  `pack-raw`, `verify`, and optional `get` for missing dependencies.
- “Collect missing assets” prompts for a local `.utoc` and AES key. The key is
  passed to RETOC on its command line for that operation. The app does not write
  the key into preferences, but command-line arguments may be visible to local
  process inspection tools. No key is included in this repository.
- Build-time pip downloads are separate from app runtime; build scripts contact
  PyPI to install requirements. PyInstaller embeds its bootloader and Python/Tk.

## Input and editing limits

The app handles binary game formats and is intended for trusted local exports.
It is not a sandbox for arbitrary hostile files. Asset path handling and parsers
remain review targets; no independent security audit is claimed.

The supported PARAM edits validate texture dimensions/layout and preserve
unmodified bytes. Weapon vector edits validate serialized identifying data.
Scalar mask writes removed during earlier development are not enabled here.
RETOC verification checks the built container, not every possible engine use of
the resulting material or compatibility with every game update.

## Submitted binary and non-source content

`release-manifest.json` lists **every file** in the submitted no-nested-ZIP release,
including the EXE, Python bytecode/DLLs, game cache, RETOC, Oodle DLL and PAK template.
The top-level SHA-256 identifies that precise submitted ZIP. It is not a prediction
of the SHA-256 of a newly rebuilt package.

The full submitted package contains third-party binary components and game-derived
data. Source availability for the app does not imply source availability or
redistribution permission for all of those components. DEPENDENCIES.md identifies
the boundary explicitly. A hosting reviewer may require additional provenance or
changes to those resources before accepting the full package.

The source repository excludes personal projects, save files, crash dumps,
recent-folder history, credentials and game archive keys.
