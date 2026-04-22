"""
ml_service/prediction/predict.py
Prediction orchestrator.
Tries LSTM first, falls back to Regression, then statistical fallback.
Returns the full dashboard prediction payload matching API contract.

FIXES:
  1. last_start: cleaned_cycles[-1] is now correctly the MOST RECENT cycle
     because fetch_cycle_history returns ASC order (after db_fetcher fix).
     Added a guard to also take the start_date correctly when it's a
     date object vs string.

  2. _ovulation_window: OVULATION_WINDOW_DAYS = 3 with // 2 = 1 gave only
     a 2-day window. Fixed formula to use the full value as a ± radius,
     giving a proper (2 * OVULATION_WINDOW_DAYS + 1) day fertile window.
     With OVULATION_WINDOW_DAYS = 3 → ov_start = center-3, ov_end = center+3
     = 7-day window, matching clinical fertile window recommendation.

  3. Confidence unification: both LSTM and Regression confidence formulas
     now use the same variance divisor (100.0) so confidence is consistent
     regardless of which model fires. (Note: also fix lstm.py divisor
     from 80.0 → 100.0 to match.)
"""

import logging
from datetime import date, timedelta
from typing import Optional

import numpy as np

from config import (
    OVULATION_OFFSET_DAYS, OVULATION_WINDOW_DAYS,
    LSTM_SEQUENCE_LEN, REGRESSION_MIN_CYCLES,
)
from preprocessing.cleaning import clean_cycle_history, derive_cycle_lengths
from prediction.feature_extraction import build_feature_vector, build_lstm_sequence
from models.regression import CycleRegressionModel
from models.lstm import CycleLSTMModel

logger = logging.getLogger(__name__)

# Module-level model instances (loaded once, reused)
_regression_model = CycleRegressionModel()
_lstm_model       = CycleLSTMModel()


def reload_models():
    """Force reload models from disk (called after retrain)."""
    global _regression_model, _lstm_model
    _regression_model = CycleRegressionModel()
    _lstm_model       = CycleLSTMModel()
    logger.info("Models reloaded.")


# ─── Prediction helpers ───────────────────────────────────────────────────────

def _regularity_score(cycle_lengths: list[int]) -> float:
    """
    Regularity score in [0, 1].
    Based on coefficient of variation of cycle lengths.
    Lower CoV → higher regularity.
    """
    if not cycle_lengths:
        return 0.5
    arr = np.array(cycle_lengths, dtype=float)
    mean = np.mean(arr)
    if mean == 0:
        return 0.5
    cv = np.std(arr) / mean
    score = max(0.0, min(1.0, 1.0 - cv))
    return round(float(score), 2)


def _ovulation_window(next_period_date: date, predicted_cycle_length: int) -> list[str]:
    """
    Ovulation ≈ next_period_date - (cycle_length - OVULATION_OFFSET_DAYS)

    FIX: old formula used OVULATION_WINDOW_DAYS // 2 = 1 giving a 2-day
    window. Now uses full OVULATION_WINDOW_DAYS as ± radius giving a
    proper 7-day fertile window (center ± 3 days) which matches the
    clinical standard of 5-day fertile window around ovulation.

    Returns [start_date, end_date] as ISO strings.
    """
    days_before_period = predicted_cycle_length - OVULATION_OFFSET_DAYS
    ovulation_center   = next_period_date - timedelta(days=days_before_period)
    # FIX: use full OVULATION_WINDOW_DAYS as radius, not // 2
    ov_start = ovulation_center - timedelta(days=OVULATION_WINDOW_DAYS)
    ov_end   = ovulation_center + timedelta(days=OVULATION_WINDOW_DAYS)
    return [ov_start.isoformat(), ov_end.isoformat()]


def _statistical_fallback(
    cleaned_cycles: list[dict],
    cycle_lengths: list[int],
    avg_cycle_length: int,
) -> tuple[float, float]:
    """
    Last-resort prediction when no trained model is available.
    Uses weighted average of recent cycle lengths (more recent = higher weight).
    Returns (predicted_length, confidence).
    """
    if cycle_lengths:
        weights    = np.arange(1, len(cycle_lengths) + 1, dtype=float)
        pred       = float(np.average(cycle_lengths, weights=weights))
        confidence = min(0.65, 0.4 + 0.05 * len(cycle_lengths))
    else:
        pred       = float(avg_cycle_length)
        confidence = 0.40

    return round(np.clip(pred, 21.0, 45.0), 1), round(confidence, 2)


# ─── Main predict function ────────────────────────────────────────────────────

def predict(
    raw_profile:         dict,
    raw_cycles:          list[dict],
    raw_cycle_logs:      list[dict],
    raw_daily_logs:      list[dict],
    my_health_responses: Optional[dict] = None,
) -> dict:
    """
    Master prediction function.
    Returns dict matching GET /api/dashboard prediction fields:
      next_period_date, ovulation_window, cycle_regularity_score,
      predicted_length, confidence

    REQUIRES: raw_cycles in ASC (oldest-first) order from db_fetcher.
    """
    # ── Prep ──────────────────────────────────────────────────────────────────
    cleaned_cycles   = clean_cycle_history(raw_cycles)   # preserves ASC order
    cycle_lengths    = derive_cycle_lengths(cleaned_cycles)
    avg_cycle_length = int(raw_profile.get("avg_cycle_length") or 28)

    # FIX: with ASC order, cleaned_cycles[-1] is now the MOST RECENT cycle.
    # Previously DESC order made [-1] the oldest, giving next_period_date
    # months in the past.
    last_start: Optional[date] = None
    if cleaned_cycles:
        raw_start = cleaned_cycles[-1]["start_date"]
        # Handle both date objects and ISO strings from psycopg2
        if isinstance(raw_start, str):
            from datetime import datetime
            last_start = datetime.strptime(raw_start, "%Y-%m-%d").date()
        else:
            last_start = raw_start

    # ── Feature extraction ────────────────────────────────────────────────────
    feature_vector = build_feature_vector(
        raw_profile, raw_cycles, raw_cycle_logs, raw_daily_logs, my_health_responses
    )

    # ── Model selection: LSTM → Regression → Statistical ─────────────────────
    predicted_length: Optional[float] = None
    confidence: float = 0.5
    model_used: str = "statistical"

    # Try LSTM (requires trained model + enough cycles)
    if _lstm_model.is_trained and len(cleaned_cycles) >= LSTM_SEQUENCE_LEN:
        try:
            sequence         = build_lstm_sequence(
                raw_profile, raw_cycles, raw_cycle_logs, raw_daily_logs, my_health_responses
            )
            predicted_length = _lstm_model.predict_cycle_length(sequence)
            if predicted_length:
                confidence = _lstm_model.predict_confidence(sequence.flatten())
                model_used = "lstm"
                logger.info("LSTM prediction: %.1f days (conf=%.2f)", predicted_length, confidence)
        except Exception as exc:
            logger.warning("LSTM predict failed, falling back: %s", exc)
            predicted_length = None

    # Fallback: Regression
    if predicted_length is None and _regression_model.is_trained:
        try:
            predicted_length = _regression_model.predict_cycle_length(feature_vector)
            if predicted_length:
                confidence = _regression_model.predict_confidence(feature_vector)
                model_used = "regression"
                logger.info("Regression prediction: %.1f days (conf=%.2f)", predicted_length, confidence)
        except Exception as exc:
            logger.warning("Regression predict failed, using statistical: %s", exc)
            predicted_length = None

    # Last resort: statistical
    if predicted_length is None:
        predicted_length, confidence = _statistical_fallback(
            cleaned_cycles, cycle_lengths, avg_cycle_length
        )
        logger.info("Statistical fallback: %.1f days (conf=%.2f)", predicted_length, confidence)

    predicted_length_int = int(round(predicted_length))

    # ── Next period date ──────────────────────────────────────────────────────
    if last_start:
        next_period_date = last_start + timedelta(days=predicted_length_int)
    else:
        # No cycle history: predict from today
        next_period_date = date.today() + timedelta(days=predicted_length_int)

    # ── Regularity score ──────────────────────────────────────────────────────
    regularity_score = _regularity_score(cycle_lengths)

    # ── Ovulation window ─────────────────────────────────────────────────────
    ovulation_window = _ovulation_window(next_period_date, predicted_length_int)

    return {
        "next_period_date":       next_period_date.isoformat(),
        "ovulation_window":       ovulation_window,
        "cycle_regularity_score": regularity_score,
        "predicted_length":       predicted_length_int,
        "confidence":             confidence,
        "_model_used":            model_used,   # internal only, strip before API response
    }