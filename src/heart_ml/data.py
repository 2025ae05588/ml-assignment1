"""Deterministic cleaning; learned imputation belongs inside the model pipeline."""

from pathlib import Path

import pandas as pd

FEATURES = [
    "age",
    "sex",
    "cp",
    "trestbps",
    "chol",
    "fbs",
    "restecg",
    "thalach",
    "exang",
    "oldpeak",
    "slope",
    "ca",
    "thal",
]
NUMERIC = ["age", "trestbps", "chol", "thalach", "oldpeak"]
CATEGORICAL = [f for f in FEATURES if f not in NUMERIC]
CODES = {
    "sex": [0, 1],
    "cp": [1, 2, 3, 4],
    "fbs": [0, 1],
    "restecg": [0, 1, 2],
    "exang": [0, 1],
    "slope": [1, 2, 3],
    "ca": [0, 1, 2, 3],
    "thal": [3, 6, 7],
}


def clean_data(raw: pd.DataFrame) -> pd.DataFrame:
    frame = raw.copy()
    if set(frame.columns) != set(FEATURES + ["num"]):
        raise ValueError("Expected Cleveland's 13 predictors and num target")
    frame = frame.replace("?", float("nan"))
    for col in frame:
        frame[col] = pd.to_numeric(frame[col], errors="raise")
    if frame["num"].isna().any() or not frame["num"].isin(range(5)).all():
        raise ValueError("Target must be an integer from 0 through 4")
    for col, codes in CODES.items():
        if not frame[col].dropna().isin(codes).all():
            raise ValueError(f"Invalid category in {col}")
    frame = frame.drop_duplicates().reset_index(drop=True)
    frame["target"] = (frame.pop("num") > 0).astype(int)
    return frame[FEATURES + ["target"]]


def load_data(path: str | Path = "data/processed/heart.csv") -> pd.DataFrame:
    return pd.read_csv(path)
