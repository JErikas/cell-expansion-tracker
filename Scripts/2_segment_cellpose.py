import sys
from datetime import datetime
from pathlib import Path

import gc
import torch

import numpy as np
import tifffile

from tqdm import tqdm

from cellpose import models, core

from skimage.segmentation import clear_border

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


def remove_border_masks(mask, margin_px=0):

    if margin_px <= 0:

        return clear_border(mask)

    h, w = mask.shape

    cropped = mask[
        margin_px:h - margin_px,
        margin_px:w - margin_px
    ]

    cleaned = clear_border(cropped)

    result = np.zeros_like(mask)

    result[
        margin_px:h - margin_px,
        margin_px:w - margin_px
    ] = cleaned

    return result


def run():

    date_prefix = config.TARGET_EXP_FOLDER[:10].replace("-", "")

    output_dir = Path(config.PROCESSED_DATA_DIR) / f"{date_prefix}_Timelapse"

    dir_tif = output_dir / "1_tif_images"

    dir_masks = output_dir / "2_masks"
    dir_masks.mkdir(parents=True, exist_ok=True)

    sys.stdout = Logger(output_dir / "Log_Segmentation.txt")

    print(f"=== Starting Segmentation {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")

    use_gpu = core.use_gpu()

    model = models.CellposeModel(
        gpu=use_gpu,
        pretrained_model='cyto3'
    )

    files = sorted(dir_tif.glob("*.tif"))

    print(f"Found {len(files)} images.\n")

    for img_path in tqdm(files, desc="Segmenting"):

        try:

            img = tifffile.imread(img_path)

            masks, flows, styles = model.eval(
                img,
                diameter=config.CELLPOSE_DIAMETER
            )

            if config.REMOVE_BORDER_OBJECTS:

                masks = remove_border_masks(
                    masks,
                    margin_px=config.BORDER_MARGIN_PX
                )

            save_name = f"{img_path.stem}_mask.tif"

            tifffile.imwrite(
                dir_masks / save_name,
                masks.astype(np.uint16)
            )

        except Exception as e:

            print(f"[ERROR] {img_path.name}: {e}")

        finally:

            gc.collect()

            if use_gpu:
                torch.cuda.empty_cache()

    print("\nSegmentation complete.")


if __name__ == "__main__":
    run()