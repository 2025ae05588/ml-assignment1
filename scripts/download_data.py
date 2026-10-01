"""Acquire and hash the UCI processed Cleveland file; never replace it silently."""

import hashlib
import json
from pathlib import Path
from urllib.request import urlopen

import pandas as pd

from heart_ml.data import FEATURES, clean_data

URL = "https://archive.ics.uci.edu/ml/machine-learning-databases/heart-disease/processed.cleveland.data"


def main():
    raw_path = Path("data/raw/processed.cleveland.data")
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    if not raw_path.exists():
        with urlopen(URL, timeout=60) as response:
            raw_path.write_bytes(response.read())
    raw = pd.read_csv(raw_path, names=FEATURES + ["num"], na_values="?")
    clean = clean_data(raw)
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    clean.to_csv("data/processed/heart.csv", index=False)
    metadata = {
        "source": URL,
        "doi": "10.24432/C52P4X",
        "license": "CC BY 4.0",
        "sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
        "raw_rows": len(raw),
        "clean_rows": len(clean),
        "duplicates_removed": len(raw) - len(clean),
        "missing": clean.isna().sum().to_dict(),
        "target_mapping": "num == 0 -> 0; num in {1,2,3,4} -> 1",
    }
    Path("data/metadata.json").write_text(json.dumps(metadata, indent=2))
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
