# Execution screenshots

The VM PNG captures show the Prayogshala execution on 19 October 2026. The GitHub Actions image is a direct browser capture of the remote CI job. The selected MLflow run and API response use model version `cab705edb7524048a8ad5b31be8316c4`, matching `artifacts/metrics.json`.

| File | Evidence |
|---|---|
| tests-vm.png | Passing lint and 11 unit tests |
| training-vm.png | Training and held-out metrics |
| mlflow-runs.png | Experiment candidate runs |
| mlflow-selected-run-vm.png | Selected model, parameters and test metrics |
| docker-build-vm.png | Docker image build |
| docker-containers-vm.png | Model images and Minikube host container |
| kubernetes-resources-vm.png | Ready deployments, pods, Services and Ingress |
| minikube-dashboard-vm.png | Kubernetes Dashboard workloads |
| api-docs.png | FastAPI endpoint schema |
| api-prediction-request-vm.png | Interactive prediction request |
| api-prediction-vm.png | HTTP 200 prediction, confidence and model version |
| kubernetes-health-vm.png | Ingress health and model version |
| prometheus-targets-vm.png | Healthy Prometheus target |
| grafana-dashboard.png | Request rate, errors, latency and prediction counts |
| github-actions-success.png | Successful GitHub Actions job and completed verification steps |

`github-actions-success.png` captures successful [workflow run 39255010564](https://github.com/2025ae05588/ml-assignment1/actions/runs/39255010564/job/118067978997), for commit `3042161`. It shows lint, data preparation, unit tests, EDA/training, Docker smoke tests and artifact upload completing successfully. GitHub CI and VM training are separate executions; the VM model run ID above refers to the submitted model.

EDA and evaluation charts are generated files under `artifacts/`, rather than manual screenshots.
