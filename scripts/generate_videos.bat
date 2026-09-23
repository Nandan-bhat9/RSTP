@echo off
setlocal
cd /d "%~dp0.."
python -m src.generate_test_videos
pause
