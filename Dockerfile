FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 MODEL_PATH=/app/artifacts/model.joblib
WORKDIR /app
COPY requirements.txt pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir -e . && useradd --uid 10001 --create-home serving
COPY artifacts/model.joblib artifacts/metrics.json ./artifacts/
USER serving
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=3)"
CMD ["uvicorn", "heart_ml.api:app", "--host", "0.0.0.0", "--port", "8000"]
