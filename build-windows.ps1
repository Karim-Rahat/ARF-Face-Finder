$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

& .\.venv\Scripts\python.exe -m pip install "pyinstaller>=6.10,<7"
& .\.venv\Scripts\python.exe -m PyInstaller `
  --noconfirm `
  --clean `
  --noconsole `
  --name FaceFinder `
  --add-data "facefinder_templates;facefinder_templates" `
  --add-data "facefinder_static;facefinder_static" `
  facefinder_windows.py

$iscc = Get-Command iscc.exe -ErrorAction SilentlyContinue
if (-not $iscc) {
  $isccPath = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
  if (Test-Path $isccPath) { $iscc = Get-Item $isccPath }
}
if (-not $iscc) { throw "Inno Setup 6 is required to build the installer." }
& $iscc.Source .\installer\FaceFinder.iss

Write-Host "Installer created: release\FaceFinder-Setup-1.0.0.exe"
