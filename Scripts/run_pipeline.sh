#!/bin/bash

# Navigate to the directory where this script is located
cd "$(dirname "$0")"

echo "Starting Timelapse Pipeline..."

# Initialize conda for bash script execution safely
eval "$(conda shell.bash hook)"

# Activate environment
conda activate timelapse_env

# Run pipeline
python 0_run_pipeline.py

echo ""
read -p "Press Enter to exit..."