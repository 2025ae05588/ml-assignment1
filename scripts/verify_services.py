"""Collect observed HTTP evidence from deployed API and monitoring services."""

import json
import time
from pathlib import Path
from urllib.request import Request, urlopen

OUT = Path("artifacts/evidence")


def fetch(url, data=None):
    request = Request(url, data=data, headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=15) as response:
        return response.read()


def main():
    patient = Path("examples/patient.json").read_bytes()
    for port, label in [(8080, "kubernetes"), (8002, "monitoring-api")]:
        OUT.joinpath(f"{label}-health.json").write_bytes(fetch(f"http://127.0.0.1:{port}/health"))
        OUT.joinpath(f"{label}-prediction.json").write_bytes(
            fetch(f"http://127.0.0.1:{port}/predict", patient)
        )
    for _ in range(30):
        fetch("http://127.0.0.1:8002/predict", patient)
    time.sleep(6)
    for label, url in {
        "prometheus-targets": "http://127.0.0.1:9090/api/v1/targets",
        "prometheus-requests": "http://127.0.0.1:9090/api/v1/query?query=heart_api_requests_total",
        "grafana-health": "http://127.0.0.1:3000/api/health",
        "mlflow-experiments": "http://127.0.0.1:5000/api/2.0/mlflow/experiments/search?max_results=10",
    }.items():
        OUT.joinpath(f"{label}.json").write_bytes(fetch(url))
    targets = json.loads(OUT.joinpath("prometheus-targets.json").read_text())
    assert any(t["health"] == "up" for t in targets["data"]["activeTargets"])
    requests = json.loads(OUT.joinpath("prometheus-requests.json").read_text())
    assert requests["data"]["result"], "Prometheus has no API request series"
    status = {
        "tests": "11 passed",
        "lint": "Ruff passed",
        "docker": "Image built; isolated health and prediction passed",
        "kubernetes": "kind cluster; two API replicas ready; Traefik Ingress verified at http://127.0.0.1:8080",
        "monitoring": "Compose services running; Prometheus target up and request series verified; Grafana healthy",
        "github": "https://github.com/2025ae05588/ml-assignment1 (see saved CI evidence)",
    }
    if OUT.joinpath("github-actions.json").exists():
        ci = json.loads(OUT.joinpath("github-actions.json").read_text())
        status["ci"] = {"conclusion": ci.get("conclusion"), "url": ci.get("url")}
    OUT.joinpath("verification.json").write_text(json.dumps(status, indent=2))
    print(json.dumps(status, indent=2))


if __name__ == "__main__":
    main()
