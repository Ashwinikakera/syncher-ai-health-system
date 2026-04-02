# ml_service/preprocessing/encoding.py

import pandas as pd
from ml_service.config import MOOD_ENCODING, FLOW_ENCODING


def encode_mood(df: pd.DataFrame) -> pd.DataFrame:
    """Convert mood text column to numeric values."""
    if "mood" not in df.columns:
        return df

    df["mood_encoded"] = (
        df["mood"]
        .str.lower()
        .str.strip()
        .map(MOOD_ENCODING)
        .fillna(2)           # default → "neutral" = 2
        .astype(int)
    )
    return df


def encode_flow(df: pd.DataFrame) -> pd.DataFrame:
    """Convert flow text column to numeric values."""
    if "flow" not in df.columns:
        return df

    df["flow_encoded"] = (
        df["flow"]
        .str.lower()
        .str.strip()
        .map(FLOW_ENCODING)
        .fillna(1)           # default → "light" = 1
        .astype(int)
    )
    return df


def encode_all(df: pd.DataFrame) -> pd.DataFrame:
    """Run all encoders in one call."""
    df = encode_mood(df)
    df = encode_flow(df)
    return df


def get_feature_vector(daily_log_df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns only numeric columns the ML model needs.
    Handles both contract field names and internal names.
    """
    df = encode_all(daily_log_df)

    # Try both contract names and internal names
    feature_cols = [
        col for col in [
            "pain",           # contract name (was pain_level)
            "mood_encoded",
            "flow_encoded",
            "sleep",          # contract name (was sleep_hours)
            "stress",         # contract name (was stress_level)
            "exercise",       # contract name (was exercise_minutes)
        ]
        if col in df.columns
    ]

    return df[feature_cols]