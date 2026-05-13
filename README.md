# Cell Expansion Tracker Pipeline

This automated pipeline processes raw CZI microscopy data to extract frames, segment cells using Cellpose, track individual cells across a timelapse, and plot their physical expansion.

## 1. Pipeline Overview: How It Works

This project is broken down into five distinct automated steps. When you run the pipeline, it executes the following scripts in order:

**Step 1: Data Extraction (`1_convert_czi.py`)**
* **What it does:** Reads proprietary Zeiss `.czi` microscopy files. Instead of processing every single frame of a massive timelapse, it extracts a user-defined number of frames (e.g., the very first frame, the last frame, and evenly spaced intermediate frames). 
* **Under the hood:** Uses `aicspylibczi` to read the files. It automatically reads the internal XML metadata to find the exact hardware scaling (µm per pixel) and parses your folder names to log the biological conditions (Voltage and Media). Outputs standard `.tif` images.

**Step 2: AI Cell Segmentation (`2_segment_cellpose.py`)**
* **What it does:** Identifies the exact boundaries of every single cell in every extracted frame.
* **Under the hood:** Uses **Cellpose**, a state-of-the-art deep learning algorithm for cellular image segmentation. It generates black-and-white integer masks where every detected cell is assigned a unique pixel value. It also includes a filtering step (using `scikit-image`) to delete any cells touching the edge of the image, ensuring no partially-cut-off cells ruin the final area statistics.

**Step 3: Tracking & Area Analysis (`3_analyze_tracking.py`)**
* **What it does:** Links the cells across time. It figures out which cell in Frame 1 corresponds to which cell in Frame 2, Frame 3, etc., and calculates how much they expanded or shrank.
* **Under the hood:** Uses `scipy` to calculate the spatial distance between cell centroids across consecutive frames. If a cell remains within a defined physical radius (`MAX_TRACKING_DISTANCE_PX`), it is logged as the same cell. The script then applies the hardware scaling metadata to calculate the exact physical area (in µm²) at the beginning and end of the timelapse, outputting `.csv` spreadsheets.

*Single Cell Tracking*
<center><img src="https://i.imgur.com/6EgLEif.png" width="100%"></center>

*Image Averages*
<center><img src="https://i.imgur.com/0W95d9s.png" width="100%"></center>


**Step 4: Visual Validation (`4_generate_overlays.py`)**
* **What it does:** Creates human-readable images to prove that the AI segmented and tracked the cells correctly. 
* **Under the hood:** Overlays the AI-generated masks onto the original microscope images. It uses a mathematical color generator to assign high-contrast colors to specific cell IDs. Because of the tracking in Step 3, a cell will maintain the exact same color across the entire timelapse, allowing you to easily spot-check the accuracy.

<center><img src="https://i.imgur.com/zh1naCW.png" width="100%"></center>

**Step 5: Statistical Plotting (`5_plot_expansion.py`)**
* **What it does:** Automatically graphs the results from the `.csv` files.
* **Under the hood:** Uses `pandas`, `matplotlib`, and `seaborn` to generate grouped statistical plots. It creates both image-level average bar charts (showing standard deviation) and single-cell violin plots to show the full distribution of expansion behaviors grouped by Voltage and Media.

<p float="left">
  <img align="middle" src="https://i.imgur.com/aK7N3Ks.png" width="49%" />
  <img align="middle" src="https://i.imgur.com/VDGIvzJ.png" width="50%" /> 
  <p align="middle">
</p>

---

## 2. Project Folder Structure

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

## 3. One-Time Setup and Installation

This pipeline requires **Miniconda** (a lightweight version of Python and the Conda package manager) to manage the necessary biological imaging libraries safely.

### Step 1: Install Miniconda

#### **For Windows:**

1. Download the latest **Miniconda Windows 64-bit installer** (`Miniconda3-latest-Windows-x86_64.exe`) from the [Official Download Page](https://repo.anaconda.com/miniconda/).
2. Run the `.exe` installer.
3. **Important:** During installation, it is highly recommended to check the box **"Add Miniconda3 to my PATH environment variable"**. This allows the `.bat` launcher to find Python automatically.
4. If you did NOT add it to PATH, you must run all commands via the **"Anaconda Prompt"** found in your Start Menu.

#### **For macOS / Linux:**

1. Download the **Miniconda installer script** (`.sh` file) from the [Official Download Page](https://repo.anaconda.com/miniconda/) for your architecture (Intel (`Miniconda3-latest-MacOSX-x86_64.sh`) or Apple M-series (`Miniconda3-latest-MacOSX-arm64.sh`)). You can confirm which architecture your Mac uses by navigating to the **Apple Menu > About This Mac**. If it lists *Apple M1 / M2 /M3*, you are using **ARM64**, if it lists *Intel*, you are using **x86_64** architecture.
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

## 4. Data Formatting Requirements

The pipeline automatically reads experimental conditions from your folder names.

### Metadata Extraction Rules

* **Experiment Date**: The main experiment folder must begin with a 10-character date (`YYYY-MM-DD`).
* **Voltage**: The folder name must contain a number followed by **kV** (case-insensitive). Decimals (`.`) or commas (`,`) are both accepted.
* **Media Type**: The script searches for keywords defined in your `config.py` (e.g., `sn` or `std`).

### Examples of Perfectly Formatted Directories:

1. Raw_Data/**2026-05-09**/**STD** **1.5kV**/202609210844-01.czi
2. Raw_Data/**2026-05-09** EP/STD **SN** EP/**4,2 KV**-CM-8HV/2026-05-09/202609210552-01.czi

*Note: The **bolded features are necessary** for the script to correctly extract the experiment date, media type, and voltage.*

## 5. Configuration Variables Guide (`config.py`)

All settings are managed in `Scripts/config.py`. Below is an explanation of every parameter.

### Paths & Experiment

* `TARGET_EXP_FOLDER`: The exact name of your main experiment folder in `Raw_Data/`.
* `RAW_DATA_DIR` / `PROCESSED_DATA_DIR`: Automatically calculated paths for input and output.

### Media Conditions

* `MEDIA_CONDITIONS`: A dictionary mapping folder keywords to readable labels.
* *Example*: `"sn": "Supplemented_Media"` means any folder containing "sn" will be labeled "Supplemented Media" in results.
* `DEFAULT_MEDIA_NAME`: The label used if no keywords from `MEDIA_CONDITIONS` are found in the folder path.

### Microscopy Settings

* `FALLBACK_MICRONS_PER_PIXEL`: Used if the `.czi` file metadata is missing or corrupted.
> **How to check:** In ImageJ/Fiji, open an image and go to **Image > Properties > Pixel width**.
* `CHANNEL_CELL_INDEX`: The channel index (starting from 0) containing the cell signal.
* `NUM_INTERMEDIATE_FRAMES`: Number of frames to extract *between* the first and last image. (e.g., 5 frames results in 7 total images per timelapse).

### Cellpose Model Settings

* `USE_CUSTOM_CELLPOSE_MODEL`: Set to `True` to use a self-trained model.
* `CUSTOM_MODEL_FILENAME`: The filename of your model (placed in the `Models/` folder).
* `BUILTIN_MODEL_NAME`: The Cellpose model to use (default is `cyto3`).
* `CELLPOSE_DIAMETER`: Expected average cell diameter in pixels.

### Manual Correction & Tracking Settings
* `PAUSE_FOR_MANUAL_CORRECTION`: Set to `True` to pause the pipeline after segmentation so you can fix masks by hand in the Cellpose GUI before tracking starts.
* `MAX_TRACKING_DISTANCE_PX`: The maximum distance (in pixels) a cell can move between sampled frames to be considered the same cell.

### Overlay Settings

* `SAVE_TRACKED_OVERLAYS`: Enables/disables the generation of visual validation images.
* `OVERLAY_OPACITY`: Transparency of the mask colors (0.0 to 1.0). High-contrast HSV colors are used to ensure cell IDs are visually distinct.

### Border Filtering Settings

* `REMOVE_BORDER_OBJECTS`: If `True`, cells touching the image edges are removed to prevent inaccurate area calculations.
* `BORDER_MARGIN_PX`: The width of the "danger zone" at the edge of the image where cells will be deleted.

## 6. Running the Pipeline

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

## 7. Manual Mask Correction Workflow

If you notice Cellpose is occasionally making mistakes (e.g., merging two cells together, or missing a cell), you can correct the masks by hand before the pipeline calculates the cell tracking data.

1. Open `config.py` and set `PAUSE_FOR_MANUAL_CORRECTION = True`.
2. Run `run_pipeline`. After segmentation finishes, the terminal will pause.
3. Leave the pipeline terminal open. Go to your `Scripts` folder and **double-click `launch_gui.bat`** (Windows) or run **`launch_gui.sh`** (Mac/Linux). This will open the Cellpose interface automatically.
4. In the Cellpose Window:
   * Navigate to `Processed_Data/.../1_images_and_segmentation/`.
   * **Drag and drop the `.tif` IMAGE or `.npy` SEGMENTATION files** directly into the Cellpose window. 
   * *Note: You need to drag only one of them. Because when both files are in the same folder, Cellpose will automatically load the image from the `.tif` and overlay the editable masks from the `.npy` file.*
5. Use your mouse to correct the cells:
   * **To DELETE an incorrect mask:** Hold **CTRL (or COMMAND on Mac) + Left-Click** on it.
   * **To TRACE a missing cell:** **Right-Click** and draw the outline, joining the trace at the start point to finish it.
   * **CTRL + S** (or CMD + S) to save your changes. This updates the `.npy` file in the folder.
6. **Pro Tip for Speed:** You do not need to drag and drop every file! Once the first image is open, **Left-Click** anywhere on the image to focus the window, then use the **Left and Right Arrow Keys** on your keyboard to instantly scroll through all the images in the folder. 
7. Close the GUI, return to the original paused pipeline terminal window and **press ENTER**. The pipeline will immediately resume and accurately track your hand-corrected masks

## 8. Outputs

Results are saved in `Processed_Data/YYYYMMDD_Timelapse/`. To keep data organized, the pipeline condenses everything into 4 clean folders:

1. `1_images_and_segmentation/`: Contains your raw extracted `.tif` frames alongside the editable `_seg.npy` Cellpose files.
2. `2_tracked_masks/`: Clean 16-bit `.tif` masks where cell IDs are mathematically linked across time. 
3. `3_results/`: CSV data spreadsheets and automatically generated expansion plots.
4. `4_tracked_overlays/`: High-contrast quality control images with colored masks overlaid on the cells.
