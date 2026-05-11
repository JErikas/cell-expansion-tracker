import os
from pathlib import Path

# =======================
# DYNAMIC PATHS
# =======================
# Dynamically resolves the base directory based on where this config.py is located.
# It assumes config.py is inside the 'Scripts' folder.
SCRIPTS_DIR_PATH = Path(__file__).resolve().parent
BASE_DIR_PATH = SCRIPTS_DIR_PATH.parent

BASE_DIR = str(BASE_DIR_PATH)
SCRIPTS_DIR = str(SCRIPTS_DIR_PATH)
RAW_DATA_DIR = str(BASE_DIR_PATH / "Raw_Data")
PROCESSED_DATA_DIR = str(BASE_DIR_PATH / "Processed_Data")

# =======================
# CURRENT EXPERIMENT
# =======================
TARGET_EXP_FOLDER = "2026-05-09 EP"

# =======================
# MICROSCOPY SETTINGS
# =======================
MICRONS_PER_PIXEL = 0.2738
CHANNEL_CELL_INDEX = 0

# =======================
# FRAME SAMPLING
# =======================
NUM_INTERMEDIATE_FRAMES = 5

# =======================
# CELLPOSE SETTINGS
# =======================
CELLPOSE_DIAMETER = 130

# =======================
# TRACKING
# =======================
MAX_TRACKING_DISTANCE_PX = 60

# =======================
# OVERLAYS
# =======================
SAVE_TRACKED_OVERLAYS = True
OVERLAY_OPACITY = 0.35

# =======================
# BORDER FILTERING
# =======================
# Remove masks touching image border
REMOVE_BORDER_OBJECTS = True

# Distance from image edge in pixels
# Any mask touching this border region is removed
BORDER_MARGIN_PX = 10