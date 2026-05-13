import sys
import re
import json
from datetime import datetime
from pathlib import Path
import numpy as np
import tifffile
import pandas as pd
from scipy.spatial.distance import cdist
from skimage.measure import regionprops
from tqdm import tqdm
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

def parse_seg_name(seg_path):
    stem = seg_path.name.replace("_seg.npy", "")
    
    media = None
    all_media_labels = list(config.MEDIA_CONDITIONS.values()) + [config.DEFAULT_MEDIA_NAME]
    for label in all_media_labels:
        if stem.startswith(label + "_"):
            media = label
            break
            
    if not media: return None
    
    rest = stem[len(media)+1:]
    v_match = re.search(r'^([0-9.]+kV)_', rest)
    if not v_match: return None
    voltage_str = v_match.group(1)
    voltage = float(voltage_str.replace("kV", ""))
    
    rest = rest[len(voltage_str)+1:]
    f_match = re.search(r'_F(\d{2})$', rest)
    if not f_match: return None
    frame = int(f_match.group(1))
    
    imgid = rest[:f_match.start()]
    
    return {
        "media": media,
        "voltage": voltage,
        "imgid": imgid,
        "frame": frame
    }

def sequential_tracking(frame_masks):
    tracked_masks =[]
    props0 = regionprops(frame_masks[0])
    tracks = {}
    relabeled0 = np.zeros_like(frame_masks[0], dtype=np.uint16)
    next_track_id = 1

    for p in props0:
        tracks[next_track_id] = {
            "centroid": p.centroid,
            "initial_area": p.area,
            "latest_area": p.area
        }
        relabeled0[frame_masks[0] == p.label] = next_track_id
        next_track_id += 1

    tracked_masks.append(relabeled0)

    for frame_idx in range(1, len(frame_masks)):
        next_mask = frame_masks[frame_idx]
        props_next = regionprops(next_mask)
        relabeled_next = np.zeros_like(next_mask, dtype=np.uint16)

        if len(props_next) == 0 or len(tracks) == 0:
            tracked_masks.append(relabeled_next)
            tracks = {}
            continue

        track_ids = list(tracks.keys())
        current_centroids = np.array([tracks[t]["centroid"] for t in track_ids])
        next_centroids = np.array([p.centroid for p in props_next])
        dists = cdist(current_centroids, next_centroids)

        candidate_pairs =[]
        for i in range(dists.shape[0]):
            for j in range(dists.shape[1]):
                candidate_pairs.append((dists[i, j], i, j))

        candidate_pairs.sort(key=lambda x: x[0])

        used_tracks = set()
        used_next = set()
        updated_tracks = {}

        for dist, i, j in candidate_pairs:
            if dist > config.MAX_TRACKING_DISTANCE_PX:
                break
            if i in used_tracks or j in used_next:
                continue

            track_id = track_ids[i]
            prop = props_next[j]
            relabeled_next[next_mask == prop.label] = track_id

            updated_tracks[track_id] = {
                "centroid": prop.centroid,
                "initial_area": tracks[track_id]["initial_area"],
                "latest_area": prop.area
            }
            used_tracks.add(i)
            used_next.add(j)

        tracked_masks.append(relabeled_next)
        tracks = updated_tracks

    return tracked_masks, tracks

def run():
    date_prefix = config.TARGET_EXP_FOLDER[:10].replace("-", "")
    output_dir = Path(config.PROCESSED_DATA_DIR) / f"{date_prefix}_Timelapse"
    
    dir_images_seg = output_dir / "1_images_and_segmentation"
    
    dir_tracked_masks = output_dir / "2_tracked_masks"
    dir_tracked_masks.mkdir(parents=True, exist_ok=True)

    dir_results = output_dir / "3_results"
    dir_results.mkdir(parents=True, exist_ok=True)

    sys.stdout = Logger(output_dir / "Log_Tracking.txt")

    print(f"=== Starting Tracking {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")

    scaling_file = output_dir / "scaling_log.json"
    scaling_dict = {}
    if scaling_file.exists():
        with open(scaling_file, "r") as f:
            scaling_dict = json.load(f)

    # Read .npy files out of the unified folder
    mask_files = sorted(dir_images_seg.glob("*_seg.npy"))
    groups = {}

    for p in mask_files:
        parsed = parse_seg_name(p)
        if parsed is None:
            continue
        key = (parsed["media"], parsed["voltage"], parsed["imgid"])
        if key not in groups:
            groups[key] = []
        groups[key].append((parsed["frame"], p))

    single_cell_data = []
    image_average_data =[]

    for (media, voltage, imgid), items in tqdm(groups.items(), desc="Tracking"):
        items = sorted(items, key=lambda x: x[0])
        frame_masks =[]
        original_names =[]

        for frame_num, path in items:
            seg_data = np.load(path, allow_pickle=True).item()
            mask = seg_data['masks']
            frame_masks.append(mask)
            original_names.append(path.name.replace("_seg.npy", ""))

        tif_key = f"{original_names[0]}.tif"
        mpp = scaling_dict.get(tif_key, config.FALLBACK_MICRONS_PER_PIXEL)
        pixel_res = 1.0 / mpp
        res_tuple = (pixel_res, pixel_res)

        tracked_masks, final_tracks = sequential_tracking(frame_masks)

        for idx, tracked_mask in enumerate(tracked_masks):
            save_name = f"{original_names[idx]}_tracked_mask.tif"
            tifffile.imwrite(
                dir_tracked_masks / save_name, 
                tracked_mask.astype(np.uint16),
                imagej=True,
                resolution=res_tuple,
                metadata={'unit': 'um'}
            )

        img_area_t0 = []
        img_area_tf =[]
        img_delta = []
        img_pct =[]

        for track_id, data in final_tracks.items():
            area_t0 = data["initial_area"] * (mpp ** 2)
            area_tf = data["latest_area"] * (mpp ** 2)
            delta = area_tf - area_t0
            pct = (delta / area_t0) * 100

            single_cell_data.append({
                "Image_ID": imgid,
                "Media": media,
                "Voltage": voltage,
                "Track_ID": track_id,
                "Area_T0_um2": round(area_t0, 2),
                "Area_Tfinal_um2": round(area_tf, 2),
                "Delta_Area_um2": round(delta, 2),
                "Percent_Change": round(pct, 2)
            })

            img_area_t0.append(area_t0)
            img_area_tf.append(area_tf)
            img_delta.append(delta)
            img_pct.append(pct)

        if len(img_pct) > 0:
            image_average_data.append({
                "Image_ID": imgid,
                "Media": media,
                "Voltage": voltage,
                "Tracked_Cells": len(img_pct),
                "Area_T0_um2": round(np.mean(img_area_t0), 2),
                "Area_Tfinal_um2": round(np.mean(img_area_tf), 2),
                "Delta_Area_um2": round(np.mean(img_delta), 2),
                "Percent_Change": round(np.mean(img_pct), 2)
            })

    df_cells = pd.DataFrame(single_cell_data)
    df_images = pd.DataFrame(image_average_data)

    df_cells.to_csv(dir_results / f"{date_prefix}_Single_Cells_Tracking.csv", index=False)
    df_images.to_csv(dir_results / f"{date_prefix}_Image_Averages.csv", index=False)

    print(f"Tracked cells: {len(df_cells)}")

if __name__ == "__main__":
    run()