@echo off
where pythonw.exe >nul 2>nul
if not errorlevel 1 (
    start "" pythonw.exe "%~dp0launch.py"
    exit /b
)
where pyw.exe >nul 2>nul
if not errorlevel 1 (
    start "" pyw.exe -3 "%~dp0launch.py"
    exit /b
)
echo Python 3 is required. Install Python, or open dist\index.html for viewing.
pause
