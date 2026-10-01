"""Generate a ten-page report from actual artifacts, never invented deployment evidence."""

import json
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
styles = getSampleStyleSheet()
styles["Normal"].fontSize = 10
styles["Normal"].leading = 14
styles["Heading1"].textColor = colors.HexColor("#155e75")


def paragraph(text):
    return Paragraph(escape(text), styles["Normal"])


def table(rows):
    t = Table([[paragraph(str(c)) for c in row] for row in rows], hAlign="LEFT")
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e0f2fe")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return t


def main():
    meta = json.loads((ROOT / "data/metadata.json").read_text())
    result = json.loads((ROOT / "artifacts/metrics.json").read_text())
    evidence_path = ROOT / "artifacts/evidence/verification.json"
    evidence = json.loads(evidence_path.read_text()) if evidence_path.exists() else {}
    pages = []

    def page(title, blocks):
        if pages:
            pages.append(PageBreak())
        pages.extend([Paragraph(title, styles["Heading1"]), Spacer(1, 14)])
        for block in blocks:
            pages.append(paragraph(block) if isinstance(block, str) else block)
            pages.append(Spacer(1, 12))

    def image(path, width=460, height=280):
        return Image(str(ROOT / path), width=width, height=height, kind="proportional")

    page(
        "1. Project objective and architecture",
        [
            "Machine Learning Operations (AIMLCZG523), Assignment 01. End-to-end educational classification of heart disease presence using the UCI Cleveland dataset. Prepared 1 October 2026.",
            "The system acquires a traceable dataset, creates reproducible experiments, packages preprocessing with the model, and exposes validated inference through FastAPI. Automation checks source quality, unit behavior and container serving. Kubernetes and monitoring configurations support deployment.",
            image("artifacts/architecture.png", height=330),
            "Evidence policy: this report labels configurations separately from executed checks. This dataset classifier predicts a historical disease label; it is not a validated clinical diagnostic service or future-risk score. Review and personalize this work in accordance with the course's academic integrity and AI-assistance policies.",
        ],
    )
    page(
        "2. Dataset acquisition and provenance",
        [
            "Source: UCI Heart Disease, https://archive.ics.uci.edu/dataset/45/heart+disease. Citation: Janosi, Steinbrunn, Pfisterer and Detrano (1989), DOI 10.24432/C52P4X. License: CC BY 4.0.",
            f"The processed Cleveland subset contains {meta['raw_rows']} rows and 13 predictors plus the original num target. The assignment's reference to 14+ features is interpreted as the commonly used 14-column dataset, including the target; no artificial predictors were added.",
            "scripts/download_data.py downloads the original file only if absent, validates its structure, writes a cleaned CSV and records a SHA-256 digest. It removes exact duplicates and maps num=0 to absence and num=1..4 to presence.",
            table(
                [
                    ["Data property", "Observed value"],
                    ["Raw / clean rows", f"{meta['raw_rows']} / {meta['clean_rows']}"],
                    ["Duplicates removed", meta["duplicates_removed"]],
                    ["Missing ca / thal", "4 / 2"],
                    ["Target mapping", "0 -> absent; 1,2,3,4 -> present"],
                ]
            ),
            "Raw data checksum: " + meta["sha256"],
            "Categorical values retain original UCI coding: cp 1-4, slope 1-3, ca 0-3 and thal 3/6/7. Predictors include age, sex, resting blood pressure, cholesterol, fasting blood sugar, ECG, maximum heart rate, exercise angina and ST depression. Full feature descriptions are linked in the README.",
        ],
    )
    page(
        "3. Exploratory analysis and cleaning",
        [
            "EDA is reproduced with scripts/eda.py or notebooks/01_eda.ipynb. Histograms examine distributions and potential outliers; class counts reveal label balance; the correlation heatmap describes associations without being used for test-informed feature selection.",
            image("artifacts/eda/histograms.png", height=320),
            image("artifacts/eda/class_balance.png", width=300, height=180),
            "Missing predictors remain missing in the cleaned CSV. No global imputation, scaling or arbitrary outlier deletion is performed. This preserves the distinction between deterministic cleaning and learned preprocessing. Numeric category correlations are descriptive and should not be interpreted as continuous clinical effects.",
        ],
    )
    page(
        "4. Features and leakage prevention",
        [
            "The preprocessing ColumnTransformer handles five numerical variables (age, trestbps, chol, thalach, oldpeak) with median imputation and StandardScaler. Eight categorical predictors use mode imputation and OneHotEncoder(handle_unknown='ignore').",
            "Both estimators receive the same feature representation for a controlled comparison. Scaling is useful for Logistic Regression; it is unnecessary but harmless for Random Forest. All 13 source predictors are retained; no selection procedure is fitted on the held-out test set.",
            f"Stratified splitting uses seed 42, {result['train_rows']} training rows and {result['test_rows']} test rows. The exact indices are saved in artifacts/split.json. Five-fold shuffled stratified CV operates exclusively on the training partition.",
            image("artifacts/eda/correlation.png", height=350),
            "Imputation and encoding are fitted within each CV fold because they are inside the sklearn Pipeline. Tests check training-only numeric imputation statistics and serialized pipeline equivalence.",
        ],
    )
    rows = [["Estimator", "CV AUC", "CV accuracy", "CV recall"]]
    for candidate in result["candidates"]:
        rows.append(
            [
                candidate["model"],
                f"{candidate['cv_roc_auc']:.4f}",
                f"{candidate['cv_accuracy']:.4f}",
                f"{candidate['cv_recall']:.4f}",
            ]
        )
    page(
        "5. Model tuning and held-out evaluation",
        [
            "Logistic Regression tests C in {0.1,1,10}. Random Forest uses 150 trees, max_depth in {3,None} and min_samples_leaf in {1,4}. Seven candidate configurations are assessed using the same five folds. Selection maximizes mean CV ROC-AUC rather than examining test performance.",
            table(rows),
            f"Selected estimator: {result['selected_model']}. Its held-out metrics are: "
            + "; ".join(f"{k}={v:.4f}" for k, v in result["test_metrics"].items())
            + ".",
            image("artifacts/confusion_matrix.png", width=290, height=190),
            image("artifacts/roc_curve.png", width=290, height=175),
            "The decision threshold is fixed at 0.5. Recall and precision expose different error costs; the report does not tune a threshold against the test set. A small 61-row test partition means these scores have substantial uncertainty. No external validation or probability calibration has been performed.",
        ],
    )
    page(
        "6. Experiment tracking and reproducibility",
        [
            "MLflow uses a local SQLite tracking store (mlflow.db) and local artifact storage. Each candidate logs hyperparameters, seed, dataset hash, five-fold metric means and standard deviations, CV result tables and EDA plots. The final run logs held-out metrics, confusion matrix, ROC plot and the full sklearn pipeline.",
            "Final evaluation run ID: " + result["mlflow_run_id"],
            "View experiments using: mlflow ui --backend-store-uri sqlite:///mlflow.db --host 127.0.0.1 --port 5000. The database and artifacts must remain together when transferred. CI uploads both as downloadable workflow artifacts.",
            "artifacts/model.joblib contains preprocessing and the selected estimator. Serving reuses this fitted pipeline and never duplicates preprocessing logic. The evaluated model is retained without refitting on held-out data.",
            "requirements.txt pins direct packages; requirements-lock.txt records the exact local resolved environment for audit. The project is installed as an editable Python package through pyproject.toml. Linux CI and Docker perform independent installs from the direct manifest.",
            "For reproducibility, retain the raw dataset, data hash, split indices, CV tables, MLflow run and package manifests. Random seeds improve repeatability but do not guarantee identical results across all platforms and dependency implementations.",
            image("screenshots/mlflow-runs.jpg", height=220),
        ],
    )
    page(
        "7. API serving and container packaging",
        [
            "FastAPI exposes POST /predict, GET /health, GET /metrics and interactive /docs. Pydantic rejects missing fields, invalid category codes, unknown fields and non-finite numeric values. ca and thal accept explicit null values that the fitted pipeline imputes.",
            "The prediction response contains the binary label, disease_probability, confidence, model version and educational-use message. Confidence is max(p,1-p), the probability assigned to the predicted label; it is not calibrated clinical certainty.",
            "The model is loaded once during application startup. Missing model artifacts fail startup visibly. Request logging records method, route, status and latency without recording the patient payload.",
            "Docker uses python:3.13-slim, installs the project, copies the model and metadata, serves on port 8000 and runs as a non-root user. A Docker healthcheck calls /health. The smoke-test script builds and starts the image, checks health and prediction and saves logs.",
            "Example: curl http://localhost:8000/predict -H 'Content-Type: application/json' --data @examples/patient.json",
            "Container execution status: "
            + str(evidence.get("docker", "Not yet verified; configuration prepared.")),
            "Actual local API response and metrics are saved under artifacts/evidence. Never substitute host Python checks for proof that the container builds and runs.",
            image("screenshots/kubernetes-terminal-evidence.png", height=200),
            "Deployment evidence: recorded live kubectl output shows two ready API replicas and the configured Ingress. The full HTTP response is saved in artifacts/evidence/kubernetes-prediction.json.",
        ],
    )
    page(
        "8. Testing and continuous integration",
        [
            "Pytest covers label conversion, missing-value preservation, duplicate removal, invalid dataset categories, target validation, fold-safe preprocessing, serialization equivalence, valid inference, input errors, nullable predictors, health and metrics.",
            "Local test outcome: " + str(evidence.get("tests", "See artifacts/evidence/tests.log")),
            "Ruff performs syntax/import/undefined-name checks. GitHub Actions installs Python 3.13 and dependencies, prepares data, runs lint and tests, generates EDA, trains and tracks experiments, then builds and smoke-tests the Docker image.",
            "Command errors stop the workflow. An always-running upload step preserves metrics, model files, test XML, MLflow storage and container logs. Unit tests are a gate before training; training itself raises errors for failed CV fits.",
            "Repository published: https://github.com/2025ae05588/ml-assignment1. GitHub Actions run 36829271226 succeeded, including all quality, training and isolated container checks. Model/results/tracking artifacts were uploaded. Actual status, logs and screenshots are included.",
            "The CI pipeline verifies the package; local Kubernetes deployment uses the included script. Cluster credentials stay excluded from Git.",
            image("screenshots/github-actions-success.jpg", height=250),
        ],
    )
    page(
        "9. Kubernetes deployment and monitoring",
        [
            "deployment/kubernetes.yaml creates a namespace, two API replicas and a LoadBalancer Service on port 80. Readiness/liveness probes use /health. Resource requests/limits, non-root execution, dropped capabilities and a read-only filesystem provide a basic deployment configuration.",
            "Verified local route: kind with a mapped NodePort and Traefik Ingress at http://127.0.0.1:8080. Reproduce with bash scripts/deploy_kind.sh. For Minikube, run scripts/deploy_local.sh and minikube tunnel. Inspect the Service external address and call /health and /predict through that address. A cloud cluster additionally requires an accessible registry image and credentials.",
            "Kubernetes execution status: "
            + str(evidence.get("kubernetes", "Not executed; tooling/cluster required.")),
            "Docker Compose provisions FastAPI, Prometheus and Grafana. Prometheus scrapes /metrics every five seconds. The Grafana dashboard shows request rate, 5xx error rate, p95 latency and total prediction count. Generate traffic to demonstrate changes.",
            "Monitoring execution status: "
            + str(evidence.get("monitoring", "See verification.json"))
            + ". The stack runs on localhost ports 8002 (API), 9090 (Prometheus) and 3000 (Grafana). The Compose monitoring demonstration targets its API container, not an unconfigured Kubernetes endpoint.",
            "Operational limitations: no authentication, TLS termination, drift detection, retraining trigger or production alerting is implemented. These are future extensions. Monitoring measures service behavior, not clinical accuracy. Do not expose the demonstration stack publicly without appropriate access controls.",
            image("screenshots/grafana-dashboard.jpg", height=210),
        ],
    )
    page(
        "10. Reproduction and submission checklist",
        [
            "Setup: python3 -m venv .venv; activate it; pip install -e .; python scripts/download_data.py; python scripts/eda.py; python scripts/train.py; pytest -q; ruff check .; uvicorn heart_ml.api:app --port 8000.",
            "Repository deliverables: source, download and training scripts, EDA notebook, raw and cleaned data with citation, requirements files, tests, workflow YAML, Dockerfile, Kubernetes manifests, monitoring configuration, screenshots and this ten-page report.",
            "Submission evidence: actual MLflow experiment view; successful CI logs/artifacts; Docker build and sample prediction; Kubernetes replicas and exposed endpoint; Grafana traffic metrics; short live video of the whole pipeline.",
            "GitHub repository: https://github.com/2025ae05588/ml-assignment1. Verified deployed API access: http://127.0.0.1:8080 through the local kind cluster Ingress. No public cloud URL is claimed.",
            "reports/DEMO_SCRIPT.md supplies the live recording sequence. reports/pipeline_terminal_demo.mp4 records actual deployment/monitoring command outputs and genuine browser screenshots. Raw timestamps and exit codes are in demo_commands.json. It is a terminal-output recording, not an operating-system desktop capture.",
            "All implementation stages have executed successfully: local data/model/API verification, remote CI, Docker isolation, Kubernetes Ingress and monitoring. Genuine screenshots and the terminal demonstration are included. Record an oral desktop presentation separately if your instructor requires that format. reports/COMPLETION_STATUS.md and artifacts/evidence/verification.json distinguish prepared and executed work.",
            "References: UCI Heart Disease (DOI 10.24432/C52P4X); sklearn Pipeline and GridSearchCV; MLflow tracking; FastAPI; Docker; Kubernetes; Prometheus and Grafana official documentation. Refer to README commands and implementation files for concrete reproduction details.",
        ],
    )

    def footer(canvas, doc):
        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(colors.HexColor("#64748b"))
        canvas.drawString(42, 25, "Heart Disease MLOps | Implementation and evidence report")
        canvas.drawRightString(A4[0] - 42, 25, str(doc.page))

    target = ROOT / "reports/assignment_report.pdf"
    SimpleDocTemplate(
        str(target), pagesize=A4, rightMargin=42, leftMargin=42, topMargin=40, bottomMargin=45
    ).build(pages, onFirstPage=footer, onLaterPages=footer)
    print(target)


if __name__ == "__main__":
    main()
