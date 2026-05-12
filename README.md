# Cell Expansion Tracker Pipeline

This automated pipeline processes raw CZI microscopy data to extract frames, segment cells using Cellpose, track individual cells across a timelapse, and plot their physical expansion.

## 1. Project Folder Structure

Ensure your project is organized as follows:

```text
Cell_Expansion_Tracker/
│
├── Models/                # Place custom Cellpose model files here
├── Processed_Data/        # Pipeline outputs will be saved here automatically
├── Raw_Data/              # Place your raw .czi experiment folders here
│   └── 2026-05-09 EP/     # Example Experiment Folder
│
└── Scripts/               # Pipeline scripts and environment files
    ├── config.py
    ├── 0_run_pipeline.py
    ├── ... (other scripts)

```
## 2. One-Time Setup and Installation

This pipeline requires **Miniconda** (a lightweight version of Python and the Conda package manager) to manage the necessary biological imaging libraries.

### Step 1: Install Miniconda

#### **For Windows:**

1. Download the **Miniconda Windows 64-bit installer** from the [Official Download Page](https://docs.conda.io/en/latest/miniconda.html).
2. Run the `.exe` installer.
3. **Important:** During installation, it is highly recommended to check the box **"Add Miniconda3 to my PATH environment variable"**. This allows the `.bat` launcher to find Python automatically.
4. If you did NOT add it to PATH, you must run all commands via the **"Anaconda Prompt"** found in your Start Menu.

#### **For macOS / Linux:**

1. Download the **Miniconda installer script** (`.sh` file) for your architecture (Intel or Apple M-series).
2. Open your Terminal and navigate to your Downloads folder:
```bash
cd ~/Downloads
```




3. Run the installer script:

```bash
bash Miniconda3-latest-MacOSX-arm64.sh  # (Example filename)
```

4. Follow the prompts. When asked "Do you wish the installer to initialize Miniconda3?", type **yes**.
5. Restart your Terminal for the changes to take effect.

---

### Step 2: Create the Environment

Once Miniconda is installed, you need to install the specific libraries (Cellpose, Tifffile, etc.) required for this pipeline.

#### **For Windows:**

1. Open the **Command Prompt** (or Anaconda Prompt).
2. Navigate to your project's `Scripts` folder:
```cmd
cd /d C:\Path\To\Your\Cell_Expansion_Tracker\Scripts
```


3. Create the environment:
```cmd
conda env create -f environment.yml
```

#### **For macOS / Linux:**

1. Open the **Terminal**.
2. Navigate to your project's `Scripts` folder:
```bash
cd ~/Path/To/Your/Cell_Expansion_Tracker/Scripts
```


3. Create the environment:
```bash
conda env create -f environment.yml
```




4. Give the launcher script permission to run:
```bash
chmod +x run_pipeline.sh
```

## 3. Data Formatting Requirements

The pipeline automatically reads experimental conditions from your folder names.

### Metadata Extraction Rules

* **Experiment Date**: The main experiment folder must begin with a 10-character date (`YYYY-MM-DD`).
* **Voltage**: The folder name must contain a number followed by **kV** (case-insensitive). Decimals (`.`) or commas (`,`) are both accepted.
* **Media Type**: The script searches for keywords defined in your `config.py` (e.g., `sn` or `std`).

### Examples of Perfectly Formatted Directories:

1. Raw_Data/**2026-05-09**/**STD** **1.5kV**/202609210844-01.czi
2. Raw_Data/**2026-05-09** EP/STD **SN** EP/**4,2 KV**-CM-8HV/2026-05-09/202609210552-01.czi

*Note: The **bolded features are necessary** for the script to correctly extract the experiment date, media type, and voltage.*

## 4. Configuration Variables Guide (`config.py`)

All settings are managed in `Scripts/config.py`. Below is an explanation of every parameter.

### Paths & Experiment

* `TARGET_EXP_FOLDER`: The exact name of your main experiment folder in `Raw_Data/`.
* `RAW_DATA_DIR` / `PROCESSED_DATA_DIR`: Automatically calculated paths for input and output.

### Media Conditions

* `MEDIA_CONDITIONS`: A dictionary mapping folder keywords to readable labels.
* *Example*: `"sn": "Supplemented_Media"` means any folder containing "sn" will be labeled "Supplemented Media" in results.


* `DEFAULT_MEDIA_NAME`: The label used if no keywords from `MEDIA_CONDITIONS` are found in the folder path.

### Microscopy Settings

* `FALLBACK_MICRONS_PER_PIXEL`: Used if the `.czi` file metadata is missing.
> **How to check:** In ImageJ/Fiji, open an image and go to **Image > Properties > Pixel width**.


* `CHANNEL_CELL_INDEX`: The channel index (starting from 0) containing the cell signal.
* `NUM_INTERMEDIATE_FRAMES`: Number of frames to extract *between* the first and last image. (e.g., 5 frames results in 7 total images per timelapse).

### Cellpose Model Settings

* `USE_CUSTOM_CELLPOSE_MODEL`: Set to `True` to use a self-trained model.
* `CUSTOM_MODEL_FILENAME`: The filename of your model (placed in the `Models/` folder).
* `BUILTIN_MODEL_NAME`: The Cellpose model to use (default is `cyto3`).
* `CELLPOSE_DIAMETER`: Expected average cell diameter in pixels.

### Tracking Settings

* `MAX_TRACKING_DISTANCE_PX`: The maximum distance (in pixels) a cell can move between sampled frames to be considered the same cell.

### Overlay Settings

* `SAVE_TRACKED_OVERLAYS`: Enables/disables the generation of visual validation images.
* `OVERLAY_OPACITY`: Transparency of the mask colors (0.0 to 1.0). High-contrast HSV colors are used to ensure cell IDs are visually distinct.

### Border Filtering Settings

* `REMOVE_BORDER_OBJECTS`: If `True`, cells touching the image edges are removed to prevent inaccurate area calculations.
* `BORDER_MARGIN_PX`: The width of the "danger zone" at the edge of the image where cells will be deleted.

## 5. Running the Pipeline

Before running, ensure you have updated the `TARGET_EXP_FOLDER` in `config.py`.

### **Windows**

* **Method:** Double-click `run_pipeline.bat` inside the `Scripts` folder.
* A black command window will open, showing you the progress of the conversion, tracking, and plotting.

### **macOS / Linux**

* **Method:** While you *can* sometimes configure these systems to run scripts on double-click, it is **highly recommended** to run it via the Terminal so you can see the progress and any errors:
1. Open Terminal.
2. Type `cd` followed by a space, then drag your `Scripts` folder into the window and hit Enter.
3. Run the script by typing:
```bash
./run_pipeline.sh
```

## 6. Outputs

Results are saved in `Processed_Data/YYYYMMDD_Timelapse/`:

1. `1_tif_images/`: Raw extracted frames.
2. `2_masks/`: Raw segmentation masks.
3. `3_tracked_masks/`: Masks where cell IDs are consistent across time.
4. `4_results/`: CSV data and expansion plots.
5. `5_tracked_overlays/`: Quality control images with colored overlays.
