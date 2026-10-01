import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression

from heart_ml.data import FEATURES, load_data
from heart_ml.model import build_pipeline


def test_pipeline_serialization_and_training_only_imputation(tmp_path):
    frame = load_data()
    train = frame.iloc[:180]
    model = build_pipeline(LogisticRegression(max_iter=2000)).fit(train[FEATURES], train.target)
    imputer = model.named_steps["preprocess"].named_transformers_["numeric"].named_steps["impute"]
    assert imputer.statistics_[0] == train.age.median()
    sample = frame.iloc[180:190][FEATURES].copy()
    sample.loc[sample.index[0], "ca"] = np.nan
    path = tmp_path / "model.joblib"
    joblib.dump(model, path)
    restored = joblib.load(path)
    np.testing.assert_allclose(model.predict_proba(sample), restored.predict_proba(sample))
    assert np.isfinite(restored.predict_proba(sample)).all()
