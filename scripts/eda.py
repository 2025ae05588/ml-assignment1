from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from heart_ml.data import NUMERIC, load_data


def main():
    output = Path("artifacts/eda")
    output.mkdir(parents=True, exist_ok=True)
    frame = load_data()
    sns.set_theme(style="whitegrid")
    frame[NUMERIC].hist(figsize=(12, 8), bins=18, color="#197c91", edgecolor="white")
    plt.suptitle("Cleveland heart disease: numeric feature distributions")
    plt.tight_layout()
    plt.savefig(output / "histograms.png", dpi=160)
    plt.close()
    plt.figure(figsize=(12, 9))
    sns.heatmap(frame.corr(), cmap="vlag", center=0, annot=True, fmt=".2f")
    plt.title("Pearson correlations (categorical codes are descriptive only)")
    plt.tight_layout()
    plt.savefig(output / "correlation.png", dpi=160)
    plt.close()
    plt.figure(figsize=(6, 4))
    sns.countplot(data=frame, x="target", color="#197c91")
    plt.xticks([0, 1], ["Absent", "Present"])
    plt.title("Disease label balance")
    plt.tight_layout()
    plt.savefig(output / "class_balance.png", dpi=160)
    plt.close()
    frame.describe().to_csv(output / "summary.csv")
    frame.isna().sum().to_csv(output / "missing.csv")
    print("EDA artifacts saved to", output)


if __name__ == "__main__":
    main()
