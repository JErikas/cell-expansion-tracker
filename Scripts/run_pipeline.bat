@echo off
echo Starting Timelapse Pipeline...

cd /d "%~dp0"

call conda activate timelapse_env
python 0_run_pipeline.py

echo.
pause