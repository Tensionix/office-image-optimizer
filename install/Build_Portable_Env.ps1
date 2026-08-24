$ErrorActionPreference = "Stop"

$installDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $installDir
$downloadDir = Join-Path $installDir "download"
$runtimeDir = Join-Path $rootDir "runtime"
$wheelhouseDir = Join-Path $rootDir "wheelhouse"
$requirementsFile = Join-Path $installDir "requirements_full.in"
$doctorScript = Join-Path $rootDir "system_core\doctor.py"
$guiSmokeScript = Join-Path $rootDir "system_core\ui_nicegui\app.py"
$cmdEncodingScript = Join-Path $installDir "Repair-CmdEncoding.ps1"

$pythonMinor = 12
$headers = @{ 'User-Agent' = 'Audion-Portable-Installer' }

$pyPatch = -1
for ($i = 0; $i -le 40; $i++) {
    $uri = "https://www.python.org/ftp/python/3.$pythonMinor.$i/python-3.$pythonMinor.$i-embed-amd64.zip"
    try {
        Invoke-WebRequest -Headers $headers -Uri $uri -Method Head -TimeoutSec 10 | Out-Null
        $pyPatch = $i
    } catch {
        if ($pyPatch -ge 0) { break }
    }
}
if ($pyPatch -lt 0) { throw "Could not resolve any Python 3.$pythonMinor.x embed-amd64 build" }
$pythonVersion = "3.$pythonMinor.$pyPatch"
$pythonZipName = "python-$pythonVersion-embed-amd64.zip"
$pythonUrl = "https://www.python.org/ftp/python/$pythonVersion/$pythonZipName"
$pythonZipPath = Join-Path $downloadDir $pythonZipName
$getPipUrl = "https://bootstrap.pypa.io/get-pip.py"
$getPipPath = Join-Path $downloadDir "get-pip.py"
$bootstrapPackages = @("setuptools", "wheel", "packaging")

function Invoke-Native {
    param(
        [Parameter(Mandatory = $true)]
        [string] $FilePath,

        [string[]] $Arguments
    )

    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Native command failed with exit code ${LASTEXITCODE}: $FilePath $($Arguments -join ' ')"
    }
}

Write-Host "======================================================================"
Write-Host "AUDION OFFICE IMAGE OPTIMIZER - BUILD PORTABLE ENV (PS)"
Write-Host "======================================================================"
Write-Host "Root:        $rootDir"
Write-Host "Install:     $installDir"
Write-Host "Download:    $downloadDir"
Write-Host "Runtime:     $runtimeDir"
Write-Host "Wheelhouse:  $wheelhouseDir"
Write-Host ""

New-Item -ItemType Directory -Force -Path $downloadDir | Out-Null
New-Item -ItemType Directory -Force -Path $runtimeDir | Out-Null
New-Item -ItemType Directory -Force -Path $wheelhouseDir | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $rootDir "report") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $rootDir "workspace") | Out-Null

Write-Host "[0/8] Normalizing project CMD files..."
if (-not (Test-Path $cmdEncodingScript)) {
    throw "Missing file: $cmdEncodingScript"
}
& $cmdEncodingScript -Root $rootDir -Fix

Write-Host "[1/8] Downloading Python Embedded..."
Invoke-WebRequest -Uri $pythonUrl -OutFile $pythonZipPath

Write-Host "[2/8] Extracting runtime..."
if (Test-Path $runtimeDir) {
    Get-ChildItem -Force $runtimeDir | Remove-Item -Force -Recurse -ErrorAction SilentlyContinue
}
Expand-Archive -Path $pythonZipPath -DestinationPath $runtimeDir -Force

Write-Host "[3/8] Enabling import site..."
$pthFile = Join-Path $runtimeDir "python3$pythonMinor._pth"
if (-not (Test-Path $pthFile)) {
    throw "Missing file: $pthFile"
}
$pthLines = (Get-Content $pthFile) -replace '^#import site$', 'import site'
if ($pthLines -notcontains "..\system_core") {
    $pthLines = @("..\system_core") + $pthLines
}
$pthLines | Set-Content $pthFile -Encoding ASCII

Write-Host "[4/8] Downloading get-pip.py..."
# A dropped connection here used to kill the whole project build.
$getPipOk = $false
foreach ($getPipTry in 1..5) {
    $getPipTmp = "$($getPipPath).part"
    try {
        Invoke-WebRequest -Uri $getPipUrl -OutFile $getPipTmp -TimeoutSec 120 -UseBasicParsing
        $getPipSize = (Get-Item -LiteralPath $getPipTmp).Length
        if ($getPipSize -lt 1000000) { throw "truncated body: $getPipSize bytes" }
        Move-Item -LiteralPath $getPipTmp -Destination $getPipPath -Force
        $getPipOk = $true
        break
    } catch {
        Write-Host "  get-pip.py attempt $getPipTry failed: $($_.Exception.Message)"
        Remove-Item -LiteralPath $getPipTmp -Force -ErrorAction SilentlyContinue
        if ($getPipTry -lt 5) { Start-Sleep -Seconds (3 * $getPipTry) }
    }
}
if (-not $getPipOk) { throw "Could not download get-pip.py after 5 attempts - the network dropped every time." }
$pythonExe = Join-Path $runtimeDir "python.exe"
if (-not (Test-Path $pythonExe)) {
    throw "Missing file: $pythonExe"
}

Write-Host "[5/8] Installing pip..."
Invoke-Native $pythonExe @($getPipPath)

Write-Host "[6/8] Installing bootstrap build packages..."
$bootstrapInstallArgs = @(
    "-m", "pip", "install",
    "--disable-pip-version-check",
    "--upgrade"
) + $bootstrapPackages
Invoke-Native $pythonExe $bootstrapInstallArgs

Write-Host "[7/8] Building wheelhouse and installing packages..."
Get-ChildItem -Force $wheelhouseDir |
    Where-Object { $_.Name -ne ".gitkeep" } |
    Remove-Item -Force -Recurse
$downloadArgs = @(
    "-m", "pip", "wheel",
    "--disable-pip-version-check",
    "--prefer-binary",
    "--no-build-isolation",
    "--timeout", "120",
    "--retries", "12",
    "-r", $requirementsFile,
    "-w", $wheelhouseDir
)
$installArgs = @(
    "-m", "pip", "install",
    "--disable-pip-version-check",
    "--no-build-isolation",
    "--no-index",
    "--find-links=$wheelhouseDir",
    "-r", $requirementsFile
)
Invoke-Native $pythonExe $downloadArgs
Invoke-Native $pythonExe $installArgs

Write-Host "[8/8] Verifying environment..."
Invoke-Native $pythonExe @($doctorScript)
if (Test-Path $guiSmokeScript) {
    Invoke-Native $pythonExe @($guiSmokeScript, "--smoke")
}

Write-Host ""
Write-Host "[SUCCESS] Portable environment is ready."
Write-Host "[INFO] Release licensing is generated later from the finalized release contents."
