import os
from pathlib import Path

# =======================
# DYNAMIC PATHS
# =======================
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
# MEDIA CONDITIONS 
# =======================
# Keys must be lowercase strings to look for in folder names.
# Values are the readable labels that will appear in your CSVs and Plots.
MEDIA_CONDITIONS = {
    "sn": "Supplemented_Media",
    "std": "Standard_Media"
    # You can easily add more here, e.g., "drugx": "Drug_X_Treatment"
}
DEFAULT_MEDIA_NAME = "Unknown_Media"

# =======================
# MICROSCOPY SETTINGS
# =======================
FALLBACK_MICRONS_PER_PIXEL = 0.1369048
CHANNEL_CELL_INDEX = 0
NUM_INTERMEDIATE_FRAMES = 5

# =======================
# CELLPOSE MODEL SETTINGS
# =======================
USE_CUSTOM_CELLPOSE_MODEL = False
CUSTOM_MODEL_FILENAME = "my_custom_model_file" 
BUILTIN_MODEL_NAME = "cyto3"
CELLPOSE_DIAMETER = 130

# =======================
# TRACKING SETTINGS
# =======================
MAX_TRACKING_DISTANCE_PX = 60

# =======================
# OVERLAY SETTINGS
# =======================
SAVE_TRACKED_OVERLAYS = True
OVERLAY_OPACITY = 0.35

# =======================
# BORDER FILTERING SETTINGS
# =======================
REMOVE_BORDER_OBJECTS = True
BORDER_MARGIN_PX = 10