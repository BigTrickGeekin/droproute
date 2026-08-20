param(
    [switch]$Clean
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

if ($Clean) {
    if (Test-Path .\build) {
        Remove-Item -Recurse -Force .\build
    }
    if (Test-Path .\dist) {
        Remove-Item -Recurse -Force .\dist
    }
}

if (-not (Test-Path .\.venv\Scripts\python.exe)) {
    & .\scripts\bootstrap.ps1 -ProjectRoot $ProjectRoot
}

& .\.venv\Scripts\python.exe -m pip install -e ".[build]"
& .\.venv\Scripts\python.exe -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --name DropRoute `
    --collect-all watchdog `
    .\src\droproute\cli.py

Write-Host "Build complete: $ProjectRoot\dist\DropRoute.exe"
