@echo off
setlocal
cd /d "%~dp0.."
python -m src.setup_binaries
pause
