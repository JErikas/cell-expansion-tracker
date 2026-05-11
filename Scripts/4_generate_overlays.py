import sys
from datetime import datetime
from pathlib import Path

import tifffile
import numpy as np

from tqdm import tqdm

from skimage.color import label2rgb
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

    tracked_mask_files = sorted(
        dir_tracked_masks.glob("*_tracked_mask.tif")
    )

    print(f"Found {len(tracked_mask_files)} tracked masks.\n")

    for mask_path in tqdm(tracked_mask_files, desc="Generating overlays"):

        try:

            # Directly recover original tif name
            original_tif_name = (
                mask_path.name
                .replace("_tracked_mask.tif", ".tif")
            )

            image_path = dir_images / original_tif_name

            if not image_path.exists():

                print(f"[MISSING IMAGE] {original_tif_name}")
                continue

            image = tifffile.imread(image_path)

            tracked_mask = tifffile.imread(mask_path)

            image_norm = rescale_intensity(
                image,
                in_range="image",
                out_range=(0, 1)
            )

            # SAME TRACK_ID = SAME COLOR
            overlay = label2rgb(
                tracked_mask,
                image=image_norm,
                bg_label=0,
                alpha=config.OVERLAY_OPACITY
            )

            overlay_uint8 = (
                overlay * 255
            ).astype(np.uint8)

            save_name = (
                mask_path.stem.replace(
                    "_tracked_mask",
                    "_overlay"
                ) + ".tif"
            )

            tifffile.imwrite(
                dir_overlays / save_name,
                overlay_uint8
            )

        except Exception as e:

            print(f"[ERROR] {mask_path.name}: {e}")

    print("\nOverlay generation complete.")


if __name__ == "__main__":
    run()