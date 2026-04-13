"""
ml_service/data/db_fetcher.py
Fetches all user-related data from Django's PostgreSQL database.
Dev3 reads only — never writes to DB (Django owns all writes).

FIXES:
  1. fetch_cycle_history: changed ORDER BY to ASC so cycles arrive
     oldest-first. predict.py and feature_extraction both rely on
     cleaned_cycles[-1] being the MOST RECENT cycle. DESC order
     made [-1] the OLDEST, producing next_period_date in the past.

  2. Table names corrected to match Django app structure visible in
     screenshot (auth_app folder, not user_app):
       user_app_userprofile    → auth_app_userprofile
       user_app_myhealthresponse → auth_app_myhealthresponse
"""

import logging
from typing import Optional
import psycopg2
import psycopg2.extras
from config import DJANGO_DB

logger = logging.getLogger(__name__)


def _get_connection():
    """Open a new psycopg2 connection to the Django DB."""
    return psycopg2.connect(
        host=DJANGO_DB["host"],
        port=DJANGO_DB["port"],
        dbname=DJANGO_DB["name"],
        user=DJANGO_DB["user"],
        password=DJANGO_DB["password"],
        cursor_factory=psycopg2.extras.RealDictCursor,
    )


def fetch_user_profile(user_id: int) -> Optional[dict]:
    """
    Returns age, weight, medical_condition, medical_notes, avg_cycle_length.
    Returns None if user not found.

    FIX: table renamed from user_app_userprofile → auth_app_userprofile
    """
    sql = """
        SELECT u.id, u.email, up.age, up.weight,
               up.medical_condition, up.medical_notes,
               up.avg_cycle_length
        FROM   auth_user u
        JOIN   auth_app_userprofile up ON up.user_id = u.id
        WHERE  u.id = %s
        LIMIT  1
    """
    try:
        with _get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (user_id,))
                row = cur.fetchone()
                return dict(row) if row else None
    except Exception as exc:
        logger.error("fetch_user_profile failed for user %s: %s", user_id, exc)
        return None


def fetch_cycle_history(user_id: int, limit: int = 6) -> list[dict]:
    """
    Returns the most recent `limit` completed cycles (start_date + end_date).

    FIX: ORDER BY changed from DESC → ASC.
    All downstream consumers (clean_cycle_history, derive_cycle_lengths,
    build_lstm_sequence) expect oldest-first order so that:
      - cleaned_cycles[-1]  = most recent cycle  (used for last_start in predict.py)
      - cycle_lengths list  = [oldest→newest]    (used for _pad, variance)
      - LSTM sequence steps = [oldest→newest]    (time-series order)
    """
    sql = """
        SELECT start_date, end_date
        FROM   cycle_app_cycle
        WHERE  user_id = %s
          AND  end_date IS NOT NULL
        ORDER  BY start_date ASC
        LIMIT  %s
    """
    try:
        with _get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (user_id, limit))
                return [dict(r) for r in cur.fetchall()]
    except Exception as exc:
        logger.error("fetch_cycle_history failed for user %s: %s", user_id, exc)
        return []


def fetch_recent_cycle_logs(user_id: int, limit: int = 10) -> list[dict]:
    """
    Returns recent cycle-day logs (pain, mood, flow, sleep, stress, exercise,
    medication, hydration) for the user.
    """
    sql = """
        SELECT date, pain, mood, flow, sleep, stress, exercise,
               medication, medication_details, hydration
        FROM   log_app_cyclelog
        WHERE  user_id = %s
        ORDER  BY date DESC
        LIMIT  %s
    """
    try:
        with _get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (user_id, limit))
                return [dict(r) for r in cur.fetchall()]
    except Exception as exc:
        logger.error("fetch_recent_cycle_logs failed for user %s: %s", user_id, exc)
        return []


def fetch_recent_daily_logs(user_id: int, limit: int = 10) -> list[dict]:
    """
    Returns recent non-cycle daily logs (sleep, stress, exercise, food,
    medication, routine_change, white_discharge, hydration, symptoms).
    """
    sql = """
        SELECT date, sleep, stress, exercise, food,
               medication, medication_details,
               routine_change, routine_details,
               white_discharge, hydration, symptoms
        FROM   log_app_dailylog
        WHERE  user_id = %s
        ORDER  BY date DESC
        LIMIT  %s
    """
    try:
        with _get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (user_id, limit))
                return [dict(r) for r in cur.fetchall()]
    except Exception as exc:
        logger.error("fetch_recent_daily_logs failed for user %s: %s", user_id, exc)
        return []


def fetch_my_health_responses(user_id: int) -> Optional[dict]:
    """
    Returns the latest My Health questionnaire responses for the user.

    FIX: table renamed from user_app_myhealthresponse → auth_app_myhealthresponse
    """
    sql = """
        SELECT q1, q2, q3, q4, q5, q6, q7, q8, q9, q10,
               score, risk_level, created_at
        FROM   auth_app_myhealthresponse
        WHERE  user_id = %s
        ORDER  BY created_at DESC
        LIMIT  1
    """
    try:
        with _get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (user_id,))
                row = cur.fetchone()
                return dict(row) if row else None
    except Exception as exc:
        logger.error("fetch_my_health_responses failed for user %s: %s", user_id, exc)
        return None


def fetch_prediction_feedback(user_id: int, limit: int = 5) -> list[dict]:
    """
    Returns past prediction feedback rows (predicted vs actual dates).
    Used by retrain pipeline.
    """
    sql = """
        SELECT predicted_date, actual_date, prediction_correct, created_at
        FROM   cycle_app_predictionfeedback
        WHERE  user_id = %s
        ORDER  BY created_at DESC
        LIMIT  %s
    """
    try:
        with _get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (user_id, limit))
                return [dict(r) for r in cur.fetchall()]
    except Exception as exc:
        logger.error("fetch_prediction_feedback failed for user %s: %s", user_id, exc)
        return []


def fetch_full_user_context(user_id: int) -> dict:
    """
    Convenience method — returns all data needed for health_engine and
    dashboard in a single call. Always returns a dict (empty sub-keys on error).
    """
    return {
        "profile":       fetch_user_profile(user_id)       or {},
        "cycle_history": fetch_cycle_history(user_id)      or [],
        "cycle_logs":    fetch_recent_cycle_logs(user_id)   or [],
        "daily_logs":    fetch_recent_daily_logs(user_id)   or [],
        "my_health":     fetch_my_health_responses(user_id) or {},
    }