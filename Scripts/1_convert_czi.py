import sys
import re
import json
from datetime import datetime
import numpy as np
import tifffile
from aicspylibczi import CziFile
from tqdm import tqdm
from pathlib import Path
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

def extract_metadata(file_path):
    path_obj = Path(file_path)
    filename = path_obj.stem
    parts = path_obj.parts

    media_type = config.DEFAULT_MEDIA_NAME
    voltage = "Unknown_Voltage"

    for folder in parts[-4:-1]:
        folder_l = folder.lower()

        # Dynamically check for media conditions defined in config
        for key, label in config.MEDIA_CONDITIONS.items():
            if key in folder_l:
                media_type = label
                break

        v_match = re.search(r'(\d+[.,]?\d*)\s*kv', folder_l, re.IGNORECASE)
        if v_match:
            voltage_str = v_match.group(1).replace(",", ".")
            voltage = f"{voltage_str}kV"

    return media_type, voltage, filename

def get_pixel_size_um(czi):
    try:
        x_node = czi.meta.find(".//Scaling/Items/Distance[@Id='X']/Value")
        if x_node is not None:
            meters_per_pixel = float(x_node.text)
            return meters_per_pixel * 1e6
    except Exception:
        pass
    return config.FALLBACK_MICRONS_PER_PIXEL

def get_frame_indices(total_frames):
    if total_frames <= 1:
        return np.array([0])
    if config.NUM_INTERMEDIATE_FRAMES <= 0:
        return np.array([0, total_frames - 1])
    indices = np.linspace(
        0, total_frames - 1, config.NUM_INTERMEDIATE_FRAMES + 2, dtype=int
    )
    return np.unique(indices)

def run():
    raw_path = Path(config.RAW_DATA_DIR) / config.TARGET_EXP_FOLDER
    date_prefix = config.TARGET_EXP_FOLDER[:10].replace("-", "")
    output_dir = Path(config.PROCESSED_DATA_DIR) / f"{date_prefix}_Timelapse"

    dir_tif = output_dir / "1_tif_images"
    dir_tif.mkdir(parents=True, exist_ok=True)

    sys.stdout = Logger(output_dir / "Log_Conversion.txt")
    print(f"=== Starting Conversion {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")

    files = sorted(raw_path.rglob("*.czi"))
    print(f"Found {len(files)} files.\n")

    scaling_dict = {}

    for czi_path in tqdm(files, desc="Converting"):
        try:
            media, voltage, fname = extract_metadata(czi_path)
            czi = CziFile(str(czi_path))
            
            mpp = get_pixel_size_um(czi)
            pixel_res = 1.0 / mpp
            res_tuple = (pixel_res, pixel_res)
            
            img_data, shp = czi.read_image()
            img = np.squeeze(img_data)

            if img.ndim == 4:
                img = img[:, config.CHANNEL_CELL_INDEX, :, :]

            total_frames = img.shape[0]
            indices = get_frame_indices(total_frames)

            for i, frame_idx in enumerate(indices):
                frame_label = f"F{i:02d}"
                out_name = f"{media}_{voltage}_{fname}_{frame_label}.tif"
                
                scaling_dict[out_name] = mpp
                
                tifffile.imwrite(
                    dir_tif / out_name, 
                    img[frame_idx],
                    imagej=True,
                    resolution=res_tuple,
                    metadata={'unit': 'um'}
                )

            tqdm.write(f"[OK] {fname}: extracted {len(indices)} frames (Scale: {mpp:.4f} um/px)")

        except Exception as e:
            tqdm.write(f"[ERROR] {czi_path.name}: {e}")

    with open(output_dir / "scaling_log.json", "w") as f:
        json.dump(scaling_dict, f, indent=4)

if __name__ == "__main__":
    run()