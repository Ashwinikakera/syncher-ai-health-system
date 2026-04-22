"""
ml_service/preprocessing/encoding.py
String → numeric encoding.  Single source of truth for all categorical fields.
Rule 5 of API contract: ML ONLY converts — backend NEVER encodes.
"""

import logging
from typing import Any
from config import (
    MOOD_MAP, FLOW_MAP, STRESS_MAP, EXERCISE_MAP,
    WHITE_DISCHARGE_MAP, FOOD_MAP, HYDRATION_MAP, BINARY_MAP,
)

logger = logging.getLogger(__name__)

# ─── Known symptom columns (one-hot) ──────────────────────────────────────────
SYMPTOM_COLUMNS = ["cramps", "headache", "fatigue", "mood_swings", "nausea"]

# ─── Known condition columns (binary flags) ───────────────────────────────────
CONDITION_COLUMNS = ["pcos", "pcod", "uti", "thyroid"]


def _encode(value: Any, mapping: dict, field_name: str, default: int = 0) -> int:
    """Generic string-to-int encoder with fallback + warning."""
    if value is None:
        return default
    key = str(value).strip().lower()
    if key not in mapping:
        logger.warning("Unknown value '%s' for field '%s'. Using default %d.",
                       value, field_name, default)
        return default
    return mapping[key]


# ─── Individual field encoders ────────────────────────────────────────────────

def encode_mood(value: Any) -> int:
    return _encode(value, MOOD_MAP, "mood", default=1)


def encode_flow(value: Any) -> int:
    return _encode(value, FLOW_MAP, "flow", default=1)


def encode_stress(value: Any) -> int:
    return _encode(value, STRESS_MAP, "stress", default=0)


def encode_exercise(value: Any) -> int:
    return _encode(value, EXERCISE_MAP, "exercise", default=0)


def encode_white_discharge(value: Any) -> int:
    return _encode(value, WHITE_DISCHARGE_MAP, "white_discharge", default=0)


def encode_food(value: Any) -> int:
    return _encode(value, FOOD_MAP, "food", default=2)  # default: home


def encode_hydration(value: Any) -> int:
    return _encode(value, HYDRATION_MAP, "hydration", default=0)


def encode_binary(value: Any) -> int:
    """Encode yes/no binary field."""
    return _encode(value, BINARY_MAP, "binary", default=0)


# ─── One-hot symptom encoder ──────────────────────────────────────────────────

def encode_symptoms(symptom_list: list[str]) -> dict[str, int]:
    """
    Returns a dict of {has_cramps, has_headache, has_fatigue,
    has_mood_swings, has_nausea} with 0/1 values.
    """
    symptom_set = {s.strip().lower() for s in (symptom_list or [])}
    return {f"has_{col}": int(col in symptom_set) for col in SYMPTOM_COLUMNS}


# ─── Medical condition encoder ────────────────────────────────────────────────

def encode_medical_condition(condition_str: Any) -> dict[str, int]:
    """
    Accepts a single string like 'PCOS', 'PCOD', 'UTI', 'Thyroid', 'none'.
    Returns binary flags {has_pcos, has_pcod, has_uti, has_thyroid}.
    """
    val = str(condition_str or "").strip().lower()
    return {f"has_{col}": int(col in val) for col in CONDITION_COLUMNS}


# ─── Batch log encoding ───────────────────────────────────────────────────────

def encode_daily_log(cleaned_log: dict) -> dict:
    """
    Accepts a cleaned daily-log dict and returns all numeric fields.
    Open-text fields (medication_details, routine_details) are excluded —
    they go to health_engine (GenAI), not the ML model.
    """
    symptoms_encoded = encode_symptoms(cleaned_log.get("symptoms", []))
    return {
        "sleep":            cleaned_log.get("sleep", 0.0),
        "stress":           encode_stress(cleaned_log.get("stress")),
        "exercise":         encode_exercise(cleaned_log.get("exercise")),
        "food":             encode_food(cleaned_log.get("food")),
        "hydration":        encode_hydration(cleaned_log.get("hydration")),
        "white_discharge":  encode_white_discharge(cleaned_log.get("white_discharge")),
        "medication_taken": encode_binary(cleaned_log.get("medication")),
        "routine_changed":  encode_binary(cleaned_log.get("routine_change")),
        "symptom_count":    len(cleaned_log.get("symptoms", [])),
        **symptoms_encoded,
    }


def encode_cycle_log(cleaned_log: dict) -> dict:
    """
    Accepts a cleaned cycle-log dict and returns all numeric fields.
    """
    return {
        "pain":             cleaned_log.get("pain", 1),
        "mood":             encode_mood(cleaned_log.get("mood")),
        "flow":             encode_flow(cleaned_log.get("flow")),
        "sleep":            cleaned_log.get("sleep", 0.0),
        "stress":           encode_stress(cleaned_log.get("stress")),
        "exercise":         encode_exercise(cleaned_log.get("exercise")),
        "hydration":        encode_hydration(cleaned_log.get("hydration")),
        "medication_taken": encode_binary(cleaned_log.get("medication")),
    }