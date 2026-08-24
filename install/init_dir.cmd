@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
for %%A in ("%SCRIPT_DIR%\..") do set "ROOT=%%~fA"

if not exist "%ROOT%\input" mkdir "%ROOT%\input"
if not exist "%ROOT%\output" mkdir "%ROOT%\output"
if not exist "%ROOT%\logs" mkdir "%ROOT%\logs"
if not exist "%ROOT%\GitHub" mkdir "%ROOT%\GitHub"

echo [OK] Working directories are ready.
echo [INFO] input   = %ROOT%\input
echo [INFO] output  = %ROOT%\output
echo [INFO] logs    = %ROOT%\logs
echo [INFO] GitHub  = %ROOT%\GitHub
exit /b 0
