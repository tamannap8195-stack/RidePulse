$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

$projectPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (Test-Path $projectPython) {
    & $projectPython -m streamlit run app.py
    exit $LASTEXITCODE
}

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw 'Python was not found. Install Python, then run .\setup.ps1.'
}
& python -c "import streamlit, pandas, plotly"
if ($LASTEXITCODE -ne 0) { throw 'RidePulse dependencies are missing. Run .\setup.ps1, then start it with .\run.ps1.' }
& python -m streamlit run app.py
exit $LASTEXITCODE
