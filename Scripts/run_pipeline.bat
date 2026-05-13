@echo off
echo Starting Timelapse Pipeline...

cd /d "%~dp0"
call conda activate timelapse_env

:: Prevent OpenMP crash during automated segmentation
set KMP_DUPLICATE_LIB_OK=TRUE

python 0_run_pipeline.py

echo.
pause