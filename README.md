# Heart Disease MLOps Assignment

Educational end-to-end classification of UCI Cleveland heart disease labels. The 13 predictors plus target comprise 14 columns. This is not a clinically validated diagnosis or calibrated future-risk model.

## Clean setup (Python 3.13)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python scripts/download_data.py
python scripts/eda.py
python scripts/train.py
ruff check .
pytest -q
uvicorn heart_ml.api:app --host 0.0.0.0 --port 8000
```

In another terminal:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/predict -H 'Content-Type: application/json' --data @examples/patient.json
curl http://localhost:8000/metrics
```

Open http://localhost:8000/docs for the validated schema. `ca` and `thal` accept null; other fields are required. Confidence is the probability assigned to the predicted class, not a guarantee of correctness. Model artifacts use joblib; load only trusted artifacts.

## Experiment tracking

```bash
mlflow ui --backend-store-uri sqlite:///mlflow.db --host 127.0.0.1 --port 5000
```

Open http://localhost:5000. Seven tuning configurations are tracked, then the CV-selected model is evaluated once on the untouched 20% test split. EDA, CV tables, parameters, dataset hash, metrics and the full pipeline are logged. `artifacts/split.json` records exact row partitions. Training retains the evaluated training-only model rather than silently refitting on test data.

## Container verification

Install Docker Desktop and start its engine. Then:

```bash
bash scripts/docker_verify.sh
```

This builds the image, starts it on port 8001, waits for health, checks prediction and saves real evidence under `artifacts/evidence/`. GitHub Actions also executes this check on Ubuntu.

## Local Kubernetes deployment

Install Docker, kubectl and Minikube:

```bash
bash scripts/deploy_local.sh
minikube tunnel
```

Keep the tunnel running. In another terminal:

```bash
kubectl -n heart-mlops get service heart-api
curl http://SERVICE_EXTERNAL_IP/health
curl http://SERVICE_EXTERNAL_IP/predict -H 'Content-Type: application/json' --data @examples/patient.json
```

Replace SERVICE_EXTERNAL_IP with the actual service address. For Docker Desktop Kubernetes, build the image locally and apply `deployment/kubernetes.yaml` directly. Capture the rollout, service address, and prediction as deployment screenshots. Public cloud use requires pushing the image to your own registry and updating its manifest image reference.

## Monitoring

```bash
docker compose -f deployment/compose.yaml up --build -d
```

Monitoring API: http://localhost:8002; Prometheus: http://localhost:9090; Grafana: http://localhost:3000. Provisioning loads the Heart API dashboard automatically. Default Grafana admin credentials are for local demonstration only; change before public exposure. The monitoring API uses port 8002 to avoid conflicting with the standalone API. Request logs contain method, bounded route name, status and duration, without patient payloads. Metrics provide request rate, 5xx errors and latency; no data-drift or clinical-performance monitoring is claimed.

## CI/CD

The workflow lints, tests, trains, logs experiments, builds Docker and smoke-tests the API. Failed commands stop the job. Artifacts are uploaded even on failure. Deployment is a documented local Kubernetes step; CI does not have credentials to deploy to a cluster automatically.

Repository: https://github.com/2025ae05588/ml-assignment1. GitHub Actions executes when the project is pushed. The local kind cluster and Compose stack are independently verified; their evidence is in artifacts/evidence/.

## Data and reproducibility

Source: https://archive.ics.uci.edu/dataset/45/heart+disease
Citation: Janosi, Steinbrunn, Pfisterer & Detrano (1989), Heart Disease, UCI Machine Learning Repository, DOI 10.24432/C52P4X, CC BY 4.0.
Original categories are retained: cp=1..4, slope=1..3, thal=3/6/7, ca=0..3. `?` is missing. Target num=0 is absence; 1..4 is presence. Cleaning removes exact duplicates, validates categories and preserves missing predictors for fold-local imputation. Numerical columns are median-imputed and standardized; categorical columns are mode-imputed and one-hot encoded. Random seed is 42. Model selection uses five-fold mean ROC-AUC, with accuracy, precision and recall also logged.

The small historical sample has limited representativeness. Test metrics have substantial sampling uncertainty, and probabilities have not been calibrated. Read and understand every component, personalize the experimental choices, and follow your course's AI-assistance policy before submission.

## Deliverables and evidence

- `src/`, `scripts/`, `tests/`: processing, models, serving, verification.
- `data/`: original source, cleaned CSV and provenance.
- `artifacts/`: plots, model, CV tables, split and metrics.
- `.github/workflows/ci.yml`: executable CI and container validation.
- `deployment/`: Kubernetes and monitoring configuration.
- `reports/`: ten-page report, status checklist, demo script and generated walkthrough.
- `screenshots/`: locally observed API/training evidence; capture actual remote CI and Kubernetes screens after running them.

All stages are verified: remote CI run 36829271226 succeeded, Docker serving passed, kind Ingress serves the API, and Prometheus/Grafana is running. The terminal-output demo and genuine browser screenshots are included. If the instructor requires an oral desktop recording, use reports/DEMO_SCRIPT.md; the included MP4 is explicitly a command-output recording.

## Verified kind deployment (current environment)

Docker Desktop is installed at `/Applications/Docker.app`. If its tools are outside your PATH:

```bash
export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"
KIND_BIN=scripts/kind bash scripts/deploy_kind.sh
```

Install kind from https://kind.sigs.k8s.io/docs/user/quick-start/ on a fresh computer; the downloaded local executable is excluded from Git. The kind configuration maps its Ingress to http://127.0.0.1:8080. This route is verified with two ready API replicas. The LoadBalancer Service has no external IP on kind; Traefik Ingress provides the working access path. To inspect:

```bash
kubectl --kubeconfig deployment/kubeconfig -n heart-mlops get deployments,pods,services,ingress
curl http://127.0.0.1:8080/health
curl http://127.0.0.1:8080/predict -H 'Content-Type: application/json' --data @examples/patient.json
python scripts/verify_services.py
```

The kubeconfig is excluded from Git because it contains cluster credentials. To stop the demo services when finished: `docker compose -f deployment/compose.yaml down`. Delete the demo cluster with `kind delete cluster --name heart-assignment` only when you no longer need it.
