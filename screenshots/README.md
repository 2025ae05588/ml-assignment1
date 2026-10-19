# Execution screenshots

The PNG captures show the Prayogshala VM execution on 19 October 2026. The selected MLflow run and API response use model version `cab705edb7524048a8ad5b31be8316c4`, matching `artifacts/metrics.json`.

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

`github-actions-success.jpg` is an earlier CI capture, retained as historical evidence. A new capture for the latest upload has not been supplied. The latest uploaded VM artifact commit passed [GitHub Actions](https://github.com/2025ae05588/ml-assignment1/actions/runs/39253566974).

EDA and evaluation charts are generated files under `artifacts/`, rather than manual screenshots.
