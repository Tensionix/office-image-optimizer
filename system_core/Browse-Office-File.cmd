@echo off
setlocal

set "OUTFILE=%~1"
if not defined OUTFILE exit /b 1

set "ROOT=%~dp0.."
set "PICKER=%ROOT%\system_core\Select-OfficeDocument.ps1"
set "INITIAL=%ROOT%\input"

if not exist "%PICKER%" exit /b 1

powershell -NoProfile -ExecutionPolicy Bypass -File "%PICKER%" -InitialDirectory "%INITIAL%" -OutputFile "%OUTFILE%"
exit /b %errorlevel%