$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

if (-not (Get-Command py -ErrorAction SilentlyContinue) -and -not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw 'Python 3.10 or newer was not found. Install Python from python.org, reopen PowerShell, and run this script again.'
}

if (-not (Test-Path '.venv\Scripts\python.exe')) {
    if (Get-Command py -ErrorAction SilentlyContinue) { & py -3 -m venv .venv }
    else { & python -m venv .venv }
    if ($LASTEXITCODE -ne 0) { throw 'Could not create .venv. Check that the Python installation includes the venv module.' }
}

& .\.venv\Scripts\python.exe -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw 'Could not update pip. Check internet access or Python package index access.' }
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed. Review the pip error above, then rerun .\setup.ps1.' }
Write-Host 'Setup complete. Start RidePulse with .\run.ps1' -ForegroundColor Green
