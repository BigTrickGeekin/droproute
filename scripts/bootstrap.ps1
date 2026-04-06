param(
    [string]$ProjectRoot = "."
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Set-Location $ProjectRoot

if (-not (Test-Path .venv)) {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        py -3 -m venv .venv
    }
    elseif (Get-Command python -ErrorAction SilentlyContinue) {
        python -m venv .venv
    }
    else {
        throw "Python 3.11+ is required but no Python launcher/runtime was found."
    }
}

& .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .[dev]

if (-not (Test-Path .\config.json)) {
    Copy-Item .\config.example.json .\config.json
}

Write-Host "Bootstrap complete."
Write-Host "Validate with: droproute validate --config .\config.json"
