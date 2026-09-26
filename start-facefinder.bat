@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Setting up FaceFinder for the first time...
  py -m venv .venv
  call .venv\Scripts\python.exe -m pip install --upgrade pip
  call .venv\Scripts\python.exe -m pip install -r facefinder-requirements.txt
  if errorlevel 1 goto :error
)
echo Starting FaceFinder at http://127.0.0.1:5173
start "" http://127.0.0.1:5173
call .venv\Scripts\python.exe facefinder.py
goto :eof
:error
echo Setup failed. Check your internet connection, then run this file again.
pause
