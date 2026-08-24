param(
    [string]$InitialDirectory = "",
    [string]$OutputFile = ""
)

$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.Windows.Forms | Out-Null
Add-Type -AssemblyName System.Drawing | Out-Null

$dialog = New-Object System.Windows.Forms.OpenFileDialog
$dialog.Title = "Select Office document"
$dialog.Filter = "Office documents (*.docx;*.pptx)|*.docx;*.pptx|Word documents (*.docx)|*.docx|PowerPoint presentations (*.pptx)|*.pptx|All files (*.*)|*.*"
$dialog.Multiselect = $false
$dialog.CheckFileExists = $true
$dialog.CheckPathExists = $true
$dialog.RestoreDirectory = $false

if ([string]::IsNullOrWhiteSpace($InitialDirectory) -or -not (Test-Path -LiteralPath $InitialDirectory -PathType Container)) {
    $InitialDirectory = (Get-Location).Path
}

$dialog.InitialDirectory = (Resolve-Path -LiteralPath $InitialDirectory).Path

$result = $dialog.ShowDialog()

if ($result -eq [System.Windows.Forms.DialogResult]::OK -and -not [string]::IsNullOrWhiteSpace($dialog.FileName)) {
    if ([string]::IsNullOrWhiteSpace($OutputFile)) {
        exit 1
    }

    $dir = Split-Path -Parent $OutputFile
    if ($dir -and -not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }

    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($OutputFile, $dialog.FileName, $utf8NoBom)
    exit 0
}

exit 1