from datetime import datetime
import pytest
from ml.features import build_features


def test_valid_flight():
    f = build_features('6E 203', 'HYD', 'DEL', datetime(2026, 11, 16, 18))
    assert f['airline_code'] == '6E'
    assert f['departure_hour'] == 18


def test_invalid_route():
    with pytest.raises(ValueError):
        build_features('6E203', 'HYD', 'HYD', datetime(2026, 11, 16, 18))
