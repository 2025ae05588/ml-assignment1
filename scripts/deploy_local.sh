#!/usr/bin/env bash
# Noninteractive Minikube deployment for the assignment.
set -euo pipefail
cd "$(dirname "$0")/.."
profile="${MINIKUBE_PROFILE:-heart-prayogshala}"
export KUBECONFIG="$PWD/deployment/kubeconfig"
docker build -t heart-api:1.0.0 .
minikube -p "$profile" start --driver=docker --cpus=2 --memory=3072 --kubernetes-version=v1.32.2
minikube -p "$profile" image load heart-api:1.0.0
# Use the cluster-matched kubectl and an explicit context for every operation.
kube() { minikube -p "$profile" kubectl -- --context "$profile" "$@"; }
kube apply -f deployment/kubernetes.yaml
minikube -p "$profile" addons enable ingress
kube apply -f deployment/minikube/ingress.yaml
kube apply -f deployment/minikube/monitoring.json
kube -n heart-mlops rollout restart deployment/heart-api
for deployment in heart-api prometheus grafana; do
  kube -n heart-mlops rollout status "deployment/$deployment" --timeout=360s
done
kube -n ingress-nginx rollout status deployment/ingress-nginx-controller --timeout=360s
kube -n heart-mlops get deployments,pods,services,ingress -o wide
cat <<'HELP'
Deployment ready. In separate VM terminals run these and keep them open:
minikube -p heart-prayogshala kubectl -- -n heart-mlops port-forward service/heart-api 18002:80
minikube -p heart-prayogshala kubectl -- -n heart-mlops port-forward service/prometheus 19090:9090
minikube -p heart-prayogshala kubectl -- -n heart-mlops port-forward service/grafana 13000:3000
minikube -p heart-prayogshala kubectl -- -n ingress-nginx port-forward service/ingress-nginx-controller 18080:80
Then open INSIDE THE VM:
http://127.0.0.1:18002/docs
http://127.0.0.1:18080/health
http://127.0.0.1:19090/targets
http://127.0.0.1:13000/d/heart-api/heart-api-operations
If MINIKUBE_PROFILE was overridden, substitute that profile in these commands.
HELP
