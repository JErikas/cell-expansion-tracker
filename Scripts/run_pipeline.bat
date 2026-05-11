@echo off
echo Starting Timelapse Pipeline...

:: Navigate to the directory where this script is located
cd /d "%~dp0"

:: Activate the conda environment
call conda activate timelapse_env

:: Run the pipeline
python 0_run_pipeline.py

echo.
pause