import sys
import json
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
    cropped = mask[margin_px:h - margin_px, margin_px:w - margin_px]
    cleaned = clear_border(cropped)

    result = np.zeros_like(mask)
    result[margin_px:h - margin_px, margin_px:w - margin_px] = cleaned

    return result

def run():

    date_prefix = config.TARGET_EXP_FOLDER[:10].replace("-", "")
    output_dir = Path(config.PROCESSED_DATA_DIR) / f"{date_prefix}_Timelapse"
    dir_tif = output_dir / "1_tif_images"
    dir_masks = output_dir / "2_masks"
    dir_masks.mkdir(parents=True, exist_ok=True)

    sys.stdout = Logger(output_dir / "Log_Segmentation.txt")

    print(f"=== Starting Segmentation {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")

    scaling_file = output_dir / "scaling_log.json"
    scaling_dict = {}
    if scaling_file.exists():
        with open(scaling_file, "r") as f:
            scaling_dict = json.load(f)

    use_gpu = core.use_gpu()

    if config.USE_CUSTOM_CELLPOSE_MODEL:
        model_path = Path(config.BASE_DIR) / "Models" / config.CUSTOM_MODEL_FILENAME
        if not model_path.exists():
            print(f"[FATAL ERROR] Custom model not found at: {model_path}")
            sys.exit(1)
        
        print(f"Loading custom model: {config.CUSTOM_MODEL_FILENAME}")
        model = models.CellposeModel(gpu=use_gpu, pretrained_model=str(model_path))
    else:
        print(f"Loading built-in model: {config.BUILTIN_MODEL_NAME}")
        model = models.CellposeModel(gpu=use_gpu, pretrained_model=config.BUILTIN_MODEL_NAME)

    files = sorted(dir_tif.glob("*.tif"))
    print(f"Found {len(files)} images.\n")

    for img_path in tqdm(files, desc="Segmenting"):
        try:
            mpp = scaling_dict.get(img_path.name, config.FALLBACK_MICRONS_PER_PIXEL)
            pixel_res = 1.0 / mpp
            res_tuple = (pixel_res, pixel_res)

            img = tifffile.imread(img_path)
            masks, flows, styles = model.eval(img, diameter=config.CELLPOSE_DIAMETER)

            if config.REMOVE_BORDER_OBJECTS:
                masks = remove_border_masks(masks, margin_px=config.BORDER_MARGIN_PX)

            save_name = f"{img_path.stem}_mask.tif"
            
            tifffile.imwrite(
                dir_masks / save_name, 
                masks.astype(np.uint16),
                imagej=True,
                resolution=res_tuple,
                metadata={'unit': 'um'}
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