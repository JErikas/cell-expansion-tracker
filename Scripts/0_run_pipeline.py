import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE" 
import subprocess
import sys
import time
from datetime import datetime
import config

def run_pipeline():

    scripts =[
        ("Converting Timelapse CZI", "1_convert_czi.py"),
        ("Segmenting Frames", "2_segment_cellpose.py"),
        ("Tracking Cells + Relabeling Masks", "3_analyze_tracking.py"),
        ("Generating Final Overlays", "4_generate_overlays.py"),
        ("Plotting Expansion Data", "5_plot_expansion.py")
    ]

    overall_start = time.time()

    print("=" * 60)
    print(f"TIMELAPSE PIPELINE STARTED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()

    for step_name, script_name in scripts:

        print(f">>>>> STARTING STEP: {step_name} <<<<<")

        try:
            subprocess.run([sys.executable, script_name], check=True)
            print(f">>>>> FINISHED STEP: {step_name} <<<<<\n")
            
            if script_name == "2_segment_cellpose.py" and getattr(config, 'PAUSE_FOR_MANUAL_CORRECTION', False):
                print("=" * 60)
                print("⏸️  PIPELINE PAUSED FOR MANUAL CORRECTION")
                print("1. Keep this window open.")
                print("2. Go to your Scripts folder and double-click 'launch_gui.bat' (Windows) or run 'launch_gui.sh' (Mac).")
                print("3. In the GUI, open your Processed_Data/.../1_images_and_segmentation/ folder.")
                print("4. Drag and drop the .tif IMAGES directly into the Cellpose window.")
                print("5. Correct the masks (CTRL+Right-Click to delete, Left-Click to trace).")
                print("6. Press CTRL+S to save your edits.")
                print("=" * 60)
                input("Press [ENTER] in this window when you are ready to resume tracking...")
                print("\nResuming pipeline...\n")

        except subprocess.CalledProcessError:
            print(f"\n[FATAL ERROR] {script_name} crashed. Pipeline halted.")
            sys.exit(1)

    total_time = time.strftime("%H:%M:%S", time.gmtime(time.time() - overall_start))

    print("=" * 60)
    print(f"PIPELINE COMPLETE! Total Time: {total_time}")
    print("=" * 60)

if __name__ == "__main__":
    run_pipeline()