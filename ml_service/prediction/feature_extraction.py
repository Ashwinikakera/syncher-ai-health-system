# ml_service/prediction/feature_extraction.py

import pandas as pd
import numpy as np
from ml_service.preprocessing.cleaning import clean_cycle_data, clean_daily_logs
from ml_service.preprocessing.encoding import encode_all


def extract_cycle_features(cycle_records: list[dict]) -> dict:
    """
    Takes raw cycle records, cleans them, and extracts
    statistical features needed by the ML model.

    Input (from Dev1's DB):
    [
        {"cycle_start_date": "2024-01-01", "cycle_length": 28, "period_length": 5},
        {"cycle_start_date": "2024-01-29", "cycle_length": 30, "period_length": 4},
        ...
    ]

    Returns a flat dict of features ready for the model.
    """
    df = clean_cycle_data(cycle_records)

    if df.empty or "cycle_length" not in df.columns:
        raise ValueError("Not enough cycle data to extract features.")

    lengths = df["cycle_length"].dropna()

    features = {
        # Core stats
        "avg_cycle_length":     round(lengths.mean(), 2),
        "std_cycle_length":     round(lengths.std(), 2) if len(lengths) > 1 else 0.0,
        "min_cycle_length":     int(lengths.min()),
        "max_cycle_length":     int(lengths.max()),
        "cycle_count":          len(lengths),

        # Variance-based irregularity
        "cycle_variance":       round(lengths.var(), 2) if len(lengths) > 1 else 0.0,
        "is_irregular":         bool(lengths.std() > 7) if len(lengths) > 1 else False,

        # Period length stats
        "avg_period_length":    round(df["period_length"].mean(), 2)
                                if "period_length" in df.columns else None,

        # Trend — is the cycle getting longer or shorter over time?
        "cycle_trend":          _compute_trend(lengths),

        # Last known cycle length (most recent) — used for next prediction
        "last_cycle_length":    int(lengths.iloc[-1]),
        "last_cycle_start":     str(df["cycle_start_date"].iloc[-1].date())
                                if "cycle_start_date" in df.columns else None,
    }

    return features


def extract_symptom_features(log_records: list[dict]) -> dict:
    """
    Takes raw daily log records and extracts symptom-level
    features for the ML model.

    Input:
    [
        {"date": "2024-01-05", "pain_level": 6, "mood": "sad",
         "flow": "heavy", "sleep_hours": 7, "stress_level": 5,
         "exercise_minutes": 30},
        ...
    ]
    """
    df = clean_daily_logs(log_records)
    df = encode_all(df)

    if df.empty:
        raise ValueError("No log data to extract features from.")

    features = {
        # Pain
        "avg_pain":             round(df["pain"].mean(), 2)
                                if "pain" in df.columns else None,
        "max_pain":             int(df["pain"].max())
                                if "pain" in df.columns else None,
        "high_pain_days":       int((df["pain"] >= 7).sum())
                                if "pain" in df.columns else 0,
 

        # Mood
        "avg_mood_encoded":     round(df["mood_encoded"].mean(), 2)
                                if "mood_encoded" in df.columns else None,
        "dominant_mood":        _dominant_mood(df),

        # Flow
        "avg_flow_encoded":     round(df["flow_encoded"].mean(), 2)
                                if "flow_encoded" in df.columns else None,

        # Sleep
        "avg_sleep":            round(df["sleep"].mean(), 2)
                                if "sleep" in df.columns else None,
        "poor_sleep_days":      int((df["sleep"] < 6).sum())
                                if "sleep" in df.columns else 0,

        # Stress
        "avg_stress":           round(df["stress"].mean(), 2)
                                if "stress" in df.columns else None,
        "high_stress_days":     int((df["stress"] >= 7).sum())
                                if "stress" in df.columns else 0,

        # Exercise
        "avg_exercise": round(df["exercise"].mean(), 2)
                                if "exercise" in df.columns else None,
    }

    return features


def build_model_input(cycle_records: list[dict], log_records: list[dict]) -> dict:
    """
    Master function — combines cycle features + symptom features
    into a single flat dict that gets passed to predict.py on Day 4.

    This is the main function Dev1 will call indirectly via the
    /api/dashboard endpoint.
    """
    cycle_features = extract_cycle_features(cycle_records)
    symptom_features = extract_symptom_features(log_records) if log_records else {}

    return {**cycle_features, **symptom_features}


# ── Helpers ──────────────────────────────────────────────────────────────────

def _compute_trend(lengths: pd.Series) -> str:
    """
    Returns 'increasing', 'decreasing', or 'stable'
    based on linear trend of cycle lengths over time.
    """
    if len(lengths) < 3:
        return "stable"

    x = np.arange(len(lengths))
    slope = np.polyfit(x, lengths.values, 1)[0]

    if slope > 0.5:
        return "increasing"
    elif slope < -0.5:
        return "decreasing"
    else:
        return "stable"


def _dominant_mood(df: pd.DataFrame) -> str:
    """Return the most frequently logged mood as a string."""
    if "mood" not in df.columns or df["mood"].empty:
        return "neutral"
    return df["mood"].mode()[0]