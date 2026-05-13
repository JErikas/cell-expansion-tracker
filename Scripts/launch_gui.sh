#!/bin/bash

# Navigate to the script directory
cd "$(dirname "$0")"

echo "Launching Cellpose GUI..."

# Activate environment
eval "$(conda shell.bash hook)"
conda activate timelapse_env

# Set the universal bug-fix variables
export QT_API=pyside6
export KMP_DUPLICATE_LIB_OK=TRUE

# Run Cellpose
python -m cellpose