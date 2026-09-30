# Dawnwalker Material Lab

Source and Windows build instructions for **v0.21**, corresponding to
`Dawnwalker_Material_Lab_v0.21_Full_Rebuilt.zip`.

Material Lab edits supported exported clothing and weapon materials for The Blood
of Dawnwalker. It discovers material sections, exposes PARAM, grime, scratch and
pattern/weapon color controls, exports preview JSON, and builds mod files using
RETOC. The interface includes drag-and-drop and persistent light/dark appearance.

## Windows quick start

1. Extract the entire portable release into a writable folder, such as Documents.
2. Run `Dawnwalker Material Lab.exe`. No Python setup is required.
3. Import an FModel item folder with material JSON, original .uasset files,
   PARAM texture metadata and preferably PSK/PSKX meshes.
4. Edit colors, Save project, then Build mod. Install the built mod trio using
   your normal game mod workflow.

Keep `_internal`, `Tools`, and `AssetLibrary` beside the EXE. To upgrade, close
Material Lab, back up its folder, then extract the full release over it. Preserve
`Projects` and settings. Vanilla exports start with vanilla colors; project
working copies retain your saved edits. Another mod's colors are not recovered
by importing a vanilla folder.

If no sections are editable, read the Import help tab and Import report.
Unsupported shaders, including the separate torso decal, remain read-only.

## Start here

- [Build instructions](docs/BUILD.md): app-only or full portable build on Windows.
- [Security review](docs/REVIEW.md): entry points, file access, subprocesses, limitations.
- [Dependencies and provenance](docs/DEPENDENCIES.md): source links and binary-only components.
- [Release manifest](review/release-manifest.json): SHA-256 of the submitted ZIP and every contained file.
- [Application source hashes](review/source-sha256.json): source files used for v0.21.
- [GitHub upload and moderator reply](docs/UPLOAD.md).

## Repository contents

`src/` contains all seven first-party Python modules used to build the application.
`MaterialLab.spec` packages those modules using PyInstaller's `noarchive=True`
mode. `build.ps1` and `scripts/` provide a repeatable build, resource verification,
runtime check, and packaging procedure. `tests/` contains source checks.

The build does not need a game installation to produce a runnable app-only EXE.
Editing and building supported items additionally needs the relevant exported
game data and build resources. These are **not application source code** and are
not stored in Git. The full release's resources can be verified and assembled
using the optional build parameter described in BUILD.md.

## Scope

Supported shader families include optimized clothing, SwordClothSimplified and
SimpleParameter weapon colors. Unsupported or unvalidated layouts are reported
rather than enabled for arbitrary editing. This repository does not include a
Blender add-on; the app exports JSON for preview integration.

This repository corresponds to the v0.21 release; it does not claim support for
every asset or future game version. Runtime tests are not a guarantee of in-game
behavior, nor of acceptance by a hosting site's review process.

## License status

Third-party components retain their own licenses; notices are in `licenses/` and
linked in DEPENDENCIES.md. No new redistribution license has been selected for
the first-party application in this review package. Publishing the source for
inspection does not relicense the game assets or proprietary dependencies.
