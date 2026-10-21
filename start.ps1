# Run from the project directory. This does not require activating a virtualenv.
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not (Test-Path '.venv\Scripts\python.exe')) {
    py -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Python environment creation failed.' }
}
& '.\.venv\Scripts\python.exe' -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
& '.\.venv\Scripts\python.exe' -m streamlit run app.py
