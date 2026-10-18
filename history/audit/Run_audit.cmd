@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Please create the Python 3.12 environment as described in README.md.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" scripts\run_offline.py
if errorlevel 1 (
  echo Audit failed. Review the output above.
  pause
  exit /b 1
)
echo Audit finished. Open the HTML report in the reports folder.
pause
