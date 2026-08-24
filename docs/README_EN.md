# Audion Office Image Optimizer

<!-- audion:release -->
[![Windows](https://img.shields.io/badge/Windows-10%20%7C%2011-0b6db8?style=flat-square&logo=windows&logoColor=white)](https://audion.dev/downloads/office-image-optimizer) [![Release](https://img.shields.io/github/v/release/Tensionix/audion-office-image-optimizer?style=flat-square&label=release&color=e08a63)](https://github.com/Tensionix/audion-office-image-optimizer/releases/latest) [![Downloads](https://img.shields.io/github/downloads/Tensionix/audion-office-image-optimizer/total?style=flat-square&label=downloads&color=5fd08a)](https://github.com/Tensionix/audion-office-image-optimizer/releases) [![License](https://img.shields.io/github/license/Tensionix/audion-office-image-optimizer?style=flat-square&color=5fd08a&logo=apache&logoColor=white&cacheSeconds=3600)](https://github.com/Tensionix/audion-office-image-optimizer/blob/main/LICENSE)

**Version 1.7.1** · 2026-08-24 · 103.9 MB

- [Direct download](https://audion.dev/get/office-image-optimizer/1.7.1/Audion_Office_Image_Optimizer_v1.7.1_Full.zip) — unmetered, no rate limits
- [Project page](https://audion.dev/downloads/office-image-optimizer) — every version and how to install

`SHA-256: f9b21c5561fda15ea9e6481c0cdbd43f48891f129d8019a7cdb1b192d861997e`
<!-- /audion:release -->

Portable project for processing embedded raster images inside Microsoft Office `DOCX` and `PPTX` files.

Current project layout:

- `system_core\app\` contains the Python application code;
- `runtime\` contains the embedded Python runtime;
- `config\` contains defaults and ICC profiles;
- `GitHub\` contains the main project documentation for releases and repository pages.

Main launchers in the project root:

- `launcher_project.cmd` - English launcher
- `launcher_project_picker.cmd` - English launcher with file picker
- `launcher_project_ru.cmd` - Russian launcher
- `launcher_project_picker_ru.cmd` - Russian launcher with file picker
- `launcher_gui.cmd` - desktop GUI shell over the existing CLI

Service launchers remain English-only:

- `builder_main.cmd` - build and packaging tools
- `launcher_tools.cmd` - service, licensing, and release tools

Python entry point:

- `runtime\python.exe -m app --help`
- `runtime\python.exe -m app scan "input\file.docx"`
- `runtime\python.exe -m app batch "input\file.docx" --mode hard --preset presentation`
- `runtime\python.exe -m app fit-size "input\file.docx" --target-mb 20`
- `runtime\python.exe -m app extract-media "input\file.docx"`

GUI optimization choice:

- `Standard resolutions`:
  - `1920x1080` - ordinary document;
  - `2560x1440` - presentations;
  - `3840x2160` - print / archive.
- `JPEG quality` - the shared compression lever for all GUI optimization modes, default `82`.
- `Custom size` - manual width/height for stronger or non-standard compression.
- `Fit to size` - a separate automatic operation for targets such as `20 MB`.

Standard resolution mode always runs `HARD`. Custom size mode exposes width/height number fields, `SAFE` / `HARD`, and the tiny-PNG override, which defaults to `400x400`.

`Fit to size` always uses `HARD JPG`: it first lowers JPEG quality to `75`, then reduces resolution down to `1920x1080`, then lowers quality to `65`, then tries `1600x900` and `1280x720`. Portrait images automatically receive rotated limits, for example `1920x1080` becomes `1080x1920`.

Reports include document size, embedded media size, decoded-size estimate, format summary, largest image parts, and per-image recommendations.

The GUI layer is focused on clear automatic workflows:

- inspect what is inside DOCX/PPTX files;
- optimize Office files through a clear resolution choice;
- fit a file under a target size in MB;
- normalize images to sRGB or CMYK;
- extract `word/media` and `ppt/media` into `output\<document-name>\`.
- choose a Source file/folder and a Target folder directly in the Workbench.

## Canonical Workbench labels

The Workbench is the shared top-level routing block used by Audion NiceGUI projects. It contains the `Source` and `Target` address rows and these exact action labels: `Source`, `Add file...`, `Target`, `Reset`, `Delete`, and `List`.

`Source` can be one `DOCX`/`PPTX` file or a folder. `Target` is the results folder. Every operation uses the paths selected in the Workbench; operation screens do not duplicate input/output path fields. `Reset` restores the project `input` and `output` routes.

The ordinary GUI hides technical image details. Standard resolutions run in `HARD`; safe optimization is available only in the manual `Custom size` mode.

Cleanup is intentionally narrower than normal I/O: it clears only the managed project `input` and `output` folders.

Interactive CLI/TUI paths such as `SAFE ASK` remain expert routes and are not the primary GUI workflow.

GUI adaptation notes and smoke gates are documented in:

- `docs\GUI_TEMPLATE_ADAPTATION_NOTES_RU.md`

Main GitHub materials:

- `GitHub\README.md`
- `GitHub\README_RU.md`
- `GitHub\Release Description (Audion Office Image Optimizer).md`
- `GitHub\source_docs\`

For normal use, keep the source document until the optimized copy has been opened and visually checked in the target Office application.
