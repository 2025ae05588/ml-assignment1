import json
import logging
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

import joblib
import pandas as pd
from fastapi import FastAPI, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from pydantic import BaseModel, ConfigDict, Field

from heart_ml.data import FEATURES

logger = logging.getLogger("heart_ml.requests")
logging.basicConfig(level=logging.INFO, format="%(message)s")
REQUESTS = Counter("heart_api_requests_total", "Requests by route and status", ["route", "status"])
LATENCY = Histogram("heart_api_request_duration_seconds", "Request duration", ["route"])


class Patient(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    age: float = Field(ge=1, le=120)
    sex: Literal[0, 1]
    cp: Literal[1, 2, 3, 4]
    trestbps: float = Field(gt=0, le=350)
    chol: float = Field(gt=0, le=1000)
    fbs: Literal[0, 1]
    restecg: Literal[0, 1, 2]
    thalach: float = Field(gt=0, le=300)
    exang: Literal[0, 1]
    oldpeak: float = Field(ge=0, le=15)
    slope: Literal[1, 2, 3]
    ca: Literal[0, 1, 2, 3] | None
    thal: Literal[3, 6, 7] | None


@asynccontextmanager
async def lifespan(app):
    path = Path(os.getenv("MODEL_PATH", "artifacts/model.joblib"))
    if not path.is_file():
        raise RuntimeError(f"Model missing: {path}. Run scripts/train.py first.")
    app.state.model = joblib.load(path)
    metadata_path = path.with_name("metrics.json")
    app.state.version = (
        json.loads(metadata_path.read_text())["mlflow_run_id"]
        if metadata_path.exists()
        else "unknown"
    )
    yield


app = FastAPI(title="Cleveland Heart Disease Classifier", version="1.0.0", lifespan=lifespan)


@app.middleware("http")
async def observe(request: Request, call_next):
    started = time.perf_counter()
    status = 500
    try:
        response = await call_next(request)
        status = response.status_code
        return response
    finally:
        route = request.scope.get("route")
        route_name = route.path if route else "unmatched"
        duration = time.perf_counter() - started
        REQUESTS.labels(route_name, str(status)).inc()
        LATENCY.labels(route_name).observe(duration)
        logger.info(
            json.dumps(
                {
                    "method": request.method,
                    "route": route_name,
                    "status": status,
                    "duration_seconds": round(duration, 6),
                }
            )
        )


@app.get("/health")
def health(request: Request):
    return {"status": "healthy", "model_version": request.app.state.version}


@app.post("/predict")
def predict(patient: Patient, request: Request):
    frame = pd.DataFrame([patient.model_dump()], columns=FEATURES).astype(float)
    probability = float(request.app.state.model.predict_proba(frame)[0, 1])
    prediction = int(probability >= 0.5)
    return {
        "prediction": prediction,
        "disease_probability": probability,
        "confidence": probability if prediction else 1 - probability,
        "model_version": request.app.state.version,
        "usage": "Educational classifier; not a clinical diagnosis.",
    }


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
