# ml_service/training/train_on_real_data.py
# Replaces synthetic training with real DB data
# Run this manually once enough users have entered data,
# OR let retrain.py call it automatically via Celery.

import numpy as np
import joblib
from pathlib import Path
from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

from ml_service.data.db_fetcher import fetch_all_users_training_data

SAVED_MODELS_DIR = Path(__file__).parent.parent / "saved_models"

# Minimum real records needed before we trust real-data training
MIN_REAL_RECORDS = 10


def train_regression_on_real_data() -> dict:
    """
    Fetches real cycle data from DB and trains Ridge regression.
    Falls back to synthetic data if not enough real data yet.

    Returns:
        {
            "source":     "real" | "synthetic",
            "n_samples":  int,
            "mae":        float,
            "model":      Ridge,
        }
    """
    print("\n  Fetching real training data from DB...")
    real_data = fetch_all_users_training_data()

    if len(real_data) >= MIN_REAL_RECORDS:
        print(f"  Found {len(real_data)} real records — training on real data")
        X, y = _build_feature_matrix(real_data)
        source = "real"
    else:
        print(f"  Only {len(real_data)} real records (need {MIN_REAL_RECORDS})")
        print("  Falling back to synthetic data for now...")
        X, y  = _generate_synthetic_data(300)
        source = "synthetic"

    # Train / evaluate
    if len(X) >= 10:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
    else:
        X_train, X_test = X, X
        y_train, y_test = y, y

    model = Ridge(alpha=10.0)   # best alpha from Day 7 CV
    model.fit(X_train, y_train)
    mae = round(mean_absolute_error(y_test, model.predict(X_test)), 3)

    # Save
    SAVED_MODELS_DIR.mkdir(exist_ok=True)
    model_path = SAVED_MODELS_DIR / "regression.pkl"
    joblib.dump(model, model_path)

    print(f"  Source    : {source}")
    print(f"  Samples   : {len(X)}")
    print(f"  MAE       : {mae} days")
    print(f"  Saved to  : {model_path}")

    return {"source": source, "n_samples": len(X), "mae": mae, "model": model}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_feature_matrix(records: list[dict]):
    """
    Converts DB records into numpy X, y arrays.
    Matches regression.py's 6-feature order exactly:
    [avg_cycle_length, std_cycle_length, avg_period_length,
     avg_pain, avg_stress, avg_sleep]
    """
    X = np.array([
        [
            r.get("avg_cycle_length")  or 28,
            r.get("std_cycle_length")  or 2,
            r.get("avg_period_length") or 5,
            r.get("avg_pain")          or 3,
            r.get("avg_stress")        or 4,
            r.get("avg_sleep")         or 7,
        ]
        for r in records
    ])
    y = np.array([r["actual_next_length"] for r in records])
    return X, y


def _generate_synthetic_data(n: int = 300):
    """Same synthetic data as original regression.py — used as fallback only."""
    np.random.seed(42)

    avg_cycle  = np.random.normal(28, 3, n).clip(21, 45)
    std_cycle  = np.random.uniform(0, 7, n)
    avg_period = np.random.normal(5, 1, n).clip(2, 9)
    avg_pain   = np.random.uniform(1, 8, n)
    avg_stress = np.random.uniform(1, 9, n)
    avg_sleep  = np.random.uniform(4, 9, n)

    X = np.column_stack([avg_cycle, std_cycle, avg_period,
                         avg_pain, avg_stress, avg_sleep])
    y = (
        avg_cycle
        + (avg_stress - 5) * 0.4
        - (avg_sleep  - 7) * 0.3
        + np.random.normal(0, 1.5, n)
    ).clip(21, 45)

    return X, y


# ── Run directly ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 55)
    print(" Training on Real DB Data")
    print("=" * 55)
    result = train_regression_on_real_data()
    print(f"\n  Done — source={result['source']}, MAE={result['mae']} days")