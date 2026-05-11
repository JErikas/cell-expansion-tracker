import sys
import re
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


MASK_REGEX = re.compile(
    r"^(?P<media>STD_EP|STD_SN_EP)_(?P<voltage>[0-9.]+kV)_(?P<imgid>.+?)_F(?P<frame>\d{2})_mask$"
)


def parse_mask_name(mask_path):

    stem = mask_path.stem

    match = MASK_REGEX.match(stem)

    if not match:
        return None

    d = match.groupdict()

    media_raw = d["media"]

    if media_raw == "STD_SN_EP":
        media = "SN"
    else:
        media = "STD"

    voltage = float(d["voltage"].replace("kV", ""))

    return {
        "media": media,
        "voltage": voltage,
        "imgid": d["imgid"],
        "frame": int(d["frame"])
    }


def sequential_tracking(frame_masks):

    tracked_masks = []

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

        current_centroids = np.array([
            tracks[t]["centroid"]
            for t in track_ids
        ])

        next_centroids = np.array([
            p.centroid
            for p in props_next
        ])

        dists = cdist(current_centroids, next_centroids)

        candidate_pairs = []

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

            if i in used_tracks:
                continue

            if j in used_next:
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

    dir_masks = output_dir / "2_masks"

    dir_tracked_masks = output_dir / "3_tracked_masks"
    dir_tracked_masks.mkdir(parents=True, exist_ok=True)

    dir_results = output_dir / "4_results"
    dir_results.mkdir(parents=True, exist_ok=True)

    sys.stdout = Logger(output_dir / "Log_Tracking.txt")

    print(f"=== Starting Tracking {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")

    mask_files = sorted(dir_masks.glob("*_mask.tif"))

    groups = {}

    for p in mask_files:

        parsed = parse_mask_name(p)

        if parsed is None:
            continue

        key = (
            parsed["media"],
            parsed["voltage"],
            parsed["imgid"]
        )

        if key not in groups:
            groups[key] = []

        groups[key].append((parsed["frame"], p))

    single_cell_data = []

    image_average_data = []

    for (media, voltage, imgid), items in tqdm(groups.items(), desc="Tracking"):

        items = sorted(items, key=lambda x: x[0])

        frame_masks = []

        original_names = []

        for frame_num, path in items:

            mask = tifffile.imread(path)

            frame_masks.append(mask)

            # ORIGINAL tif naming preserved
            original_name = path.stem.replace("_mask", "")

            original_names.append(original_name)

        tracked_masks, final_tracks = sequential_tracking(frame_masks)

        # =====================================================
        # SAVE TRACKED MASKS
        # =====================================================

        for idx, tracked_mask in enumerate(tracked_masks):

            save_name = f"{original_names[idx]}_tracked_mask.tif"

            tifffile.imwrite(
                dir_tracked_masks / save_name,
                tracked_mask.astype(np.uint16)
            )

        # =====================================================
        # SAVE DATA
        # =====================================================

        img_area_t0 = []
        img_area_tf = []
        img_delta = []
        img_pct = []

        for track_id, data in final_tracks.items():

            area_t0 = data["initial_area"] * (config.MICRONS_PER_PIXEL ** 2)

            area_tf = data["latest_area"] * (config.MICRONS_PER_PIXEL ** 2)

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

    df_cells.to_csv(
        dir_results / f"{date_prefix}_Single_Cells_Tracking.csv",
        index=False
    )

    df_images.to_csv(
        dir_results / f"{date_prefix}_Image_Averages.csv",
        index=False
    )

    print(f"Tracked cells: {len(df_cells)}")


if __name__ == "__main__":
    run()