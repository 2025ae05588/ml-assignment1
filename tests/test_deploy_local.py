"""Exercise deployment command order without changing a real cluster."""

import os
import shutil
import subprocess
from pathlib import Path


def test_content_image_and_admission_retry(tmp_path):
    root = Path(__file__).resolve().parents[1]
    shutil.copytree(root / "deployment", tmp_path / "deployment")
    (tmp_path / "scripts").mkdir()
    shutil.copy2(root / "scripts/deploy_local.sh", tmp_path / "scripts/deploy_local.sh")
    binaries = tmp_path / "bin"
    binaries.mkdir()
    docker = binaries / "docker"
    docker.write_text(
        '#!/bin/bash\nprintf "docker %s\\n" "$*" >> "$COMMAND_LOG"\n'
        'if [[ "$1 $2" == "image inspect" ]]; then echo sha256:abc123; fi\n'
    )
    minikube = binaries / "minikube"
    minikube.write_text(
        '#!/bin/bash\nprintf "minikube %s\\n" "$*" >> "$COMMAND_LOG"\n'
        'if [[ "$*" == *"apply -f deployment/minikube/ingress.yaml"* ]]; then\n'
        '  if [[ ! -f "$RETRY_MARKER" ]]; then touch "$RETRY_MARKER"; exit 1; fi\n'
        'fi\n'
        'if [[ "$*" == *"apply -f /"* ]]; then\n'
        '  cat "${@: -1}" > "$APPLIED_MANIFEST"\n'
        'fi\n'
    )
    (binaries / "sleep").write_text("#!/bin/sh\nexit 0\n")
    for binary in binaries.iterdir():
        binary.chmod(0o755)
    log = tmp_path / "commands.log"
    applied = tmp_path / "applied.yaml"
    env = {
        **os.environ,
        "PATH": str(binaries) + os.pathsep + os.environ["PATH"],
        "COMMAND_LOG": str(log),
        "RETRY_MARKER": str(tmp_path / "retried"),
        "APPLIED_MANIFEST": str(applied),
    }
    subprocess.run(["bash", "scripts/deploy_local.sh"], cwd=tmp_path, env=env, check=True)
    commands = log.read_text()
    assert "image load heart-api:build-abc123" in commands
    assert "image: heart-api:build-abc123" in applied.read_text()
    assert "image: heart-api:1.0.0" in (tmp_path / "deployment/kubernetes.yaml").read_text()
    assert commands.index("--for=condition=complete") < commands.index(
        "apply -f deployment/minikube/ingress.yaml"
    )
    assert commands.count("apply -f deployment/minikube/ingress.yaml") == 2
    assert "rollout status deployment/heart-api" in commands
