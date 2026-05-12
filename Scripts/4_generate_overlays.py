import sys
import json
from datetime import datetime
from pathlib import Path
import tifffile
import numpy as np
import colorsys  # NEW: Used for distinct color generation
from tqdm import tqdm
from skimage.exposure import rescale_intensity
import config

class Logger(object):
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, "a", encoding="utf-8")
    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush()
    def flush(self):
        pass

def run():
    if not config.SAVE_TRACKED_OVERLAYS:
        print("Tracked overlays disabled.")
        return

    date_prefix = config.TARGET_EXP_FOLDER[:10].replace("-", "")
    output_dir = Path(config.PROCESSED_DATA_DIR) / f"{date_prefix}_Timelapse"
    dir_images = output_dir / "1_tif_images"
    dir_tracked_masks = output_dir / "3_tracked_masks"
    dir_overlays = output_dir / "5_tracked_overlays"
    dir_overlays.mkdir(parents=True, exist_ok=True)

    sys.stdout = Logger(output_dir / "Log_Overlays.txt")

    print(f"=== Starting Overlay Generation {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")

    scaling_file = output_dir / "scaling_log.json"
    scaling_dict = {}
    if scaling_file.exists():
        with open(scaling_file, "r") as f:
            scaling_dict = json.load(f)

    tracked_mask_files = sorted(dir_tracked_masks.glob("*_tracked_mask.tif"))
    print(f"Found {len(tracked_mask_files)} tracked masks.\n")

    # =========================================================
    # HIGH-CONTRAST HSV COLOR GENERATION
    # =========================================================
    np.random.seed(42)
    MAX_LABELS = 65536
    fixed_colors = np.zeros((MAX_LABELS, 3))
    
    # By forcing high saturation (0.6-1.0) and brightness (0.7-1.0) using HSV,
    # we avoid "muddy" or dark gray colors that blend in with the background.
    for i in range(1, MAX_LABELS):
        hue = np.random.uniform(0.0, 1.0)
        sat = np.random.uniform(0.6, 1.0)
        val = np.random.uniform(0.7, 1.0)
        fixed_colors[i] = colorsys.hsv_to_rgb(hue, sat, val)
        
    fixed_colors[0] = [0, 0, 0] # Background is strictly black

    for mask_path in tqdm(tracked_mask_files, desc="Generating overlays"):
        try:
            original_tif_name = mask_path.name.replace("_tracked_mask.tif", ".tif")
            image_path = dir_images / original_tif_name

            if not image_path.exists():
                print(f"[MISSING IMAGE] {original_tif_name}")
                continue

            mpp = scaling_dict.get(original_tif_name, config.FALLBACK_MICRONS_PER_PIXEL)
            pixel_res = 1.0 / mpp
            res_tuple = (pixel_res, pixel_res)

            image = tifffile.imread(image_path)
            tracked_mask = tifffile.imread(mask_path)

            image_norm = rescale_intensity(image, in_range="image", out_range=(0, 1))

            # Blend image with fixed vibrant colors
            image_rgb = np.dstack((image_norm, image_norm, image_norm))
            mask_colors = fixed_colors[tracked_mask]
            is_foreground = np.expand_dims(tracked_mask > 0, axis=-1)
            
            overlay = np.where(
                is_foreground,
                (image_rgb * (1.0 - config.OVERLAY_OPACITY)) + (mask_colors * config.OVERLAY_OPACITY),
                image_rgb
            )

            overlay_uint8 = (overlay * 255).astype(np.uint8)
            save_name = mask_path.stem.replace("_tracked_mask", "_overlay") + ".tif"

            tifffile.imwrite(
                dir_overlays / save_name, 
                overlay_uint8,
                imagej=True,
                resolution=res_tuple,
                metadata={'unit': 'um'}
            )

        except Exception as e:
            print(f"[ERROR] {mask_path.name}: {e}")

    print("\nOverlay generation complete.")

if __name__ == "__main__":
    run()