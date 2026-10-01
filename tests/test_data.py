import numpy as np
import pandas as pd
import pytest

from heart_ml.data import FEATURES, clean_data


def raw():
    return pd.DataFrame(
        [
            [63, 1, 1, 145, 233, 1, 2, 150, 0, 2.3, 3, "?", 6, 0],
            [67, 1, 4, 160, 286, 0, 2, 108, 1, 1.5, 2, 3, 3, 4],
        ],
        columns=FEATURES + ["num"],
    )


def test_cleaning_preserves_missing_and_maps_target():
    source = raw()
    result = clean_data(pd.concat([source, source.iloc[[0]]]))
    assert len(result) == 2
    assert result.target.tolist() == [0, 1]
    assert np.isnan(result.loc[0, "ca"])
    assert source.loc[0, "ca"] == "?"


@pytest.mark.parametrize("column,value", [("num", 5), ("num", np.nan), ("cp", 0)])
def test_bad_data_rejected(column, value):
    frame = raw()
    frame.loc[0, column] = value
    with pytest.raises(ValueError):
        clean_data(frame)
