"""
ml_service/preprocessing/cleaning.py
Raw data cleaning: null handling, type coercion, date parsing.
"""

import logging
from datetime import date, datetime, timedelta
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _parse_date(value: Any) -> Optional[date]:
    """Safely parse a date string (YYYY-MM-DD) or date object."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except (ValueError, TypeError):
        logger.warning("Could not parse date: %s", value)
        return None


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_str_lower(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip().lower()


# ─── Cycle history cleaning ───────────────────────────────────────────────────

def clean_cycle_history(raw_cycles: list[dict]) -> list[dict]:
    """
    Accepts raw cycle dicts with start_date / end_date.
    Returns list of cleaned dicts with:
      - start_date (date)
      - end_date   (date | None)
      - period_duration (int days, 0 if end unknown)
    Only cycles with valid start_date are kept.
    """
    cleaned = []
    for cycle in raw_cycles:
        start = _parse_date(cycle.get("start_date"))
        if start is None:
            continue
        end = _parse_date(cycle.get("end_date"))
        duration = (end - start).days if end and end > start else 0
        cleaned.append({
            "start_date":      start,
            "end_date":        end,
            "period_duration": max(0, min(duration, 14)),  # cap at 14 days
        })
    # Sort ascending so index 0 = oldest
    cleaned.sort(key=lambda x: x["start_date"])
    return cleaned


def derive_cycle_lengths(cleaned_cycles: list[dict]) -> list[int]:
    """
    Given a sorted list of cleaned cycles, compute gap between
    consecutive start_dates (= cycle length in days).
    Returns list of cycle lengths (length = n_cycles - 1).
    """
    lengths = []
    for i in range(1, len(cleaned_cycles)):
        gap = (cleaned_cycles[i]["start_date"] - cleaned_cycles[i - 1]["start_date"]).days
        if 15 <= gap <= 60:   # physiologically valid range
            lengths.append(gap)
    return lengths


# ─── Log cleaning ─────────────────────────────────────────────────────────────

def clean_daily_log(raw: dict) -> dict:
    """Coerce and sanitise a single daily-log row."""
    return {
        "date":             _parse_date(raw.get("date")),
        "sleep":            max(0.0, min(_safe_float(raw.get("sleep"), 0.0), 24.0)),
        "stress":           _safe_str_lower(raw.get("stress"),          "none"),
        "exercise":         _safe_str_lower(raw.get("exercise"),        "none"),
        "food":             _safe_str_lower(raw.get("food"),            "home"),
        "medication":       _safe_str_lower(raw.get("medication"),      "no"),
        "medication_details": str(raw.get("medication_details") or ""),
        "routine_change":   _safe_str_lower(raw.get("routine_change"),  "no"),
        "routine_details":  str(raw.get("routine_details") or ""),
        "white_discharge":  _safe_str_lower(raw.get("white_discharge"), "none"),
        "hydration":        _safe_str_lower(raw.get("hydration"),       "no"),
        "symptoms":         _clean_symptoms(raw.get("symptoms")),
    }


def clean_cycle_log(raw: dict) -> dict:
    """Coerce and sanitise a single cycle-log row."""
    return {
        "date":              _parse_date(raw.get("date")),
        "pain":              max(1, min(_safe_int(raw.get("pain"), 1), 5)),
        "mood":              _safe_str_lower(raw.get("mood"),      "low"),
        "flow":              _safe_str_lower(raw.get("flow"),      "light"),
        "sleep":             max(0.0, min(_safe_float(raw.get("sleep"), 0.0), 24.0)),
        "stress":            _safe_str_lower(raw.get("stress"),    "none"),
        "exercise":          _safe_str_lower(raw.get("exercise"),  "none"),
        "medication":        _safe_str_lower(raw.get("medication"), "no"),
        "medication_details": str(raw.get("medication_details") or ""),
        "hydration":         _safe_str_lower(raw.get("hydration"), "no"),
    }


def _clean_symptoms(raw_symptoms: Any) -> list[str]:
    """Normalise symptoms field — can be a list or comma-string."""
    valid = {"cramps", "headache", "fatigue", "mood_swings", "nausea"}
    if isinstance(raw_symptoms, list):
        return [s.strip().lower() for s in raw_symptoms if s.strip().lower() in valid]
    if isinstance(raw_symptoms, str) and raw_symptoms:
        return [s.strip().lower() for s in raw_symptoms.split(",")
                if s.strip().lower() in valid]
    return []


# ─── Profile cleaning ─────────────────────────────────────────────────────────

def clean_profile(raw: dict) -> dict:
    """Sanitise user profile fields."""
    age    = max(10, min(_safe_int(raw.get("age"), 25),    60))
    weight = max(30.0, min(_safe_float(raw.get("weight"), 55.0), 200.0))
    avg_cl = max(21, min(_safe_int(raw.get("avg_cycle_length"), 28), 45))

    condition = _safe_str_lower(raw.get("medical_condition"), "none")
    notes     = str(raw.get("medical_notes") or "")

    return {
        "age":              age,
        "weight":           weight,
        "avg_cycle_length": avg_cl,
        "medical_condition": condition,
        "medical_notes":    notes,
    }