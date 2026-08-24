Place these files like this:

system_core\Select-OfficeDocument.ps1
system_core\Browse-Office-File.cmd

Recommended launcher logic:
- build one FZF file list that includes a synthetic entry like:
  BROWSE FILE...
- if that entry is selected, call:
  system_core\Browse-Office-File.cmd
- read the returned full path from stdout
- use that path as the document target

This keeps the GUI picker isolated in system_core and the main launcher stays simple.
