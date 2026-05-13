import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import sys
from datetime import datetime
from pathlib import Path
import gc
import torch
import numpy as np
import tifffile
from tqdm import tqdm
from cellpose import models, core, io
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
    cropped = mask[margin_px:h - margin_px, margin_px:w - margin_px]
    cleaned = clear_border(cropped)
    result = np.zeros_like(mask)
    result[margin_px:h - margin_px, margin_px:w - margin_px] = cleaned
    return result

def run():
    date_prefix = config.TARGET_EXP_FOLDER[:10].replace("-", "")
    output_dir = Path(config.PROCESSED_DATA_DIR) / f"{date_prefix}_Timelapse"
    
    # Read from and save to the same combined folder
    dir_images_seg = output_dir / "1_images_and_segmentation"

    sys.stdout = Logger(output_dir / "Log_Segmentation.txt")

    print(f"=== Starting Segmentation {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")

    use_gpu = core.use_gpu()

    if config.USE_CUSTOM_CELLPOSE_MODEL:
        model_path = Path(config.BASE_DIR) / "Models" / config.CUSTOM_MODEL_FILENAME
        if not model_path.exists():
            print(f"[FATAL ERROR] Custom model not found at: {model_path}")
            sys.exit(1)
        model = models.CellposeModel(gpu=use_gpu, pretrained_model=str(model_path))
    else:
        model = models.CellposeModel(gpu=use_gpu, pretrained_model=config.BUILTIN_MODEL_NAME)

    files = sorted(dir_images_seg.glob("*.tif"))
    print(f"Found {len(files)} images.\n")

    for img_path in tqdm(files, desc="Segmenting"):
        try:
            img = tifffile.imread(img_path)
            masks, flows, styles = model.eval(img, diameter=config.CELLPOSE_DIAMETER)

            if config.REMOVE_BORDER_OBJECTS:
                masks = remove_border_masks(masks, margin_px=config.BORDER_MARGIN_PX)

            # Pass strictly the core positional arguments to avoid any API keyword mismatches
            # This directly outputs the properly formatted _seg.npy next to the .tif
            io.masks_flows_to_seg([img], [masks], [flows], [str(img_path)])

        except Exception as e:
            print(f"[ERROR] {img_path.name}: {e}")

        finally:
            gc.collect()
            if use_gpu:
                torch.cuda.empty_cache()

    print("\nSegmentation complete.")

if __name__ == "__main__":
    run()