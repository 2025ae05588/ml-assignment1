#!/usr/bin/env bash
set -euo pipefail
# Install kind and Docker first; see README. Kubeconfig stays inside this project.
KIND_BIN="${KIND_BIN:-kind}"
if ! "$KIND_BIN" get clusters | grep -qx heart-assignment; then
  "$KIND_BIN" create cluster --name heart-assignment --config deployment/kind.yaml --kubeconfig deployment/kubeconfig --wait 180s
fi
docker build -t heart-api:1.0.0 .
"$KIND_BIN" load docker-image heart-api:1.0.0 --name heart-assignment
kubectl --kubeconfig deployment/kubeconfig apply -f deployment/kubernetes.yaml
kubectl --kubeconfig deployment/kubeconfig apply -f deployment/ingress.yaml
kubectl --kubeconfig deployment/kubeconfig -n heart-mlops rollout status deployment/heart-api --timeout=180s
kubectl --kubeconfig deployment/kubeconfig -n heart-mlops rollout status deployment/traefik --timeout=180s
curl -fsS http://127.0.0.1:8080/health
curl -fsS http://127.0.0.1:8080/predict -H 'Content-Type: application/json' --data @examples/patient.json
