import json

import joblib
import pytest
from fastapi.testclient import TestClient
from sklearn.linear_model import LogisticRegression

from heart_ml.api import app
from heart_ml.data import FEATURES, load_data
from heart_ml.model import build_pipeline


@pytest.fixture
def client(tmp_path, monkeypatch):
    frame = load_data()
    model = build_pipeline(LogisticRegression(max_iter=2000)).fit(frame[FEATURES], frame.target)
    path = tmp_path / "model.joblib"
    joblib.dump(model, path)
    monkeypatch.setenv("MODEL_PATH", str(path))
    with TestClient(app) as test_client:
        yield test_client


def patient():
    with open("examples/patient.json") as handle:
        return json.load(handle)


def test_prediction_health_and_metrics(client):
    assert client.get("/health").json()["status"] == "healthy"
    result = client.post("/predict", json=patient())
    assert result.status_code == 200
    body = result.json()
    assert body["prediction"] in [0, 1]
    assert 0 <= body["disease_probability"] <= 1
    assert 0.5 <= body["confidence"] <= 1
    assert "heart_api_requests_total" in client.get("/metrics").text


@pytest.mark.parametrize("change", [{"cp": 0}, {"age": -1}, {"thal": 4}, {"extra": 1}])
def test_invalid_input(client, change):
    assert client.post("/predict", json={**patient(), **change}).status_code == 422


def test_missing_and_nullable_features(client):
    payload = patient()
    del payload["age"]
    assert client.post("/predict", json=payload).status_code == 422
    assert client.post("/predict", json={**patient(), "ca": None, "thal": None}).status_code == 200
