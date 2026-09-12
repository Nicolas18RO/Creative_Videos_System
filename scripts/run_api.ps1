# Arranca la API con el venv del proyecto (Whisper + tokenizers correctos).
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Host "No existe .venv. Crea e instala dependencias:" -ForegroundColor Yellow
    Write-Host "  python -m venv .venv"
    Write-Host "  .\.venv\Scripts\pip install -e `".[ml]`""
    exit 1
}

& $VenvPython -m uvicorn aicos.api.main:app --reload --host 127.0.0.1 --port 8000
