"""
ml_service/prediction/feature_extraction.py
Builds the 32-feature numpy vector used by both Regression and LSTM models.
Feature order must match config.FEATURE_COLUMNS exactly.

FIXES:
  1. cycle_variance: was computed on the padded list (including artificial
     pad values), inflating variance when fewer than 3 real cycles exist.
     Now computed only on the REAL cycle lengths before padding.

  2. build_lstm_sequence: the loop iterated over cleaned_cycles[-seq_len:]
     using index i with subset_cycles = cleaned_cycles[:i+1]. With cycles
     now correctly in ASC order (oldest first, after db_fetcher fix), this
     correctly builds step 0 = oldest context, step 2 = newest context.
     Added explicit comment to document expected ASC ordering dependency.
"""

import logging
import numpy as np
from typing import Optional

from config import FEATURE_COLUMNS, LSTM_SEQUENCE_LEN
from preprocessing.cleaning import (
    clean_profile, clean_cycle_history, derive_cycle_lengths,
    clean_daily_log, clean_cycle_log,
)
from preprocessing.encoding import (
    encode_daily_log, encode_cycle_log, encode_medical_condition,
)
from prediction.my_health_scorer import compute_my_health_score

logger = logging.getLogger(__name__)


# ─── Aggregation helpers ──────────────────────────────────────────────────────

def _avg(values: list, default: float = 0.0) -> float:
    return float(np.mean(values)) if values else default


def _pad(lst: list, length: int, pad_value=0) -> list:
    """Pad or truncate list to exact length from the right."""
    return (lst + [pad_value] * length)[:length]


# ─── Main feature builder ─────────────────────────────────────────────────────

def build_feature_vector(
    raw_profile:     dict,
    raw_cycles:      list[dict],
    raw_cycle_logs:  list[dict],
    raw_daily_logs:  list[dict],
    my_health_responses: Optional[dict] = None,
) -> np.ndarray:
    """
    Returns a 1D numpy array of shape (len(FEATURE_COLUMNS),) = (32,).

    Parameters
    ----------
    raw_profile          : dict from db_fetcher.fetch_user_profile()
    raw_cycles           : list of dicts from db_fetcher.fetch_cycle_history()
                           MUST be in ASC (oldest-first) order.
    raw_cycle_logs       : list of dicts from db_fetcher.fetch_recent_cycle_logs()
    raw_daily_logs       : list of dicts from db_fetcher.fetch_recent_daily_logs()
    my_health_responses  : dict from db_fetcher.fetch_my_health_responses() or None
    """

    # ── 1. Profile ─────────────────────────────────────────────────────────────
    profile = clean_profile(raw_profile)
    age              = float(profile["age"])
    weight           = float(profile["weight"])
    avg_cycle_length = float(profile["avg_cycle_length"])
    condition_flags  = encode_medical_condition(profile["medical_condition"])

    # ── 2. Cycle history → lengths & durations ────────────────────────────────
    # raw_cycles is ASC (oldest first). cleaned_cycles[-1] = most recent.
    cleaned_cycles   = clean_cycle_history(raw_cycles)
    cycle_lengths    = derive_cycle_lengths(cleaned_cycles)   # gap between starts
    period_durations = [c["period_duration"] for c in cleaned_cycles]

    # FIX: compute variance on REAL cycle lengths only, before padding.
    # Old code computed np.var on cl_padded which included artificial pad
    # values (avg_cycle_length), inflating variance when <3 real cycles exist.
    real_lengths_for_var = cycle_lengths[-3:] if cycle_lengths else []
    if len(real_lengths_for_var) > 1:
        cycle_variance = float(np.var(real_lengths_for_var))
    else:
        cycle_variance = 0.0

    # Pad / truncate to 3 most-recent values (newest last = index 2)
    cl_padded  = _pad(cycle_lengths[-3:],    3, pad_value=int(avg_cycle_length))
    pd_padded  = _pad(period_durations[-3:], 3, pad_value=5)

    cycle_length_1, cycle_length_2, cycle_length_3 = cl_padded
    period_dur_1,   period_dur_2,   period_dur_3   = pd_padded

    # ── 3. Aggregate recent cycle-log data (pain, mood, flow, etc.) ───────────
    encoded_cycle_logs = [encode_cycle_log(clean_cycle_log(r)) for r in raw_cycle_logs]

    if encoded_cycle_logs:
        pain         = _avg([r["pain"]            for r in encoded_cycle_logs])
        flow         = _avg([r["flow"]            for r in encoded_cycle_logs])
        mood         = _avg([r["mood"]            for r in encoded_cycle_logs])
        cl_sleep     = _avg([r["sleep"]           for r in encoded_cycle_logs])
        cl_stress    = _avg([r["stress"]          for r in encoded_cycle_logs])
        cl_exercise  = _avg([r["exercise"]        for r in encoded_cycle_logs])
        cl_hydration = _avg([r["hydration"]       for r in encoded_cycle_logs])
        cl_medication = _avg([r["medication_taken"] for r in encoded_cycle_logs])
    else:
        pain = flow = mood = cl_sleep = cl_stress = cl_exercise = 0.0
        cl_hydration = cl_medication = 0.0

    # ── 4. Aggregate recent daily-log data ────────────────────────────────────
    encoded_daily_logs = [encode_daily_log(clean_daily_log(r)) for r in raw_daily_logs]

    if encoded_daily_logs:
        sleep            = _avg([r["sleep"]           for r in encoded_daily_logs])
        stress           = _avg([r["stress"]          for r in encoded_daily_logs])
        exercise         = _avg([r["exercise"]        for r in encoded_daily_logs])
        food             = _avg([r["food"]            for r in encoded_daily_logs])
        hydration        = _avg([r["hydration"]       for r in encoded_daily_logs])
        white_discharge  = _avg([r["white_discharge"] for r in encoded_daily_logs])
        medication_taken = _avg([r["medication_taken"] for r in encoded_daily_logs])
        routine_changed  = _avg([r["routine_changed"]  for r in encoded_daily_logs])
        symptom_count    = _avg([r["symptom_count"]    for r in encoded_daily_logs])

        # One-hot symptoms: average across logs → threshold at 0.3
        has_cramps      = int(_avg([r["has_cramps"]      for r in encoded_daily_logs]) >= 0.3)
        has_headache    = int(_avg([r["has_headache"]    for r in encoded_daily_logs]) >= 0.3)
        has_fatigue     = int(_avg([r["has_fatigue"]     for r in encoded_daily_logs]) >= 0.3)
        has_mood_swings = int(_avg([r["has_mood_swings"] for r in encoded_daily_logs]) >= 0.3)
        has_nausea      = int(_avg([r["has_nausea"]      for r in encoded_daily_logs]) >= 0.3)
    else:
        # Fall back to cycle-log aggregates where available
        sleep = cl_sleep; stress = cl_stress; exercise = cl_exercise
        food = 2.0; hydration = cl_hydration; white_discharge = 0.0
        medication_taken = cl_medication; routine_changed = 0.0; symptom_count = 0.0
        has_cramps = has_headache = has_fatigue = has_mood_swings = has_nausea = 0

    # ── 5. My Health score ────────────────────────────────────────────────────
    if my_health_responses:
        mh_result       = compute_my_health_score(my_health_responses)
        my_health_score = float(mh_result["score"])
    else:
        my_health_score = 0.0

    # ── 6. Assemble vector (order must match FEATURE_COLUMNS) ─────────────────
    feature_dict = {
        "age":               age,
        "weight":            weight,
        "avg_cycle_length":  avg_cycle_length,
        "cycle_length_1":    float(cycle_length_1),
        "cycle_length_2":    float(cycle_length_2),
        "cycle_length_3":    float(cycle_length_3),
        "period_duration_1": float(period_dur_1),
        "period_duration_2": float(period_dur_2),
        "period_duration_3": float(period_dur_3),
        "cycle_variance":    cycle_variance,
        "pain":              pain,
        "flow":              flow,
        "mood":              mood,
        "sleep":             sleep,
        "stress":            stress,
        "exercise":          exercise,
        "food":              food,
        "hydration":         hydration,
        "white_discharge":   white_discharge,
        "medication_taken":  medication_taken,
        "routine_changed":   routine_changed,
        "symptom_count":     symptom_count,
        "has_cramps":        float(has_cramps),
        "has_headache":      float(has_headache),
        "has_fatigue":       float(has_fatigue),
        "has_mood_swings":   float(has_mood_swings),
        "has_nausea":        float(has_nausea),
        "has_pcos":          float(condition_flags["has_pcos"]),
        "has_pcod":          float(condition_flags["has_pcod"]),
        "has_uti":           float(condition_flags["has_uti"]),
        "has_thyroid":       float(condition_flags["has_thyroid"]),
        "my_health_score":   my_health_score,
    }

    # Validate all columns present
    missing = [col for col in FEATURE_COLUMNS if col not in feature_dict]
    if missing:
        logger.error("Missing feature columns: %s", missing)
        raise ValueError(f"Feature extraction incomplete. Missing: {missing}")

    vector = np.array([feature_dict[col] for col in FEATURE_COLUMNS], dtype=np.float32)
    logger.debug("Feature vector built: shape=%s, values=%s", vector.shape, vector)
    return vector


# ─── LSTM sequence builder ────────────────────────────────────────────────────

def build_lstm_sequence(
    raw_profile:         dict,
    raw_cycles:          list[dict],
    raw_cycle_logs:      list[dict],
    raw_daily_logs:      list[dict],
    my_health_responses: Optional[dict] = None,
) -> np.ndarray:
    """
    Builds a (1, LSTM_SEQUENCE_LEN, n_features) array for the LSTM model.
    Each step = one cycle's aggregated feature vector, oldest → newest.

    REQUIRES: raw_cycles in ASC (oldest-first) order — guaranteed by
    db_fetcher.fetch_cycle_history() after the ORDER BY ASC fix.

    Step 0 = context up to oldest available cycle
    Step 1 = context up to second cycle
    Step 2 = context up to most recent cycle  ← what model predicts FROM

    If fewer than SEQUENCE_LEN cycles exist, earlier steps are zero-padded.
    Returns shape: (1, LSTM_SEQUENCE_LEN, n_features)
    """
    n_features     = len(FEATURE_COLUMNS)
    seq_len        = LSTM_SEQUENCE_LEN
    cleaned_cycles = clean_cycle_history(raw_cycles)  # ASC order preserved

    # Build one feature vector per available cycle (up to seq_len)
    # cleaned_cycles is oldest-first, so cleaned_cycles[-seq_len:] gives
    # the last `seq_len` cycles in chronological order.
    step_vectors = []
    target_cycles = cleaned_cycles[-seq_len:]
    for i in range(len(target_cycles)):
        # Context up to and including cycle i from the tail
        # We want: step i uses cycles from position 0 to (len - seq_len + i + 1)
        end_idx = len(cleaned_cycles) - seq_len + i + 1
        subset_cycles = cleaned_cycles[:end_idx]
        vec = build_feature_vector(
            raw_profile, subset_cycles, raw_cycle_logs, raw_daily_logs, my_health_responses
        )
        step_vectors.append(vec)

    # Pad with zeros at front if not enough cycles
    while len(step_vectors) < seq_len:
        step_vectors.insert(0, np.zeros(n_features, dtype=np.float32))

    sequence = np.stack(step_vectors[-seq_len:], axis=0)    # (seq_len, n_features)
    return sequence.reshape(1, seq_len, n_features)          # (1, seq_len, n_features)