# ml_service/retrain.py
# Day 7 Task 3 — UPDATED: now pulls real data from DB automatically
# Dev1's Celery tasks.py calls: from ml_service.retrain import trigger_retrain

import numpy as np
import joblib
from pathlib import Path
from datetime import datetime
from sklearn.linear_model import Ridge

from ml_service.data.db_fetcher import fetch_all_users_training_data

SAVED_MODELS_DIR = Path(__file__).parent / "saved_models"
RETRAIN_LOG      = Path(__file__).parent / "retrain_log.txt"

MIN_NEW_CYCLES = 10   # raised from 3 — need more real data for meaningful retraining


def trigger_retrain() -> dict:
    """
    Called by Dev1's Celery scheduler (e.g. every week).
    Automatically fetches latest real data from DB and retrains.

    No arguments needed — pulls data itself via db_fetcher.

    Returns:
        {
            "status":       "retrained" | "skipped",
            "reason":       str,
            "samples_used": int,
            "old_mae":      float | None,
            "new_mae":      float | None,
            "improved":     bool | None,
            "timestamp":    str,
        }
    """
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    print("  Fetching training data from DB...")
    real_data = fetch_all_users_training_data()
    valid     = [r for r in real_data if r.get("actual_next_length")]

    if len(valid) < MIN_NEW_CYCLES:
        msg = f"Only {len(valid)} real records - need {MIN_NEW_CYCLES} to retrain"
        _log(timestamp, "SKIPPED", msg)
        return {
            "status":       "skipped",
            "reason":       msg,
            "samples_used": len(valid),
            "old_mae":      None,
            "new_mae":      None,
            "improved":     None,
            "timestamp":    timestamp,
        }

    # Build feature matrix - 6 cols matching regression.py
    X = np.array([
        [
            r.get("avg_cycle_length")  or 28,
            r.get("std_cycle_length")  or 2,
            r.get("avg_period_length") or 5,
            r.get("avg_pain")          or 3,
            r.get("avg_stress")        or 4,
            r.get("avg_sleep")         or 7,
        ]
        for r in valid
    ])
    y = np.array([r["actual_next_length"] for r in valid])

    # Evaluate old model before overwriting
    model_path = SAVED_MODELS_DIR / "regression.pkl"
    old_mae = None
    if model_path.exists():
        try:
            old_model = joblib.load(model_path)
            old_preds = old_model.predict(X)
            old_mae   = round(float(np.mean(np.abs(old_preds - y))), 3)
        except Exception:
            old_mae = None  # feature mismatch - old model incompatible

    # Train new model
    new_model = Ridge(alpha=10.0)
    new_model.fit(X, y)
    new_preds = new_model.predict(X)
    new_mae   = round(float(np.mean(np.abs(new_preds - y))), 3)

    # Only save if new model is actually better
    improved = (old_mae is None) or (new_mae < old_mae)

    if improved:
        SAVED_MODELS_DIR.mkdir(exist_ok=True)
        joblib.dump(new_model, model_path)
        msg = f"Retrained on {len(valid)} real samples | old_mae={old_mae} -> new_mae={new_mae} days"
        _log(timestamp, "RETRAINED", msg)
    else:
        msg = f"New model not better - skipping save | old_mae={old_mae}, new_mae={new_mae}"
        _log(timestamp, "SKIPPED", msg)

    return {
        "status":       "retrained" if improved else "skipped",
        "reason":       msg,
        "samples_used": len(valid),
        "old_mae":      old_mae,
        "new_mae":      new_mae,
        "improved":     improved,
        "timestamp":    timestamp,
    }


def _log(timestamp: str, status: str, message: str):
    line = f"[{timestamp}] {status}: {message}\n"
    with open(RETRAIN_LOG, "a", encoding="utf-8") as f:
        f.write(line)
    print(f"  Retrain log: [{timestamp}] {status}: {message}")