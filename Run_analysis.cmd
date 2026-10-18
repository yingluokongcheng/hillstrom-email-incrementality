@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Create the Python 3.12 environment as described in README.md.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" scripts\run_offline.py
if errorlevel 1 (
  echo Analysis stopped. Review the error above.
  pause
  exit /b 1
)
echo Completed. Open the HTML report in reports.
pause
