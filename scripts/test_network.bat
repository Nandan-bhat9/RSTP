@echo off
setlocal
cd /d "%~dp0.."

echo ===================================================
echo KAVACH RTSP Network and Stream Health Diagnostic
echo ===================================================
echo.
set /p TARGET_HOST="Enter Simulator IP/Host (press Enter for local auto-detect): "

if "%TARGET_HOST%"=="" (
    python -m src.main health
) else (
    python -m src.main health --host %TARGET_HOST%
)

echo.
pause
