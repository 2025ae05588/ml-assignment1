#!/usr/bin/env bash
# Noninteractive Minikube deployment for the assignment.
set -euo pipefail
cd "$(dirname "$0")/.."
profile="${MINIKUBE_PROFILE:-heart-prayogshala}"
export KUBECONFIG="$PWD/deployment/kubeconfig"
docker build -t heart-api:1.0.0 .
# Docker's content ID changes when the packaged model/metadata changes.
image_id="$(docker image inspect heart-api:1.0.0 --format '{{.Id}}')"
image="heart-api:build-${image_id#sha256:}"
docker tag heart-api:1.0.0 "$image"
manifest="$(mktemp)"
trap 'rm -f "$manifest"' EXIT
sed "s|image: heart-api:1.0.0|image: $image|" deployment/kubernetes.yaml > "$manifest"
printf 'Deploying model image: %s\n' "$image"
minikube -p "$profile" start --driver=docker --cpus=2 --memory=3072 --kubernetes-version=v1.32.2
minikube -p "$profile" image load "$image"
# Use the cluster-matched kubectl and an explicit context for every operation.
kube() { minikube -p "$profile" kubectl -- --context "$profile" "$@"; }
kube apply -f "$manifest"
minikube -p "$profile" addons enable ingress
# Enabling the addon can return before its admission endpoint accepts requests.
kube -n ingress-nginx rollout status deployment/ingress-nginx-controller --timeout=360s
kube -n ingress-nginx wait --for=condition=complete job \
  -l app.kubernetes.io/component=admission-webhook --timeout=360s
applied=0
for attempt in {1..12}; do
  if kube apply -f deployment/minikube/ingress.yaml; then
    applied=1
    break
  fi
  printf 'Ingress apply attempt %s failed; waiting for admission readiness.\n' "$attempt"
  sleep 5
done
if [[ "$applied" != 1 ]]; then
  kube -n ingress-nginx get pods,jobs,endpointslices -o wide || true
  echo 'Ingress application failed after 12 attempts.' >&2
  exit 1
fi
kube apply -f deployment/minikube/monitoring.json
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
