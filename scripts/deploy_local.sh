#!/usr/bin/env bash
set -euo pipefail
docker build -t heart-api:1.0.0 .
minikube start
minikube image load heart-api:1.0.0
kubectl apply -f deployment/kubernetes.yaml
kubectl -n heart-mlops rollout status deployment/heart-api --timeout=180s
kubectl -n heart-mlops get deployments,pods,services
printf '\nRun minikube tunnel in another terminal, then use the service EXTERNAL-IP on port 80.\n'
