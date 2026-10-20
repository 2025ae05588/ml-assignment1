"""Render the architecture for the current local Minikube deployment."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


def main():
    output = Path("artifacts")
    output.mkdir(exist_ok=True)
    fig, ax = plt.subplots(figsize=(16, 9))
    fig.patch.set_facecolor("#f4f7fa")
    ax.set(xlim=(0, 16), ylim=(0, 9))
    ax.axis("off")
    ink, teal = "#17364b", "#16798a"

    def box(x, y, width, height, title, detail):
        ax.add_patch(FancyBboxPatch(
            (x, y), width, height, boxstyle="round,pad=0.14,rounding_size=0.12",
            facecolor="white", edgecolor=teal, linewidth=1.7,
        ))
        ax.text(x + 0.18, y + height - 0.32, title, fontsize=12,
                weight="bold", color=ink, va="top")
        ax.text(x + 0.18, y + height - 0.75, detail, fontsize=10.7,
                color=ink, va="top", linespacing=1.6)

    def arrow(start, end, label=None, dashed=False):
        ax.add_patch(FancyArrowPatch(
            start, end, arrowstyle="-|>", mutation_scale=15,
            linewidth=1.6, color=teal, linestyle="--" if dashed else "-",
        ))
        if label:
            ax.text((start[0] + end[0]) / 2, (start[1] + end[1]) / 2 + 0.13,
                    label, ha="center", fontsize=10, color=ink,
                    bbox={"facecolor": "#f4f7fa", "edgecolor": "none", "pad": 2})

    ax.text(0.6, 8.5, "Heart Disease MLOps Architecture", fontsize=25,
            weight="bold", color=teal)
    ax.text(0.6, 8.08, "Training, tracked experiments and local Minikube serving",
            fontsize=12, color=ink)
    box(0.7, 5.9, 4.0, 1.65, "Data preparation + EDA",
        "UCI Cleveland: download, hash, clean\nCleaned CSV + generated charts")
    box(6.0, 5.9, 4.0, 1.65, "Training + model selection",
        "Fold-local preprocessing + tuning\n5-fold CV selection; held-out test")
    box(11.3, 5.9, 4.0, 1.65, "MLflow experiment tracking",
        "Logs parameters, metrics and plots\nStores model artifacts + run IDs")
    arrow((4.85, 6.7), (5.85, 6.7))
    arrow((10.15, 6.7), (11.15, 6.7), "logs")

    ax.add_patch(FancyBboxPatch(
        (0.45, 1.72), 15.1, 3.45,
        boxstyle="round,pad=0.08,rounding_size=0.15",
        facecolor="#e6f1f3", edgecolor=teal, linewidth=1.7,
    ))
    ax.text(0.75, 4.72, "MINIKUBE  |  Docker driver",
            fontsize=11.5, weight="bold", color=ink)
    ax.text(0.75, 4.40, "API + monitoring namespace: heart-mlops",
            fontsize=10, color=ink)
    box(0.85, 2.25, 4.0, 1.85, "NGINX Ingress",
        "Controller namespace: ingress-nginx\nVM access: 127.0.0.1:18080\n(port-forward to Ingress controller)")
    box(6.0, 2.25, 4.0, 1.85, "FastAPI Service + 2 replicas",
        "Docker image + saved joblib pipeline\n/predict   /health   /metrics\nReadiness + liveness probes")
    box(11.2, 2.25, 3.95, 1.85, "Monitoring inside Minikube",
        "Prometheus scrapes API /metrics\nGrafana queries Prometheus\nRequest rate, errors, latency, counts")
    arrow((4.99, 3.14), (5.85, 3.14))
    arrow((10.15, 3.14), (11.05, 3.14), "metrics")
    arrow((8.0, 5.75), (8.0, 4.25))
    ax.text(8.18, 5.4, "Saved preprocessing + classifier\nPackaged with FastAPI in Docker",
            fontsize=10.5, color=ink, va="top", linespacing=1.5,
            bbox={"facecolor": "#f4f7fa", "edgecolor": "none", "pad": 3})
    ax.text(0.8, 1.93,
            "Direct VM browser ports: API docs 18002  |  Prometheus 19090  |  Grafana 13000",
            fontsize=10.5, color=ink)
    ax.text(0.7, 1.1,
            "GitHub Actions: lint -> tests -> EDA / training -> Docker build -> isolated API smoke test -> artifacts",
            fontsize=12, weight="bold", color=ink)
    ax.text(0.7, 0.62,
            "CI verifies the project. Local Minikube deployment is a separate step; CI does not deploy to the VM.",
            fontsize=11, color=ink)
    fig.savefig(output / "architecture.png", dpi=180, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    fig.savefig(output / "architecture.svg", bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    print("Updated artifacts/architecture.png and artifacts/architecture.svg")


if __name__ == "__main__":
    main()
