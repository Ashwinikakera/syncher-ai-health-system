# ml_service/models/regression.py

import numpy as np
import joblib
import os
from datetime import datetime, timedelta

MODEL_PATH = "ml_service/saved_models/regression.pkl"


def _generate_synthetic_training_data(n_samples: int = 200):
    """
    Generates synthetic training data to bootstrap the model
    before real user data is available.

    Features (X):
        avg_cycle_length, std_cycle_length, avg_period_length,
        avg_pain, avg_stress, avg_sleep

    Target (y):
        next_cycle_length  (what we're predicting)
    """
    np.random.seed(42)

    avg_cycle   = np.random.normal(28, 3, n_samples).clip(21, 45)
    std_cycle   = np.random.uniform(0, 7, n_samples)
    avg_period  = np.random.normal(5, 1, n_samples).clip(2, 9)
    avg_pain    = np.random.uniform(1, 8, n_samples)
    avg_stress  = np.random.uniform(1, 9, n_samples)
    avg_sleep   = np.random.uniform(4, 9, n_samples)

    # Target: next cycle length is mostly driven by avg_cycle_length
    # with small influence from stress and sleep
    noise = np.random.normal(0, 1.5, n_samples)
    next_cycle_length = (
        avg_cycle
        + (avg_stress - 5) * 0.4     # high stress → slightly longer cycle
        - (avg_sleep - 7) * 0.3      # poor sleep → slightly longer cycle
        + noise
    ).clip(21, 45)

    X = np.column_stack([
        avg_cycle, std_cycle, avg_period,
        avg_pain, avg_stress, avg_sleep
    ])
    y = next_cycle_length

    return X, y


def train_and_save():
    """Train regression model and save to disk."""
    from sklearn.linear_model import Ridge
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_absolute_error

    print(" Training regression model...")

    X, y = _generate_synthetic_training_data(300)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = Ridge(alpha=10.0)
    model.fit(X_train, y_train)

    mae = mean_absolute_error(y_test, model.predict(X_test))
    print(f"  ✅ Model trained — MAE: {mae:.2f} days")

    # Save model
    os.makedirs("ml_service/saved_models", exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"  ✅ Model saved to {MODEL_PATH}")

    return model


def load_model():
    if not os.path.exists(MODEL_PATH):
        print("  No saved model found - training fresh...")
        return train_and_save()
    model = joblib.load(MODEL_PATH)
    print(f"  Model loaded from {MODEL_PATH}")
    return model
 
 
def predict_next_cycle_length(model, features: dict) -> float:
    """
    Features dict uses API contract names:
    pain, sleep, stress (not pain_level, sleep_hours, stress_level)
    """
    X = np.array([[
        features.get("avg_cycle_length")  or 28,
        features.get("std_cycle_length")  or 2,
        features.get("avg_period_length") or 5,
        features.get("avg_pain")          or 3,   # sourced from contract: pain
        features.get("avg_stress")        or 4,   # sourced from contract: stress
        features.get("avg_sleep")         or 7,   # sourced from contract: sleep
    ]])
    return round(float(model.predict(X)[0]), 1)