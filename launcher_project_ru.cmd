@echo off
chcp 65001 >nul
setlocal EnableExtensions EnableDelayedExpansion

title Audion Office Image Optimizer - Русский

set "BASE_DIR=%~dp0"
if "%BASE_DIR:~-1%"=="\" set "BASE_DIR=%BASE_DIR:~0,-1%"
cd /d "%BASE_DIR%"

set "CORE_DIR=%BASE_DIR%\system_core"
set "RUNTIME_DIR=%BASE_DIR%\._runtime"

if not exist "%RUNTIME_DIR%" mkdir "%RUNTIME_DIR%" >nul 2>nul

set "MENU_FILE=%RUNTIME_DIR%\project_menu_ru.txt"
set "RES_FILE=%RUNTIME_DIR%\project_menu_ru_res.txt"
set "DOC_FILE=%RUNTIME_DIR%\project_docs_ru.txt"
set "DOC_RES=%RUNTIME_DIR%\project_docs_ru_res.txt"

del /q "%RUNTIME_DIR%\project_menu_ru_*.txt" "%RUNTIME_DIR%\project_docs_ru_*.txt" >nul 2>nul

set "PYTHONPATH=system_core"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

call :RESOLVE_PYTHON
if errorlevel 1 goto NO_PYTHON

call :RESOLVE_FZF
if errorlevel 1 (
  set "MENU_MODE=CMD fallback"
) else (
  set "MENU_MODE=FZF"
)

:MAIN
cls
echo ======================================================================
echo   AUDION OFFICE IMAGE OPTIMIZER - РУССКИЙ ПРОЕКТНЫЙ ЛАУНЧЕР
echo ======================================================================
echo Корень:    %BASE_DIR%
echo Python:    %PYTHON_CMD% %PYTHON_ARGS%
echo Режим меню: %MENU_MODE%
echo.

if /I "%AUDION_AUTO_EXIT%"=="1" exit /b 0

if defined FZF_CMD goto FZF_MENU
goto FALLBACK_MENU

:FZF_MENU
> "%MENU_FILE%" echo [01] SAFE FHD       - Интерактивно, только JPEG, 1920x1080   ^| ask_safe_fhd   ^| ask --mode safe --preset fhd
>>"%MENU_FILE%" echo [02] SAFE QHD       - Интерактивно, только JPEG, 2560x1440   ^| ask_safe_qhd   ^| ask --mode safe --preset qhd
>>"%MENU_FILE%" echo [03] SAFE UHD       - Интерактивно, только JPEG, 3840x2160   ^| ask_safe_uhd   ^| ask --mode safe --preset uhd
>>"%MENU_FILE%" echo [04] HARD QHD       - Интерактивно, все растры, 2560x1440    ^| ask_hard_qhd   ^| ask --mode hard --preset qhd
>>"%MENU_FILE%" echo [05] HARD UHD       - Интерактивно, все растры, 3840x2160    ^| ask_hard_uhd   ^| ask --mode hard --preset uhd
>>"%MENU_FILE%" echo [06] SAFE BATCH FHD - Авто, только JPEG, 1920x1080           ^| batch_safe_fhd ^| batch --mode safe --preset fhd
>>"%MENU_FILE%" echo [07] SAFE BATCH QHD - Авто, только JPEG, 2560x1440           ^| batch_safe_qhd ^| batch --mode safe --preset qhd
>>"%MENU_FILE%" echo [08] SAFE BATCH UHD - Авто, только JPEG, 3840x2160           ^| batch_safe_uhd ^| batch --mode safe --preset uhd
>>"%MENU_FILE%" echo [09] HARD BATCH FHD - Авто, все растры, 1920x1080            ^| batch_hard_fhd ^| batch --mode hard --preset fhd
>>"%MENU_FILE%" echo [10] HARD BATCH QHD - Авто, все растры, 2560x1440            ^| batch_hard_qhd ^| batch --mode hard --preset qhd
>>"%MENU_FILE%" echo [11] HARD BATCH UHD - Авто, все растры, 3840x2160            ^| batch_hard_uhd ^| batch --mode hard --preset uhd
>>"%MENU_FILE%" echo.
>>"%MENU_FILE%" echo [12] УЛОЖИТЬСЯ В 20 МБ    - HARD JPG автоподбор              ^| fit_size       ^| fit-size --target-mb 20
>>"%MENU_FILE%" echo [13] НОРМАЛИЗОВАТЬ В SRGB - КОМПАКТ (РЕКОМЕНДУЕТСЯ)          ^| norm_srgb      ^| normalize-srgb
>>"%MENU_FILE%" echo [14] НОРМАЛИЗОВАТЬ В SRGB - ВШИТЬ ICC                        ^| norm_srgb_icc  ^| normalize-srgb --embed-icc
>>"%MENU_FILE%" echo [15] НОРМАЛИЗОВАТЬ В CMYK - КОМПАКТ (РЕКОМЕНДУЕТСЯ)          ^| norm_cmyk      ^| normalize-cmyk
>>"%MENU_FILE%" echo [16] НОРМАЛИЗОВАТЬ В CMYK - ВШИТЬ ICC HEAVY                  ^| norm_cmyk_icc  ^| normalize-cmyk --embed-icc
>>"%MENU_FILE%" echo [17] ТОЛЬКО СКАНИРОВАНИЕ  - анализ без записи                ^| scan           ^| scan
>>"%MENU_FILE%" echo [18] ИЗВЛЕЧЬ КАРТИНКИ     - экспорт word/ppt media           ^| extract_media  ^| extract-media
>>"%MENU_FILE%" echo.
>>"%MENU_FILE%" echo [19] ОТКРЫТЬ INPUT         - открыть папку input             ^| open_input     ^| explorer
>>"%MENU_FILE%" echo [20] СПРАВКА CLI           - python -m app --help            ^| cli_help       ^| --help
>>"%MENU_FILE%" echo [00] ВЫХОД                  - закрыть лаунчер                ^| exit           ^| close

"%FZF_CMD%" --prompt="audion@image-optimizer [PROJECT-RU] > " --pointer=">" --header="Выберите режим. Сверху быстрые режимы, ниже служебные пункты." --layout=reverse --border=rounded --info=hidden --margin=1,2  < "%MENU_FILE%" > "%RES_FILE%"

set "CHOICE="
set /p CHOICE=<"%RES_FILE%"
if not defined CHOICE goto MAIN

for /f "tokens=2 delims=|" %%a in ("%CHOICE%") do set "RAW=%%a"
call :TRIM RAW

if /I "%RAW%"=="exit" exit /b 0
if /I "%RAW%"=="open_input" goto OPEN_INPUT
if /I "%RAW%"=="cli_help" goto CLI_HELP
if /I "%RAW%"=="ask_safe_fhd" goto SET_ASK_SAFE_FHD
if /I "%RAW%"=="ask_safe_qhd" goto SET_ASK_SAFE_QHD
if /I "%RAW%"=="ask_safe_uhd" goto SET_ASK_SAFE_UHD
if /I "%RAW%"=="ask_hard_qhd" goto SET_ASK_HARD_QHD
if /I "%RAW%"=="ask_hard_uhd" goto SET_ASK_HARD_UHD
if /I "%RAW%"=="batch_safe_fhd" goto SET_BATCH_SAFE_FHD
if /I "%RAW%"=="batch_safe_qhd" goto SET_BATCH_SAFE_QHD
if /I "%RAW%"=="batch_safe_uhd" goto SET_BATCH_SAFE_UHD
if /I "%RAW%"=="batch_hard_fhd" goto SET_BATCH_HARD_FHD
if /I "%RAW%"=="batch_hard_qhd" goto SET_BATCH_HARD_QHD
if /I "%RAW%"=="batch_hard_uhd" goto SET_BATCH_HARD_UHD
if /I "%RAW%"=="fit_size" goto SET_FIT_SIZE
if /I "%RAW%"=="norm_srgb" goto SET_NORM_SRGB
if /I "%RAW%"=="norm_srgb_icc" goto SET_NORM_SRGB_ICC
if /I "%RAW%"=="norm_cmyk" goto SET_NORM_CMYK
if /I "%RAW%"=="norm_cmyk_icc" goto SET_NORM_CMYK_ICC
if /I "%RAW%"=="scan" goto SET_SCAN
if /I "%RAW%"=="extract_media" goto SET_EXTRACT_MEDIA
goto MAIN

:FALLBACK_MENU
echo [1] SAFE FHD       - Интерактивно, только JPEG, 1920x1080
echo [2] SAFE QHD       - Интерактивно, только JPEG, 2560x1440
echo [3] SAFE UHD       - Интерактивно, только JPEG, 3840x2160
echo [4] HARD QHD       - Интерактивно, все растры, 2560x1440
echo [5] HARD UHD       - Интерактивно, все растры, 3840x2160
echo [6] JPEG до 1920x1080 - авто, PNG/GIF/BMP/TIFF не трогает
echo [7] JPEG до 2560x1440 - авто, PNG/GIF/BMP/TIFF не трогает
echo [8] JPEG до 3840x2160 - авто, PNG/GIF/BMP/TIFF не трогает
echo [9] Растры до 1920x1080 - авто, JPEG/PNG/GIF/BMP/TIFF
echo [A] Растры до 2560x1440 - авто, JPEG/PNG/GIF/BMP/TIFF
echo [B] Растры до 3840x2160 - авто, JPEG/PNG/GIF/BMP/TIFF
echo [C] УЛОЖИТЬСЯ В 20 МБ - HARD JPG автоподбор
echo [D] НОРМАЛИЗОВАТЬ В SRGB - КОМПАКТ (РЕКОМЕНДУЕТСЯ)
echo [E] НОРМАЛИЗОВАТЬ В SRGB - ВШИТЬ ICC
echo [F] НОРМАЛИЗОВАТЬ В CMYK - КОМПАКТ (РЕКОМЕНДУЕТСЯ)
echo [G] НОРМАЛИЗОВАТЬ В CMYK - ВШИТЬ ICC HEAVY (БОЛЬШИЕ ФАЙЛЫ)
echo [H] ТОЛЬКО СКАНИРОВАНИЕ
echo [I] ИЗВЛЕЧЬ КАРТИНКИ
echo [J] ОТКРЫТЬ INPUT
echo [K] СПРАВКА CLI
echo [0] ВЫХОД
echo.
choice /C 123456789ABCDEFGHIJK0 /N /M "Выбор: "
if errorlevel 21 exit /b 0
if errorlevel 20 goto CLI_HELP
if errorlevel 19 goto OPEN_INPUT
if errorlevel 18 goto SET_EXTRACT_MEDIA
if errorlevel 17 goto SET_SCAN
if errorlevel 16 goto SET_NORM_CMYK_ICC
if errorlevel 15 goto SET_NORM_CMYK
if errorlevel 14 goto SET_NORM_SRGB_ICC
if errorlevel 13 goto SET_NORM_SRGB
if errorlevel 12 goto SET_FIT_SIZE
if errorlevel 11 goto SET_BATCH_HARD_UHD
if errorlevel 10 goto SET_BATCH_HARD_QHD
if errorlevel 9 goto SET_BATCH_HARD_FHD
if errorlevel 8 goto SET_BATCH_SAFE_UHD
if errorlevel 7 goto SET_BATCH_SAFE_QHD
if errorlevel 6 goto SET_BATCH_SAFE_FHD
if errorlevel 5 goto SET_ASK_HARD_UHD
if errorlevel 4 goto SET_ASK_HARD_QHD
if errorlevel 3 goto SET_ASK_SAFE_UHD
if errorlevel 2 goto SET_ASK_SAFE_QHD
if errorlevel 1 goto SET_ASK_SAFE_FHD
goto MAIN

:SET_ASK_SAFE_FHD
set "APP_CMD=ask"
set "APP_MODE=safe"
set "APP_PRESET=fhd"
goto PICK_DOC
:SET_ASK_SAFE_QHD
set "APP_CMD=ask"
set "APP_MODE=safe"
set "APP_PRESET=qhd"
goto PICK_DOC
:SET_ASK_SAFE_UHD
set "APP_CMD=ask"
set "APP_MODE=safe"
set "APP_PRESET=uhd"
goto PICK_DOC
:SET_ASK_HARD_QHD
set "APP_CMD=ask"
set "APP_MODE=hard"
set "APP_PRESET=qhd"
goto PICK_DOC
:SET_ASK_HARD_UHD
set "APP_CMD=ask"
set "APP_MODE=hard"
set "APP_PRESET=uhd"
goto PICK_DOC
:SET_BATCH_SAFE_FHD
set "APP_CMD=batch"
set "APP_MODE=safe"
set "APP_PRESET=fhd"
goto PICK_DOC
:SET_BATCH_SAFE_QHD
set "APP_CMD=batch"
set "APP_MODE=safe"
set "APP_PRESET=qhd"
goto PICK_DOC
:SET_BATCH_SAFE_UHD
set "APP_CMD=batch"
set "APP_MODE=safe"
set "APP_PRESET=uhd"
goto PICK_DOC
:SET_BATCH_HARD_FHD
set "APP_CMD=batch"
set "APP_MODE=hard"
set "APP_PRESET=fhd"
goto PICK_DOC
:SET_BATCH_HARD_QHD
set "APP_CMD=batch"
set "APP_MODE=hard"
set "APP_PRESET=qhd"
goto PICK_DOC
:SET_BATCH_HARD_UHD
set "APP_CMD=batch"
set "APP_MODE=hard"
set "APP_PRESET=uhd"
goto PICK_DOC
:SET_FIT_SIZE
set "APP_CMD=fit_size"
set "APP_MODE="
set "APP_PRESET="
set "APP_TARGET_MB=20"
goto PICK_DOC
:SET_NORM_SRGB
set "APP_CMD=norm_srgb"
set "APP_MODE="
set "APP_PRESET="
goto PICK_DOC
:SET_NORM_SRGB_ICC
set "APP_CMD=norm_srgb_icc"
set "APP_MODE="
set "APP_PRESET="
goto PICK_DOC
:SET_NORM_CMYK
set "APP_CMD=norm_cmyk"
set "APP_MODE="
set "APP_PRESET="
goto PICK_DOC
:SET_NORM_CMYK_ICC
set "APP_CMD=norm_cmyk_icc"
set "APP_MODE="
set "APP_PRESET="
goto PICK_DOC
:SET_SCAN
set "APP_CMD=scan"
set "APP_MODE="
set "APP_PRESET="
goto PICK_DOC
:SET_EXTRACT_MEDIA
set "APP_CMD=extract_media"
set "APP_MODE="
set "APP_PRESET="
goto PICK_DOC

:PICK_DOC
if defined FZF_CMD (
  call :PICK_DOC_FZF
) else (
  call :PICK_DOC_CMD
)
if not defined TARGET goto MAIN
if not exist "%TARGET%" (
  echo [ERROR] Файл не найден: %TARGET%
  if not defined AUDION_NO_PAUSE pause >nul
  goto MAIN
)
call :RUN_CMD
if not defined AUDION_NO_PAUSE pause
goto MAIN

:PICK_DOC_FZF
set "TARGET="
type nul > "%DOC_FILE%"
if exist "%BASE_DIR%\input" for /r "%BASE_DIR%\input" %%F in (*.docx *.pptx) do @echo %%~fF>>"%DOC_FILE%"
for %%Z in ("%DOC_FILE%") do set "DOC_SIZE=%%~zZ"
if "%DOC_SIZE%"=="0" (
  del /q "%DOC_FILE%" >nul 2>nul
  echo [ERROR] В input не найдено файлов DOCX или PPTX.
  if not defined AUDION_NO_PAUSE pause >nul
  goto :eof
)
sort "%DOC_FILE%" /o "%DOC_FILE%.sorted" >nul
"%FZF_CMD%" --prompt="Документ > " --pointer=">" --header="Выберите DOCX/PPTX из input" --layout=reverse --border=rounded --info=hidden --margin=1,2 < "%DOC_FILE%.sorted" > "%DOC_RES%"
del /q "%DOC_FILE%" "%DOC_FILE%.sorted" >nul 2>nul
set /p TARGET=<"%DOC_RES%"
del /q "%DOC_RES%" >nul 2>nul
goto :eof

:PICK_DOC_CMD
set "TARGET="
echo.
set /p TARGET=Введите путь к DOCX/PPTX файлу: 
goto :eof

:CLI_HELP
"%PYTHON_CMD%" %PYTHON_ARGS% -m app --help
if not defined AUDION_NO_PAUSE pause
goto MAIN

:OPEN_INPUT
start "" explorer "%BASE_DIR%\input"
goto MAIN

:RUN_CMD
if /I "%APP_CMD%"=="ask" "%PYTHON_CMD%" %PYTHON_ARGS% -m app ask "%TARGET%" --mode %APP_MODE% --preset %APP_PRESET%
if /I "%APP_CMD%"=="batch" "%PYTHON_CMD%" %PYTHON_ARGS% -m app batch "%TARGET%" --mode %APP_MODE% --preset %APP_PRESET%
if /I "%APP_CMD%"=="fit_size" "%PYTHON_CMD%" %PYTHON_ARGS% -m app fit-size "%TARGET%" --target-mb %APP_TARGET_MB%
if /I "%APP_CMD%"=="norm_srgb" "%PYTHON_CMD%" %PYTHON_ARGS% -m app normalize-srgb "%TARGET%"
if /I "%APP_CMD%"=="norm_srgb_icc" "%PYTHON_CMD%" %PYTHON_ARGS% -m app normalize-srgb "%TARGET%" --embed-icc
if /I "%APP_CMD%"=="norm_cmyk" "%PYTHON_CMD%" %PYTHON_ARGS% -m app normalize-cmyk "%TARGET%"
if /I "%APP_CMD%"=="norm_cmyk_icc" "%PYTHON_CMD%" %PYTHON_ARGS% -m app normalize-cmyk "%TARGET%" --embed-icc
if /I "%APP_CMD%"=="scan" "%PYTHON_CMD%" %PYTHON_ARGS% -m app scan "%TARGET%"
if /I "%APP_CMD%"=="extract_media" "%PYTHON_CMD%" %PYTHON_ARGS% -m app extract-media "%TARGET%"
goto :eof

:NO_PYTHON
cls
echo [ERROR] Python runtime не найден.
echo.
echo Поддерживаемые варианты:
echo   runtime\python.exe
echo   runtime\python\python.exe
echo   py -3.12
echo   python
echo.
if not defined AUDION_NO_PAUSE pause
exit /b 1

:RESOLVE_PYTHON
set "PYTHON_CMD="
set "PYTHON_ARGS="
if exist "%BASE_DIR%\runtime\python.exe" (
  set "PYTHON_CMD=%BASE_DIR%\runtime\python.exe"
  goto :eof
)
if exist "%BASE_DIR%\runtime\python\python.exe" (
  set "PYTHON_CMD=%BASE_DIR%\runtime\python\python.exe"
  goto :eof
)
py -3.12 -V >nul 2>nul
if not errorlevel 1 (
  set "PYTHON_CMD=py"
  set "PYTHON_ARGS=-3.12"
  goto :eof
)
where python >nul 2>nul
if not errorlevel 1 set "PYTHON_CMD=python"
if defined PYTHON_CMD (exit /b 0) else (exit /b 1)

:RESOLVE_FZF
set "FZF_CMD="
if exist "%CORE_DIR%\fzf.exe" (
  set "FZF_CMD=%CORE_DIR%\fzf.exe"
  exit /b 0
)
where fzf >nul 2>nul
if not errorlevel 1 (
  set "FZF_CMD=fzf"
  exit /b 0
)
exit /b 1

:TRIM
for /f "tokens=* delims= " %%z in ("!%~1!") do set "%~1=%%z"
:TRIM_R
if "!%~1:~-1!"==" " set "%~1=!%~1:~0,-1!" & goto TRIM_R
goto :eof
