# Live recording guide (approximately 5 minutes)

Record your screen while performing these steps. Explain each design decision in your own words. Do not describe prepared configurations as completed deployments.

1. Show repository layout and README; describe the Cleveland label mapping and dataset provenance.
2. Show `data/metadata.json`, the cleaned CSV and EDA plots. Explain why imputation happens inside CV folds.
3. Run training or show its actual saved log; open MLflow and compare the seven candidate runs and final evaluation. Explain CV selection versus held-out evaluation.
4. Show `pytest -q` and `ruff check .`. Open the actual GitHub Actions run after uploading the repository and show logs and artifacts.
5. Run `bash scripts/docker_verify.sh`; show real image build, health and prediction evidence.
6. Run `bash scripts/deploy_local.sh`, keep `minikube tunnel` open, and show deployment replicas, Service external address and a successful deployed request.
7. Start monitoring with Docker Compose, make a valid and invalid prediction request, show logs and Grafana request/latency panels.
8. Show the ten-page report, explain the small dataset limitation, and finish with repository URL and deployment access instructions.

Save the recording as `reports/pipeline_live_demo.mp4`. The generated local-results walkthrough, if present, is a supplementary visual summary and does not replace this live recording.
