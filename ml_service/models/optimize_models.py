# ml_service/models/optimize_models.py
# Day 7 — Task 1: Optimize model accuracy

import numpy as np
import joblib
from pathlib import Path
from sklearn.linear_model import Ridge
from sklearn.model_selection import cross_val_score, KFold
from sklearn.metrics import mean_absolute_error

SAVED_MODELS_DIR = Path(__file__).parent.parent / "saved_models"

# ── Feature order must match regression.py exactly ───────────────────────────
# [avg_cycle_length, std_cycle_length, avg_period_length,
#  avg_pain, avg_stress, avg_sleep]
FEATURE_DEFAULTS = {
    "avg_cycle_length":  28,
    "std_cycle_length":  2,
    "avg_period_length": 5,
    "avg_pain":          3,
    "avg_stress":        4,
    "avg_sleep":         7,
}


# ── Regression optimizer ──────────────────────────────────────────────────────

def optimize_regression(X: np.ndarray, y: np.ndarray) -> dict:
    """
    Replaces plain LinearRegression with Ridge (regularized).
    Runs 5-fold CV across alphas and saves best model to regression.pkl.

    X must have 6 columns matching FEATURE_DEFAULTS order.

    Returns:
        {"best_alpha": float, "cv_mae": float, "model": Ridge}
    """
    alphas = [0.01, 0.1, 1.0, 5.0, 10.0, 50.0]
    kf = KFold(n_splits=5, shuffle=True, random_state=42)

    best_alpha = 1.0
    best_mae = float("inf")

    for alpha in alphas:
        model = Ridge(alpha=alpha)
        scores = cross_val_score(
            model, X, y,
            cv=kf,
            scoring="neg_mean_absolute_error"
        )
        mae = -scores.mean()
        print(f"  alpha={alpha:<6} -> MAE={mae:.3f} days")

        if mae < best_mae:
            best_mae = mae
            best_alpha = alpha

    # Retrain on full data with best alpha
    best_model = Ridge(alpha=best_alpha)
    best_model.fit(X, y)

    # Save — overwrites existing regression.pkl
    model_path = SAVED_MODELS_DIR / "regression.pkl"
    joblib.dump(best_model, model_path)
    print(f"\n  Saved optimized regression -> {model_path}")

    return {
        "best_alpha": best_alpha,
        "cv_mae":     round(best_mae, 3),
        "model":      best_model,
    }


def features_to_vector(features: dict) -> np.ndarray:
    """
    Converts a features dict (from feature_extraction.py) into the
    6-column numpy array regression.py expects.
    Handles None values with defaults — same logic as predict_next_cycle_length.
    """
    return np.array([[
        features.get("avg_cycle_length")  or FEATURE_DEFAULTS["avg_cycle_length"],
        features.get("std_cycle_length")  or FEATURE_DEFAULTS["std_cycle_length"],
        features.get("avg_period_length") or FEATURE_DEFAULTS["avg_period_length"],
        features.get("avg_pain")          or FEATURE_DEFAULTS["avg_pain"],
        features.get("avg_stress")        or FEATURE_DEFAULTS["avg_stress"],
        features.get("avg_sleep")         or FEATURE_DEFAULTS["avg_sleep"],
    ]])


# ── LSTM accuracy evaluator ───────────────────────────────────────────────────

def evaluate_lstm_accuracy(lstm_model, scaler, cycle_sequences: list) -> dict:
    """
    Evaluates LSTM on held-out sequences (last item = true value).

    Args:
        lstm_model:      loaded Keras LSTM
        scaler:          fitted MinMaxScaler
        cycle_sequences: list of cycle length lists (min 4 items each)

    Returns:
        {"mae": float, "within_2_days": float, "within_3_days": float}
    """
    predictions = []
    actuals = []

    for seq in cycle_sequences:
        if len(seq) < 4:
            continue

        input_seq   = seq[:-1]
        actual      = seq[-1]
        scaled      = scaler.transform(np.array(input_seq).reshape(-1, 1))
        X           = scaled.reshape(1, len(input_seq), 1)
        pred_scaled = lstm_model.predict(X, verbose=0)
        pred        = scaler.inverse_transform(pred_scaled)[0][0]

        predictions.append(pred)
        actuals.append(actual)

    if not predictions:
        return {"mae": None, "within_2_days": None, "within_3_days": None}

    errors   = [abs(p - a) for p, a in zip(predictions, actuals)]
    mae      = round(np.mean(errors), 3)
    within_2 = round(sum(1 for e in errors if e <= 2) / len(errors), 3)
    within_3 = round(sum(1 for e in errors if e <= 3) / len(errors), 3)

    print(f"\n  LSTM Accuracy Report:")
    print(f"    MAE            : {mae} days")
    print(f"    Within 2 days  : {within_2 * 100:.1f}%")
    print(f"    Within 3 days  : {within_3 * 100:.1f}%")

    return {"mae": mae, "within_2_days": within_2, "within_3_days": within_3}


# ── Confidence score tuning ───────────────────────────────────────────────────

def compute_confidence(
    cycle_count:        int,
    lstm_conf:          float,
    reg_lstm_agreement: bool,
    std_cycle_length:   float,
) -> str:
    """
    Improved confidence scoring — factors in cycle count, LSTM confidence,
    model agreement, and cycle variance.

    Returns: "high" | "medium" | "low"
    """
    score = 0

    if cycle_count >= 6:   score += 3
    elif cycle_count >= 3: score += 2

    if lstm_conf >= 0.75:  score += 2
    elif lstm_conf >= 0.5: score += 1

    if reg_lstm_agreement: score += 1
    if std_cycle_length > 7: score -= 1

    if score >= 5:   return "high"
    elif score >= 3: return "medium"
    else:            return "low"


# ── Run optimization test (called from main.py test_day7) ────────────────────

def run_optimization_test():
    """
    Generates synthetic data with the same 6-feature structure as
    regression.py, runs Ridge CV, and saves the optimized model.
    """
    print("\n" + "=" * 55)
    print(" Day 7 - Model Optimization")
    print("=" * 55)

    # Same distribution as regression.py's _generate_synthetic_training_data
    np.random.seed(42)
    n = 200

    avg_cycle  = np.random.normal(28, 3, n).clip(21, 45)
    std_cycle  = np.random.uniform(0, 7, n)
    avg_period = np.random.normal(5, 1, n).clip(2, 9)
    avg_pain   = np.random.uniform(1, 8, n)
    avg_stress = np.random.uniform(1, 9, n)
    avg_sleep  = np.random.uniform(4, 9, n)

    # 6 features — matches regression.py column order exactly
    X = np.column_stack([avg_cycle, std_cycle, avg_period,
                         avg_pain, avg_stress, avg_sleep])

    # Same target formula as regression.py
    y = (
        avg_cycle
        + (avg_stress - 5) * 0.4
        - (avg_sleep  - 7) * 0.3
        + np.random.normal(0, 1.5, n)
    ).clip(21, 45)

    print("\nOptimizing regression (Ridge CV)...")
    result = optimize_regression(X, y)
    print(f"\n  Best alpha : {result['best_alpha']}")
    print(f"  CV MAE     : {result['cv_mae']} days")

    print("\nModel optimization complete\n")