"""CV-only model selection, followed by one held-out evaluation of the winner."""

import hashlib
import json
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
from mlflow.models import infer_signature
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    RocCurveDisplay,
    accuracy_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split

from heart_ml.data import FEATURES, load_data
from heart_ml.model import build_pipeline

SEED = 42


def main():
    out = Path("artifacts")
    out.mkdir(exist_ok=True)
    frame = load_data()
    X, y = frame[FEATURES], frame.target
    train_idx, test_idx = train_test_split(
        np.arange(len(frame)), test_size=0.2, stratify=y, random_state=SEED
    )
    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
    (out / "split.json").write_text(
        json.dumps({"seed": SEED, "train": train_idx.tolist(), "test": test_idx.tolist()}, indent=2)
    )
    mlflow.set_tracking_uri("sqlite:///mlflow.db")
    mlflow.set_experiment("cleveland-heart-classification")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    scoring = {
        "accuracy": "accuracy",
        "precision": "precision",
        "recall": "recall",
        "roc_auc": "roc_auc",
    }
    candidates = {
        "logistic_regression": (
            LogisticRegression(max_iter=2000, random_state=SEED),
            {"classifier__C": [0.1, 1.0, 10.0]},
        ),
        "random_forest": (
            RandomForestClassifier(n_estimators=150, random_state=SEED, n_jobs=1),
            {"classifier__max_depth": [3, None], "classifier__min_samples_leaf": [1, 4]},
        ),
    }
    winners, rows = {}, []
    data_hash = hashlib.sha256(Path("data/processed/heart.csv").read_bytes()).hexdigest()
    for name, (classifier, grid) in candidates.items():
        search = GridSearchCV(
            build_pipeline(classifier),
            grid,
            scoring=scoring,
            refit="roc_auc",
            cv=cv,
            n_jobs=1,
            error_score="raise",
        )
        search.fit(X_train, y_train)
        results = pd.DataFrame(search.cv_results_)
        results.to_csv(out / f"{name}_cv.csv", index=False)
        for i, params in enumerate(search.cv_results_["params"]):
            with mlflow.start_run(run_name=f"{name}-candidate-{i}"):
                mlflow.log_params(
                    {
                        **params,
                        "model": name,
                        "seed": SEED,
                        "cv_folds": 5,
                        "dataset_sha256": data_hash,
                    }
                )
                for metric in scoring:
                    mlflow.log_metric(f"cv_{metric}", results.loc[i, f"mean_test_{metric}"])
                    mlflow.log_metric(f"cv_{metric}_std", results.loc[i, f"std_test_{metric}"])
                mlflow.log_artifact(str(out / f"{name}_cv.csv"))
                mlflow.log_artifacts("artifacts/eda", artifact_path="eda")
        winners[name] = search.best_estimator_
        row = {"model": name, "parameters": search.best_params_}
        for metric in scoring:
            row[f"cv_{metric}"] = float(results.loc[search.best_index_, f"mean_test_{metric}"])
        rows.append(row)
    selected = max(rows, key=lambda row: row["cv_roc_auc"])
    model = winners[selected["model"]]
    pred = model.predict(X_test)
    prob = model.predict_proba(X_test)[:, 1]
    metrics = {
        "accuracy": accuracy_score(y_test, pred),
        "precision": precision_score(y_test, pred, zero_division=0),
        "recall": recall_score(y_test, pred, zero_division=0),
        "roc_auc": roc_auc_score(y_test, prob),
    }
    ConfusionMatrixDisplay.from_predictions(y_test, pred)
    plt.title("Selected model: held-out confusion matrix")
    plt.savefig(out / "confusion_matrix.png", dpi=160, bbox_inches="tight")
    plt.close()
    RocCurveDisplay.from_predictions(y_test, prob)
    plt.title("Selected model: held-out ROC")
    plt.savefig(out / "roc_curve.png", dpi=160, bbox_inches="tight")
    plt.close()
    joblib.dump(model, out / "model.joblib")
    summary = {
        "selected_model": selected["model"],
        "selection_metric": "mean CV ROC-AUC",
        "candidates": rows,
        "test_metrics": metrics,
        "train_rows": len(train_idx),
        "test_rows": len(test_idx),
        "threshold": 0.5,
        "seed": SEED,
        "dataset_sha256": data_hash,
        "features": FEATURES,
    }
    with mlflow.start_run(run_name="selected-model-heldout-evaluation") as run:
        summary["mlflow_run_id"] = run.info.run_id
        mlflow.log_params(
            {
                "model": selected["model"],
                "seed": SEED,
                "dataset_sha256": data_hash,
                **selected["parameters"],
            }
        )
        mlflow.log_metrics({f"test_{k}": v for k, v in metrics.items()})
        mlflow.sklearn.log_model(
            model, name="pipeline", signature=infer_signature(X_train, model.predict(X_train))
        )
        (out / "metrics.json").write_text(json.dumps(summary, indent=2))
        mlflow.log_artifacts(str(out), artifact_path="evaluation")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
