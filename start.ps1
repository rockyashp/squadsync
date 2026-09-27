# SquadSync Development Launcher (PowerShell)
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $scriptDir

$venvPython = Join-Path $scriptDir "backend\.venv\Scripts\python.exe"

if (Test-Path $venvPython) {
    Write-Host "[*] Launching SquadSync using backend virtual environment..." -ForegroundColor Cyan
    & $venvPython run.py
} else {
    Write-Host "[*] Launching SquadSync using system Python..." -ForegroundColor Cyan
    python run.py
}
