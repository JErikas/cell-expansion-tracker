import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import config

def run():

    date_prefix = config.TARGET_EXP_FOLDER[:10].replace("-", "")
    results_dir = Path(config.PROCESSED_DATA_DIR) / f"{date_prefix}_Timelapse" / "3_results"

    avg_csv = results_dir / f"{date_prefix}_Image_Averages.csv"
    cell_csv = results_dir / f"{date_prefix}_Single_Cells_Tracking.csv"

    if not avg_csv.exists() or not cell_csv.exists():
        print("Required CSV files not found.")
        return

    df_avg = pd.read_csv(avg_csv)
    df_cells = pd.read_csv(cell_csv)

    if len(df_avg) == 0 or len(df_cells) == 0:
        print("CSV files empty.")
        return

    df_avg["Voltage"] = pd.to_numeric(df_avg["Voltage"])
    df_cells["Voltage"] = pd.to_numeric(df_cells["Voltage"])

    df_avg = df_avg.sort_values("Voltage")
    df_cells = df_cells.sort_values("Voltage")

    sns.set_style("whitegrid")

    plt.figure(figsize=(12, 7))
    ax = sns.barplot(
        data=df_avg, x="Voltage", y="Percent_Change",
        hue="Media", errorbar="sd", capsize=0.12
    )
    sns.stripplot(
        data=df_avg, x="Voltage", y="Percent_Change",
        hue="Media", dodge=True, alpha=0.7, linewidth=1, legend=False
    )
    plt.axhline(y=0, color='black', linestyle='--', linewidth=1)
    plt.title("Average Cell Area Change After Electroporation", fontsize=16, pad=15)
    plt.xlabel("Voltage (kV/cm)", fontsize=13)
    plt.ylabel("Mean Area Change (%)", fontsize=13)
    plt.tight_layout()

    save_path_1 = results_dir / f"{date_prefix}_Average_Response.png"
    plt.savefig(save_path_1, dpi=300, bbox_inches="tight")
    plt.close()

    plt.figure(figsize=(14, 8))
    sns.violinplot(
        data=df_cells, x="Voltage", y="Percent_Change",
        hue="Media", split=True, inner=None
    )
    sns.stripplot(
        data=df_cells, x="Voltage", y="Percent_Change",
        hue="Media", dodge=True, alpha=0.25, size=2, legend=False
    )
    plt.axhline(y=0, color='black', linestyle='--', linewidth=1)
    plt.title("Single-Cell Area Change Distribution", fontsize=16, pad=15)
    plt.xlabel("Voltage (kV/cm)", fontsize=13)
    plt.ylabel("Cell Area Change (%)", fontsize=13)
    plt.tight_layout()

    save_path_2 = results_dir / f"{date_prefix}_Single_Cell_Distribution.png"
    plt.savefig(save_path_2, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"\nSaved:")
    print(save_path_1)
    print(save_path_2)

if __name__ == "__main__":
    run()