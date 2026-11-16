"""Train only from independently obtained, legal historical flight-delay records.

This module intentionally ships with NO fabricated historical labels. It creates
real model artifacts only when a valid history CSV has been supplied explicitly.
"""
from pathlib import Path
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score, log_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from ml.features import FEATURES, AIRLINES

REQUIRED = [
    "flight_date", "airline_code", "origin_code", "destination_code",
    "scheduled_departure_hour", "departure_delay_minutes", "arrival_delay_minutes",
]

def prepare_history(df):
    """Validate and transform observed delay labels, without using target leakage."""
    missing=[name for name in REQUIRED if name not in df.columns]
    if missing:
        raise ValueError("History CSV missing columns: "+", ".join(missing))
    data=df[REQUIRED].copy()
    data["flight_date"]=pd.to_datetime(data["flight_date"],errors="coerce")
    if data["flight_date"].isna().any():
        raise ValueError("Invalid flight dates")
    if data["flight_date"].dt.tz is not None:
        data["flight_date"]=data["flight_date"].dt.tz_convert(None)
    for field in ("scheduled_departure_hour","departure_delay_minutes","arrival_delay_minutes"):
        data[field]=pd.to_numeric(data[field],errors="coerce")
    if data[["scheduled_departure_hour","departure_delay_minutes","arrival_delay_minutes"]].isna().any().any():
        raise ValueError("Historical delay and hour values must be numeric")
    if not data["scheduled_departure_hour"].between(0,23).all():
        raise ValueError("Scheduled departure hour outside 0–23")
    if data[["airline_code","origin_code","destination_code"]].isna().any().any():
        raise ValueError("Missing airline or route code")
    if data["origin_code"].eq(data["destination_code"]).any():
        raise ValueError("Origin and destination cannot be equal")
    data["month"]=data["flight_date"].dt.month
    data["day_of_week"]=data["flight_date"].dt.dayofweek
    data["departure_hour"]=data["scheduled_departure_hour"].astype(int)
    # These outcomes must have been observed, never forecasts or guessed data.
    data["departure_delay"]=(data["departure_delay_minutes"]>=15).astype(int)
    data["arrival_delay"]=(data["arrival_delay_minutes"]>=15).astype(int)
    return data.sort_values("flight_date").reset_index(drop=True)

def chronological_split(data, test_fraction=0.2):
    """Date-blocked holdout prevents the same calendar date appearing in both sets."""
    if len(data)<200:
        raise ValueError("Need at least 200 genuine observed flight records")
    unique_dates=sorted(data["flight_date"].dt.normalize().unique())
    if len(unique_dates)<10:
        raise ValueError("Need at least 10 distinct observed flight dates")
    boundary=unique_dates[max(1,int(len(unique_dates)*(1-test_fraction)))]
    train=data[data["flight_date"]<boundary]
    test=data[data["flight_date"]>=boundary]
    if len(train)<100 or len(test)<25:
        raise ValueError("Not enough rows on either side of chronological boundary")
    return train,test

def train_from_history(input_csv, output_dir):
    data=prepare_history(pd.read_csv(input_csv))
    train,test=chronological_split(data)
    output=Path(output_dir)
    output.mkdir(parents=True,exist_ok=True)
    cat=["airline_code","origin_code","destination_code"]
    metrics={}
    for name,label in [("departure","departure_delay"),("arrival","arrival_delay")]:
        if train[label].nunique()!=2 or test[label].nunique()!=2:
            raise ValueError(f"Both train and holdout must include delayed and on-time {name} flights")
        model=Pipeline([
            ("encode",ColumnTransformer([("categorical",OneHotEncoder(handle_unknown="ignore"),cat)],remainder="passthrough")),
            ("classifier",LogisticRegression(max_iter=1000)),
        ])
        model.fit(train[FEATURES],train[label])
        probs=np.asarray(model.predict_proba(test[FEATURES])[:,1])
        metrics[name]={
            "roc_auc":round(float(roc_auc_score(test[label],probs)),4),
            "brier":round(float(brier_score_loss(test[label],probs)),4),
            "holdout_count":int(len(test)),
            "training_count":int(len(train)),
        }
        joblib.dump(model,output/f"{name}_real.joblib")
    metadata={
        "model_data":"historical_observed",
        "rows":len(data),
        "date_start":data["flight_date"].min().date().isoformat(),
        "date_end":data["flight_date"].max().date().isoformat(),
        "train_end":train["flight_date"].max().date().isoformat(),
        "test_start":test["flight_date"].min().date().isoformat(),
        "metrics":metrics,
        "limitations":"Training data provenance, distribution and representativeness must be independently audited.",
    }
    (output/"model_validation.json").write_text(json.dumps(metadata,indent=2),encoding="utf-8")
    return metadata

if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--history",required=True,help="CSV of independently observed historical flights")
    parser.add_argument("--output",default="ml")
    args=parser.parse_args()
    print(json.dumps(train_from_history(args.history,args.output),indent=2))
