#!/usr/bin/env bash
set -euo pipefail
mkdir -p artifacts/evidence
docker build -t heart-api:1.0.0 . 2>&1 | tee artifacts/evidence/docker-build.log
docker run -d --name heart-assignment-verification -p 8001:8000 heart-api:1.0.0
trap 'docker logs heart-assignment-verification > artifacts/evidence/docker.log 2>&1; docker rm -f heart-assignment-verification >/dev/null' EXIT
for attempt in $(seq 1 30); do
  if curl -fsS http://localhost:8001/health; then break; fi
  sleep 2
done
curl -fsS http://localhost:8001/health > artifacts/evidence/docker-health.json
curl -fsS http://localhost:8001/predict -H 'Content-Type: application/json' --data @examples/patient.json > artifacts/evidence/docker-prediction.json
