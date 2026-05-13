@echo off
echo Launching Cellpose GUI...

:: Navigate to the script directory
cd /d "%~dp0"

:: Activate environment
call conda activate timelapse_env

:: Set the universal bug-fix variables
set QT_API=pyside6
set KMP_DUPLICATE_LIB_OK=TRUE

:: Run Cellpose
python -m cellpose