# ml_service/data/db_fetcher.py
# Fetches real user data from Dev1's Django REST API
# Called by: training pipeline, retrain trigger, predict()

import requests
from ml_service.config import DJANGO_API_BASE_URL, DJANGO_INTERNAL_TOKEN


HEADERS = {
    "Authorization": f"Token {DJANGO_INTERNAL_TOKEN}",
    "Content-Type": "application/json",
}


# ── Fetch functions ───────────────────────────────────────────────────────────

def fetch_cycle_records(user_id: int) -> list[dict]:
    """
    Fetches cycle records for a specific user from Dev1's API.
    Maps Django field names → ML service field names.

    Returns:
        [{"start_date": "2024-01-01", "cycle_length": 28}, ...]
    """
    try:
        response = requests.get(
            f"{DJANGO_API_BASE_URL}/api/cycle/",
            headers=HEADERS,
            params={"user_id": user_id},
            timeout=5,
        )
        response.raise_for_status()
        raw = response.json()

        # Normalize field names to what ML service expects
        return [
            {
                "start_date":   r.get("cycle_start_date") or r.get("start_date"),
                "cycle_length": r.get("cycle_length"),
            }
            for r in raw
            if r.get("cycle_length")  # skip incomplete records
        ]

    except requests.RequestException as e:
        print(f"  [db_fetcher] Could not fetch cycle records: {e}")
        return []


def fetch_daily_logs(user_id: int) -> list[dict]:
    """
    Fetches daily log records for a specific user.

    Returns:
        [{"date": "2024-01-05", "pain": 6, "mood": "low",
          "flow": "heavy", "sleep": 7, "stress": "medium",
          "exercise": "light"}, ...]
    """
    try:
        response = requests.get(
            f"{DJANGO_API_BASE_URL}/api/daily-log/",
            headers=HEADERS,
            params={"user_id": user_id},
            timeout=5,
        )
        response.raise_for_status()
        return response.json()

    except requests.RequestException as e:
        print(f"  [db_fetcher] Could not fetch daily logs: {e}")
        return []


def fetch_all_users_training_data() -> list[dict]:
    """
    Fetches training data across ALL users for model retraining.
    Each record = one completed cycle with symptom averages.

    Returns:
        [
            {
                "avg_cycle_length":   28.5,
                "std_cycle_length":   2.1,
                "avg_period_length":  5.0,
                "avg_pain":           4.2,
                "avg_stress":         3.8,
                "avg_sleep":          7.1,
                "actual_next_length": 29,   ← ground truth
            },
            ...
        ]
    """
    try:
        response = requests.get(
            f"{DJANGO_API_BASE_URL}/api/ml/training-data/",
            headers=HEADERS,
            timeout=10,
        )
        response.raise_for_status()
        raw = response.json()

        # Filter out records missing the label
        return [r for r in raw if r.get("actual_next_length")]

    except requests.RequestException as e:
        print(f"  [db_fetcher] Could not fetch training data: {e}")
        return []


def fetch_user_data_for_predict(user_id: int) -> dict:
    """
    Master function — builds the full user_data dict that predict() expects.
    Called by Dev1's dashboard_app/services.py indirectly.

    Returns:
        {
            "cycle_records": [...],
            "log_records":   [...],
        }
    """
    return {
        "cycle_records": fetch_cycle_records(user_id),
        "log_records":   fetch_daily_logs(user_id),
    }


# ── Data sufficiency check ────────────────────────────────────────────────────

def has_enough_data(user_id: int) -> dict:
    """
    Quick check before running predict() — tells caller if user has
    enough data for a reliable prediction.

    Returns:
        {
            "can_predict":    bool,
            "cycle_count":    int,
            "log_count":      int,
            "reason":         str,
        }
    """
    cycles = fetch_cycle_records(user_id)
    logs   = fetch_daily_logs(user_id)

    if len(cycles) < 2:
        return {
            "can_predict": False,
            "cycle_count": len(cycles),
            "log_count":   len(logs),
            "reason": "Need at least 2 cycle records for a basic prediction.",
        }

    return {
        "can_predict": True,
        "cycle_count": len(cycles),
        "log_count":   len(logs),
        "reason": "Sufficient data available.",
    }