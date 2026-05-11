# Cell Timelapse Analysis Pipeline

Welcome to the Cell Timelapse Analysis Pipeline. This automated tool takes raw microscopy data (CZI format), extracts frames, segments cells using AI (Cellpose), tracks individual cells over time, and generates statistical plots and visual overlays to analyze cell area expansion (e.g., after electroporation).

---

## 📂 1. Project Folder Structure

For the pipeline to work correctly, your project folder must be organized exactly like this:

```text
Your_Project_Folder/
│
├── Models/                # (Optional) Stores any custom Cellpose models if needed later
├── Processed_Data/        # Pipeline outputs will be saved here automatically
├── Raw_Data/              # Place your raw .czi experiment folders here
│   └── 2026-05-09 EP/     # Example Experiment Folder containing .czi files
│
└── Scripts/               # Pipeline scripts and environment files
    ├── config.py
    ├── 0_run_pipeline.py
    ├── 1_convert_czi.py
    ├── 2_segment_cellpose.py
    ├── 3_analyze_tracking.py
    ├── 4_generate_overlays.py
    ├── 5_plot_expansion.py
    ├── environment.yml
    ├── run_pipeline.bat   # Launcher for Windows
    └── run_pipeline.sh    # Launcher for Mac/Linux
```

---

## 🛠️ 2. One-Time Setup & Installation

The pipeline runs on Python and requires specific scientific libraries. To manage these easily without breaking your computer, we use **Miniconda**.

### Step 1: Install Miniconda
1. Go to the [Miniconda Download Page](https://docs.conda.io/en/latest/miniconda.html).
2. Download and install the version for your Operating System (Windows, Mac, or Linux).
3. **Windows Users:** During installation, it is highly recommended to select **"Add Miniconda3 to my PATH environment variable"** (even if it shows in red) OR ensure you always use the "Anaconda Prompt" from your Start menu.

### Step 2: Install the Environment
You only need to do this **once** on your computer.

**For Windows:**
1. Open the **Anaconda Prompt** (or Command Prompt if added to PATH).
2. Navigate to your Scripts folder using the `cd` command. For example:
   ```cmd
   cd C:\Users\Name\Desktop\Anusiya\Scripts
   ```
3. Create the environment:
   ```cmd
   conda env create -f environment.yml
   ```

**For Mac / Linux:**
1. Open the **Terminal**.
2. Navigate to your Scripts folder:
   ```bash
   cd ~/Desktop/Anusiya/Scripts
   ```
3. Create the environment:
   ```bash
   conda env create -f environment.yml
   ```

*(Note: This step may take 5–15 minutes as it downloads heavy AI libraries like PyTorch and Cellpose).*

---

## 🚀 3. Tutorial: Running a New Experiment

Follow these steps every time you have a new batch of data to process.

### Step 1: Add Raw Data
Create a new folder inside `Raw_Data/` and name it appropriately (e.g., `2026-05-09 EP`). Place all your raw `.czi` files inside this new folder. 
*Note: The script attempts to read the date from the first 10 characters of the folder name (e.g., `2026-05-09`).*

### Step 2: Update Configuration
Open `Scripts/config.py` in any text editor (like Notepad, TextEdit, or VS Code). 
Find the `TARGET_EXP_FOLDER` variable and change it to exactly match your new folder's name:

```python
# =======================
# CURRENT EXPERIMENT
# =======================
TARGET_EXP_FOLDER = "2026-05-09 EP" # <--- Change this to your new folder name
```
Save and close `config.py`.

### Step 3: Launch the Pipeline

**If you are on Windows:**
Simply go to the `Scripts/` folder and **double-click** `run_pipeline.bat`. A black terminal window will open, activate the environment, and run the whole process automatically.

**If you are on Mac / Linux:**
1. Open your Terminal.
2. Navigate to the Scripts folder:
   ```bash
   cd path/to/Your_Project_Folder/Scripts
   ```
3. *(First time only)* Make the script executable:
   ```bash
   chmod +x run_pipeline.sh
   ```
4. Run the script:
   ```bash
   ./run_pipeline.sh
   ```

---

## ⚙️ 4. Configuration Guide (`config.py`)

You can tweak how the pipeline behaves by editing the values in `Scripts/config.py`:

| Setting | What it does |
| :--- | :--- |
| `MICRONS_PER_PIXEL` | Converts pixel measurements to real-world micrometers (µm). Update this if you change your microscope's objective/magnification. |
| `NUM_INTERMEDIATE_FRAMES` | How many frames to extract between the first and last frame of the CZI file. If set to `5`, the pipeline extracts 7 frames total (Start + 5 Intermediate + End). |
| `CELLPOSE_DIAMETER` | The expected average size of the cells in pixels. Increasing this helps detect larger cells; decreasing detects smaller ones. |
| `MAX_TRACKING_DISTANCE_PX` | The maximum distance (in pixels) a cell can move between frames and still be considered the same cell. |
| `REMOVE_BORDER_OBJECTS` | Set to `True` to delete cells that touch the edges of the image (prevents analyzing partially cut-off cells). |
| `SAVE_TRACKED_OVERLAYS` | Set to `True` to generate visualization images showing colored masks layered over the raw cells. |

---

## 📊 5. Understanding Your Outputs

Once the terminal says **"PIPELINE COMPLETE!"**, go to the `Processed_Data/` folder. You will find a new folder named after your experiment date (e.g., `20260509_Timelapse`). Inside are five numbered folders:

1. **`1_tif_images/`**: The raw `.czi` files split into individual `.tif` frames.
2. **`2_masks/`**: The raw black-and-white segmentation results from Cellpose.
3. **`3_tracked_masks/`**: The cleaned masks. Here, the pipeline has assigned a unique ID (color value) to each cell. The cell maintains this ID across all frames.
4. **`4_results/`**: The numerical and statistical core of the pipeline:
   * **`..._Image_Averages.csv`**: A spreadsheet summarizing the average area change per image/condition.
   * **`..._Single_Cells_Tracking.csv`**: A detailed spreadsheet showing the Area at T0, Area at Final Time, and Percentage Change for *every single tracked cell*.
   * **`.png` Plots**: Automatically generated Bar charts and Violin plots visualizing your data distribution.
5. **`5_tracked_overlays/`**: Beautiful colored visual overlays. Watch these as an image sequence to visually verify that the AI correctly tracked the cells over time.

---

## ❓ 6. Troubleshooting

* **"Conda is not recognized as an internal or external command" (Windows)** 
  *miniconda wasn't added to your system PATH. Reinstall Miniconda and check the box "Add to PATH", or run the `.bat` file directly from the "Anaconda Prompt" instead of standard CMD.*
* **"Permission Denied" (Mac/Linux)**
  *You need to make the launcher executable. Run `chmod +x run_pipeline.sh` in the terminal.*
* **Cells are being mis-segmented**
  *Open `config.py` and adjust the `CELLPOSE_DIAMETER`. You can also tweak the `CHANNEL_CELL_INDEX` if your CZI channels are ordered differently.*
* **Pipeline crashes at "Tracking"**
  *This usually happens if cells move too fast between frames. Try increasing `MAX_TRACKING_DISTANCE_PX` in `config.py`.*