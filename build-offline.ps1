$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    python -m venv .venv
}

& .\.venv\Scripts\python.exe -m pip install -r facefinder-requirements.txt
& .\.venv\Scripts\python.exe -m pip install "pyinstaller>=6.10,<7" "Pillow>=10,<13"

& .\.venv\Scripts\python.exe -m PyInstaller `
    --noconfirm `
    --clean `
    --noconsole `
    --name ARFFaceFinder `
    --icon ".\assets\arf-face-finder.ico" `
    --add-data "facefinder_templates;facefinder_templates" `
    --add-data "facefinder_static;facefinder_static" `
    --add-data "assets\models;offline_models" `
    facefinder_windows_offline_v103.py

$isccPaths = @(
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe"
)
$iscc = $isccPaths | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $iscc) {
    throw "Inno Setup 6 was not found. Install JRSoftware.InnoSetup with winget."
}

& $iscc ".\installer\ARFFaceFinderOffline103.iss"
Write-Host "Created release\ARF-Face-Finder-Offline-Setup-1.0.3.exe"
