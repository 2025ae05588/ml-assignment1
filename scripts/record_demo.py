"""Record real command outputs and evidence into a narrated-by-captions MP4.

This is a terminal-output recording, not an operating-system screen capture.
Raw command results accompany the video for audit.
"""

import json
import os
import subprocess
import textwrap
from datetime import datetime, timezone
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FONT = "/System/Library/Fonts/Supplemental/Arial.ttf"
if not Path(FONT).exists():
    FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def main():
    commands = [
        ("1. Dataset provenance and cleaning", ["cat", "data/metadata.json"]),
        ("2. Cross-validation selection and held-out results", ["cat", "artifacts/metrics.json"]),
        ("3. Automated test evidence", ["cat", "artifacts/evidence/tests.log"]),
        (
            "4. Container build and isolated prediction proof",
            ["cat", "artifacts/evidence/docker-prediction.json"],
        ),
        (
            "5. Live Kubernetes replicas and Ingress",
            [
                "kubectl",
                "--kubeconfig",
                "deployment/kubeconfig",
                "-n",
                "heart-mlops",
                "get",
                "deployments,pods,ingress",
            ],
        ),
        (
            "6. Live deployed prediction through Ingress",
            [
                "curl",
                "-fsS",
                "http://127.0.0.1:8080/predict",
                "-H",
                "Content-Type: application/json",
                "--data",
                "@examples/patient.json",
            ],
        ),
        ("7. Live monitoring stack", ["docker", "compose", "-f", "deployment/compose.yaml", "ps"]),
        (
            "8. Live Prometheus scrape status",
            ["curl", "-fsS", "http://127.0.0.1:9090/api/v1/targets"],
        ),
        ("9. Verified implementation status", ["cat", "artifacts/evidence/verification.json"]),
        (
            "10. Actual successful GitHub Actions evidence",
            ["cat", "artifacts/evidence/github-actions.json"],
        ),
    ]
    env = {
        **os.environ,
        "PATH": "/Applications/Docker.app/Contents/Resources/bin:" + os.environ["PATH"],
    }
    title_font = ImageFont.truetype(FONT, 30)
    font = ImageFont.truetype(FONT, 19)
    footer_font = ImageFont.truetype(FONT, 16)
    records = []
    video = ROOT / "reports/pipeline_terminal_demo.mp4"
    with imageio.get_writer(video, fps=10, codec="libx264", quality=7) as writer:

        def append(image, seconds=7):
            for _ in range(seconds * 10):
                writer.append_data(np.asarray(image))

        def frame(title, body):
            im = Image.new("RGB", (1280, 720), "#0f172a")
            draw = ImageDraw.Draw(im)
            draw.text((35, 24), title, font=title_font, fill="#67e8f9")
            lines = []
            for line in body.splitlines():
                lines.extend(textwrap.wrap(line, 105, replace_whitespace=False) or [""])
            for i, line in enumerate(lines[:26]):
                draw.text((35, 90 + i * 21), line, font=font, fill="#e2e8f0")
            draw.text(
                (35, 681),
                "Recorded command outputs | See demo_commands.json for timestamps and exit codes",
                font=footer_font,
                fill="#94a3b8",
            )
            return im

        append(
            frame(
                "Heart Disease MLOps - verified local pipeline",
                "UCI Cleveland data -> CV models -> MLflow -> FastAPI -> Docker -> Kubernetes Ingress -> monitoring\n\nThis video records actual command outputs and includes genuine browser screenshots.\nIt is not a desktop screen capture. Previously generated training/test/build artifacts are labelled as evidence.\nThe successful GitHub Actions run is shown as saved remote evidence; all service commands execute against the live local deployment.",
            ),
            8,
        )
        screenshots = {
            1: ("EDA distributions", "artifacts/eda/histograms.png"),
            2: ("Actual MLflow candidate runs", "screenshots/mlflow-runs.jpg"),
            7: ("Actual Grafana dashboard", "screenshots/grafana-dashboard.jpg"),
            9: ("Actual successful GitHub Actions run", "screenshots/github-actions-success.jpg"),
        }
        for index, (title, command) in enumerate(commands, 1):
            result = subprocess.run(
                command, cwd=ROOT, env=env, capture_output=True, text=True, timeout=30
            )
            output = result.stdout + result.stderr
            if command[0] == "curl":
                try:
                    output = json.dumps(json.loads(result.stdout), indent=2)
                except json.JSONDecodeError:
                    pass
            records.append(
                {
                    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                    "title": title,
                    "command": command,
                    "exit_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                }
            )
            rendered = frame(title, "$ " + " ".join(command) + "\n\n" + output)
            append(rendered, 9)
            if index == 5:
                rendered.save(ROOT / "screenshots/kubernetes-terminal-evidence.png")
            if index in screenshots:
                label, path = screenshots[index]
                if (ROOT / path).exists():
                    im = frame(label, "")
                    source = Image.open(ROOT / path).convert("RGB")
                    source.thumbnail((1200, 560))
                    im.paste(source, ((1280 - source.width) // 2, 92))
                    append(im, 8)
    (ROOT / "reports/demo_commands.json").write_text(json.dumps(records, indent=2))
    print(video)
    if any(record["exit_code"] != 0 for record in records):
        raise RuntimeError("A recorded command failed; inspect demo_commands.json")


if __name__ == "__main__":
    main()
