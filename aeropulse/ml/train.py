"""Train an illustrative demo model. NOT validated against real flight records."""
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.metrics import roc_auc_score
from ml.features import AIRPORTS, AIRLINES, FEATURES

ROOT = Path(__file__).resolve().parents[1]


def train_demo():
    rng = np.random.default_rng(42)
    n = 3500
    airports = list(AIRPORTS)
    origins = rng.choice(airports, n)
    destinations = rng.choice(airports, n)
    for i in range(n):
        if origins[i] == destinations[i]:
            destinations[i] = airports[(airports.index(origins[i]) + 1) % len(airports)]
    df = pd.DataFrame({'airline_code': rng.choice(list(AIRLINES), n), 'origin_code': origins,
                       'destination_code': destinations, 'month': rng.integers(1, 13, n),
                       'day_of_week': rng.integers(0, 7, n), 'departure_hour': rng.integers(0, 24, n)})
    # Synthetic probabilities are only for illustrating the complete software pipeline.
    p = np.clip(.13 + .12 * df.departure_hour.between(17, 22).to_numpy()
                + .07 * df.month.isin([6, 7, 8]).to_numpy()
                + .05 * df.origin_code.isin(['DEL', 'BOM']).to_numpy(), .02, .8)
    departure = rng.binomial(1, p)
    arrival = rng.binomial(1, np.clip(p + .10 + .09 * departure, .02, .9))
    cat = ['airline_code', 'origin_code', 'destination_code']
    pre = ColumnTransformer([('categories', OneHotEncoder(handle_unknown='ignore'), cat)], remainder='passthrough')
    results = {}
    for label, target in [('departure', departure), ('arrival', arrival)]:
        # This is an illustrative random holdout on synthetic data, NOT real-world validation.
        split = int(n * .8)
        model = Pipeline([('features', pre), ('classifier', RandomForestClassifier(
            n_estimators=100, min_samples_leaf=15, random_state=42, n_jobs=-1))])
        model.fit(df.iloc[:split][FEATURES], target[:split])
        score = roc_auc_score(target[split:], model.predict_proba(df.iloc[split:][FEATURES])[:, 1])
        results[label] = score
        joblib.dump(model, ROOT / 'ml' / f'{label}_demo.joblib')
    return results


if __name__ == '__main__':
    print('Synthetic demo validation only:', train_demo())
