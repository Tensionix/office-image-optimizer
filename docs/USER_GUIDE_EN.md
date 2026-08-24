# Audion Office Image Optimizer - User Guide

Audion Office Image Optimizer reduces embedded image weight in office documents while preserving a controlled output copy and a readable processing report.

## Start

Use the project GUI launcher for normal work. The project launcher exposes the same operations for keyboard-driven use, while builder and install scripts belong to maintenance.

Before the first run, verify the portable runtime. Keep source documents outside disposable runtime and cache folders.

## Prepare Input

1. Add one or more supported office documents through the source picker.
2. Review the selected list and remove accidental entries.
3. Select an output folder different from the source folder.
4. Choose the optimization profile and any quality or size limits exposed by the current build.

Never overwrite the only copy of an important document. Work on copies and compare the optimized result before replacing an original.

## Run Optimization

Start the operation once and follow the live terminal. The application extracts or streams supported embedded images, applies the selected optimization policy, rebuilds the document, and writes results to the target folder.

The exact outcome depends on source formats, embedded image types, dimensions, compression, transparency, and office-package structure. Unsupported objects should be reported rather than silently discarded.

## Review Results

After completion:

- open the result in the relevant Office application;
- inspect representative pages, slides, sheets, headers, and backgrounds;
- compare file size with the source;
- check images that contain text, diagrams, transparency, or fine lines;
- read the generated log/report for skipped or failed objects;
- preserve the source until visual verification is complete.

## Workbench And Paths

The GUI separates `Source` and `Target`. The source list may contain multiple documents; the target is the output directory. Reset clears the current selection, while delete removes only the selected entry from the managed list.

Paths with spaces and Cyrillic are supported. Temporary data belongs to managed runtime locations, not to the project root. User output is never treated as cache.

## Launchers And Encoding

GUI, FZF, and CMD fallback actions must call the same project commands. Visible labels can be translated; paths, command identifiers, config keys, and environment variables remain unchanged.

All CMD/BAT files use UTF-8 without BOM and CRLF. If a launcher loops, closes instantly, or displays corrupted text, run the project encoding check and compare FZF dispatch with the fallback menu.

## Safe Maintenance

Routine cleanup may remove caches, temporary extraction trees, reports, logs, and rebuildable runtime artifacts according to the project policy. It must preserve source code, configuration, input documents, user output, license texts, and canonical documentation.

Use builder operations only when dependencies or runtime changed. Rebuilding is not required for ordinary document processing.

## Troubleshooting

- No output: verify target permissions and inspect the terminal.
- Document will not open: keep the source and review the first packaging error in the report.
- Images look soft: use a less aggressive profile or raise the quality/dimension limit.
- File size barely changes: the source may already contain compressed images or mostly vector content.
- Some images are skipped: check whether their format or office object type is supported.
- GUI picker fails: verify portable PowerShell and path quoting.

## Release Check

Before publishing the project, verify launchers, portable imports, one representative document per supported family, cleanup safety, license collection, and documentation links. Generated PDF documentation is not stored in the source Docs set.

Record the selected optimization profile and compare source/result size in the run report; size reduction is accepted only together with successful visual verification.

The GUI manifest is the source for supported actions, fields, defaults, hints, and command bindings. Use the guide to interpret those controls in document terms: expected size savings, image-quality risk, supported Office families, output placement, and the visual checks required before replacing an original.
