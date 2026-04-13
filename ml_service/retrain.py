"""
ml_service/retrain.py
Retraining pipeline. Called by Django Celery worker (Sprint 11)
or via POST /ml/retrain from main.py.
Rebuilds Regression and LSTM models from latest DB data.
"""

import logging
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
from datetime import date

from data.db_fetcher import (
    _get_connection,
    fetch_user_profile,
    fetch_cycle_history,
    fetch_recent_cycle_logs,
    fetch_recent_daily_logs,
    fetch_my_health_responses,
)
from prediction.feature_extraction import build_feature_vector, build_lstm_sequence
from preprocessing.cleaning import clean_cycle_history, derive_cycle_lengths
from models.regression import CycleRegressionModel
from models.lstm import CycleLSTMModel
from config import REGRESSION_MIN_CYCLES, LSTM_SEQUENCE_LEN

logger = logging.getLogger(__name__)


def _fetch_all_user_ids() -> list[int]:
    """Fetch all user IDs that have at least 2 completed cycles."""
    sql = """
        SELECT DISTINCT user_id
        FROM   cycle_app_cycle
        WHERE  end_date IS NOT NULL
        GROUP  BY user_id
        HAVING COUNT(*) >= %s
    """
    try:
        with _get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (REGRESSION_MIN_CYCLES,))
                return [row["user_id"] for row in cur.fetchall()]
    except Exception as exc:
        logger.error("Could not fetch user IDs for retrain: %s", exc)
        return []


def _build_regression_dataset(user_ids: list[int]) -> tuple[np.ndarray, np.ndarray]:
    """
    For each user, build (feature_vector, next_cycle_length) pairs.
    Each user can contribute multiple samples (one per completed cycle gap).
    """
    X_list, y_list = [], []

    for uid in user_ids:
        try:
            profile     = fetch_user_profile(uid)     or {}
            cycles      = fetch_cycle_history(uid, limit=10)
            cycle_logs  = fetch_recent_cycle_logs(uid)
            daily_logs  = fetch_recent_daily_logs(uid)
            mh_resp     = fetch_my_health_responses(uid)

            cleaned   = clean_cycle_history(cycles)
            cl_values = derive_cycle_lengths(cleaned)  # n-1 values

            # Each pair: use cycles[0..i] as input → predict cl_values[i]
            for i, target_length in enumerate(cl_values):
                subset_cycles = cleaned[: i + 1]
                fv = build_feature_vector(
                    profile,
                    [{"start_date": c["start_date"], "end_date": c["end_date"]}
                     for c in subset_cycles],
                    cycle_logs,
                    daily_logs,
                    mh_resp,
                )
                X_list.append(fv)
                y_list.append(float(target_length))

        except Exception as exc:
            logger.warning("Skipping user %d in regression dataset: %s", uid, exc)
            continue

    if not X_list:
        return np.array([]), np.array([])

    return np.stack(X_list), np.array(y_list)


def _build_lstm_dataset(user_ids: list[int]) -> tuple[np.ndarray, np.ndarray]:
    """
    For each user, build LSTM (sequence, next_cycle_length) pairs.
    Requires at least LSTM_SEQUENCE_LEN + 1 cycles per user.
    """
    X_list, y_list = [], []

    for uid in user_ids:
        try:
            profile     = fetch_user_profile(uid)     or {}
            cycles      = fetch_cycle_history(uid, limit=10)
            cycle_logs  = fetch_recent_cycle_logs(uid)
            daily_logs  = fetch_recent_daily_logs(uid)
            mh_resp     = fetch_my_health_responses(uid)

            cleaned   = clean_cycle_history(cycles)
            cl_values = derive_cycle_lengths(cleaned)

            if len(cleaned) < LSTM_SEQUENCE_LEN + 1:
                continue

            for i in range(LSTM_SEQUENCE_LEN, len(cl_values) + 1):
                subset_cycles = cleaned[:i]
                seq = build_lstm_sequence(
                    profile,
                    [{"start_date": c["start_date"], "end_date": c["end_date"]}
                     for c in subset_cycles],
                    cycle_logs,
                    daily_logs,
                    mh_resp,
                )
                target = float(cl_values[i - 1])
                X_list.append(seq[0])   # remove batch dim
                y_list.append(target)

        except Exception as exc:
            logger.warning("Skipping user %d in LSTM dataset: %s", uid, exc)
            continue

    if not X_list:
        return np.array([]), np.array([])

    return np.stack(X_list), np.array(y_list)


def run_retrain() -> dict:
    """
    Full retraining run.
    Returns summary dict with training metrics.
    """
    logger.info("=== Starting SYNCHER ML Retrain ===")
    user_ids = _fetch_all_user_ids()

    if not user_ids:
        logger.warning("No eligible users found for retraining.")
        return {"status": "skipped", "reason": "no eligible users"}

    logger.info("Found %d eligible users.", len(user_ids))
    results = {}

    # ── Regression ────────────────────────────────────────────────────────────
    X_reg, y_reg = _build_regression_dataset(user_ids)
    if len(X_reg) >= REGRESSION_MIN_CYCLES:
        try:
            reg_model = CycleRegressionModel()
            metrics   = reg_model.train(X_reg, y_reg)
            results["regression"] = metrics
            logger.info("Regression retrained. MAE=%.2f", metrics.get("mae", -1))
        except Exception as exc:
            logger.error("Regression retrain failed: %s", exc)
            results["regression"] = {"error": str(exc)}
    else:
        logger.warning("Not enough regression samples (%d). Skipping.", len(X_reg))
        results["regression"] = {"skipped": True, "samples": len(X_reg)}

    # ── LSTM ──────────────────────────────────────────────────────────────────
    X_lstm, y_lstm = _build_lstm_dataset(user_ids)
    if len(X_lstm) >= 5:
        try:
            lstm_model = CycleLSTMModel()
            metrics    = lstm_model.train(X_lstm, y_lstm)
            results["lstm"] = metrics
            logger.info("LSTM retrained. MAE=%.2f", metrics.get("mae", -1))
        except Exception as exc:
            logger.error("LSTM retrain failed: %s", exc)
            results["lstm"] = {"error": str(exc)}
    else:
        logger.warning("Not enough LSTM samples (%d). Skipping.", len(X_lstm))
        results["lstm"] = {"skipped": True, "samples": len(X_lstm)}

    logger.info("=== Retrain complete: %s ===", results)

    # Log to retrain_log.txt
    _write_retrain_log(results, len(user_ids))

    return results


def _write_retrain_log(results: dict, user_count: int):
    """Append a retrain summary line to retrain_log.txt."""
    log_path = os.path.join(os.path.dirname(__file__), "retrain_log.txt")
    try:
        from datetime import datetime
        timestamp = datetime.utcnow().isoformat()
        line = (
            f"{timestamp} | users={user_count} | "
            f"reg_mae={results.get('regression', {}).get('mae', 'N/A')} | "
            f"lstm_mae={results.get('lstm', {}).get('mae', 'N/A')}\n"
        )
        with open(log_path, "a") as f:
            f.write(line)
    except Exception as exc:
        logger.warning("Could not write retrain log: %s", exc)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_retrain()