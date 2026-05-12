#!/bin/bash

cd "$(dirname "$0")"
echo "Starting Timelapse Pipeline..."

eval "$(conda shell.bash hook)"
conda activate timelapse_env

python 0_run_pipeline.py

echo ""
read -p "Press Enter to exit..."