"""Offline regression tests, never represented as real historical flights."""
import numpy as np
import pandas as pd
import pytest
from ml.real_training import prepare_history, chronological_split, train_from_history

def fake_history():
    rng=np.random.default_rng(2026)
    n=360
    day=np.repeat(pd.date_range("2026-08-01", periods=30, freq="D"),12)
    airline=rng.choice(["6E","AI","QP"],n)
    origin=rng.choice(["HYD","DEL","BOM","BLR"],n)
    destination=np.where(origin=="DEL","HYD","DEL")
    hour=rng.integers(5,23,n)
    dep=rng.choice([0,8,18,34,55],n)
    arr=rng.choice([0,5,24,45],n)
    return pd.DataFrame({
        "flight_date":day.astype(str),"airline_code":airline,
        "origin_code":origin,"destination_code":destination,
        "scheduled_departure_hour":hour,
        "departure_delay_minutes":dep,"arrival_delay_minutes":arr,
    })

def test_observed_history_has_time_separated_holdout():
    data=prepare_history(fake_history())
    earlier,later=chronological_split(data)
    assert earlier.flight_date.max()<later.flight_date.min()
    assert (data["departure_delay"]==(data.departure_delay_minutes>=15)).all()

def test_requires_real_outcome_labels():
    df=fake_history().drop(columns=["arrival_delay_minutes"])
    with pytest.raises(ValueError,match="missing columns"):
        prepare_history(df)

def test_real_training_works_only_when_explicit_csv_provided(tmp_path):
    path=tmp_path/"synthetic-unit-test-input.csv"
    fake_history().to_csv(path,index=False)
    # Synthetic data is solely used to TEST the pipeline; never shipped as a real model.
    meta=train_from_history(path,tmp_path/"models")
    assert meta["model_data"]=="historical_observed"
    assert meta["metrics"]["departure"]["holdout_count"]>=25
    assert (tmp_path/"models"/"departure_real.joblib").exists()
    assert (tmp_path/"models"/"model_validation.json").exists()

def test_rejects_too_little_history():
    data=prepare_history(fake_history().head(50))
    with pytest.raises(ValueError,match="at least 200"):
        chronological_split(data)
