# ml_service/preprocessing/cleaning.py

import pandas as pd
import numpy as np


def clean_cycle_data(records: list[dict]) -> pd.DataFrame:
    if not records:
        raise ValueError("No cycle records provided.")

    df = pd.DataFrame(records)

    # ── Normalize field names to internal standard ────────────────
    # Contract uses start_date/end_date, internally we use cycle_start_date/end_date
    if "start_date" in df.columns and "cycle_start_date" not in df.columns:
        df.rename(columns={"start_date": "cycle_start_date"}, inplace=True)
    if "end_date" in df.columns and "cycle_end_date" not in df.columns:
        df.rename(columns={"end_date": "cycle_end_date"}, inplace=True)

    # ── Parse dates ───────────────────────────────────────────────
    if "cycle_start_date" in df.columns:
        df["cycle_start_date"] = pd.to_datetime(df["cycle_start_date"], errors="coerce")
    if "cycle_end_date" in df.columns:
        df["cycle_end_date"] = pd.to_datetime(df["cycle_end_date"], errors="coerce")

    # ── Fill missing cycle_length from dates ──────────────────────
    if "cycle_length" in df.columns:
        missing_mask = df["cycle_length"].isna()
        if "cycle_start_date" in df.columns and "cycle_end_date" in df.columns:
            calculated = (df["cycle_end_date"] - df["cycle_start_date"]).dt.days
            df.loc[missing_mask, "cycle_length"] = calculated[missing_mask]

    # ── Fill remaining missing values ─────────────────────────────
    if "cycle_length" in df.columns:
        df["cycle_length"] = df["cycle_length"].fillna(round(df["cycle_length"].mean()))
    if "period_length" in df.columns:
        df["period_length"] = df["period_length"].fillna(round(df["period_length"].mean()))

    # ── Remove impossible values ──────────────────────────────────
    if "cycle_length" in df.columns:
        df = df[df["cycle_length"].between(15, 60)]
    if "period_length" in df.columns:
        df = df[df["period_length"].between(1, 15)]

    # ── Normalize cycle_length ────────────────────────────────────
    if "cycle_length" in df.columns and len(df) > 1:
        min_c = df["cycle_length"].min()
        max_c = df["cycle_length"].max()
        df["cycle_length_normalized"] = (
            ((df["cycle_length"] - min_c) / (max_c - min_c))
            if max_c != min_c else 0.5
        )

    # Compute cycle variance (used for irregularity score)
    if "cycle_length" in df.columns:
        df["cycle_variance"] = df["cycle_length"].std()

    df = df.reset_index(drop=True)
    return df


def clean_daily_logs(logs: list[dict]) -> pd.DataFrame:
    if not logs:
        raise ValueError("No daily logs provided.")

    df = pd.DataFrame(logs)

    # ── Convert string stress → numeric ──────────────────────────
    # Contract sends: "low" | "medium" | "high"
    STRESS_ENCODING = {"low": 2, "medium": 5, "high": 8}
    if "stress" in df.columns:
        df["stress"] = df["stress"].apply(
            lambda x: STRESS_ENCODING.get(str(x).lower(), x)
            if isinstance(x, str) else x
        )

    # ── Convert string exercise → numeric (minutes) ───────────────
    # Contract sends: "none" | "light" | "moderate" | "heavy"
    EXERCISE_ENCODING = {"none": 0, "light": 20, "moderate": 45, "heavy": 75}
    if "exercise" in df.columns:
        df["exercise"] = df["exercise"].apply(
            lambda x: EXERCISE_ENCODING.get(str(x).lower(), x)
            if isinstance(x, str) else x
        )

    # ── Parse date ────────────────────────────────────────────────
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"])

    # ── Fill numeric fields with median ──────────────────────────
    numeric_fields = ["pain", "sleep", "stress", "exercise"]
    for field in numeric_fields:
        if field in df.columns:
            df[field] = pd.to_numeric(df[field], errors="coerce")
            df[field] = df[field].fillna(df[field].median())

    # ── Clamp ranges ──────────────────────────────────────────────
    if "pain"   in df.columns: df["pain"]   = df["pain"].clip(0, 10)
    if "stress" in df.columns: df["stress"] = df["stress"].clip(0, 10)
    if "sleep"  in df.columns: df["sleep"]  = df["sleep"].clip(0, 24)

    # ── Fill missing mood/flow ────────────────────────────────────
    # Contract mood values: "low" | "medium" | "high" | "happy" | "sad" etc.
    for col in ["mood", "flow"]:
        if col in df.columns:
            most_common = df[col].mode()
            df[col] = df[col].fillna(
                most_common[0] if not most_common.empty
                else ("neutral" if col == "mood" else "light")
            )

    df = df.reset_index(drop=True)
    return df