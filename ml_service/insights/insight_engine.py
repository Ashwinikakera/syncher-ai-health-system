"""
ml_service/insights/insight_engine.py
Rule-based insight generator using ML features.
Returns health_insights list for GET /api/dashboard.
These are pattern-based insights from ML data — NOT GenAI.
GenAI health_risk comes from health_engine.py.
"""

import logging
from typing import Optional
import numpy as np

from config import FEATURE_COLUMNS
from preprocessing.cleaning import clean_cycle_history, derive_cycle_lengths

logger = logging.getLogger(__name__)


def _get(feature_vector: np.ndarray, name: str) -> float:
    """Safe feature lookup by column name."""
    try:
        idx = FEATURE_COLUMNS.index(name)
        return float(feature_vector[idx])
    except (ValueError, IndexError):
        return 0.0


def generate_insights(
    feature_vector:  np.ndarray,
    raw_cycles:      list[dict],
    predicted_length: int,
    confidence:      float,
) -> list[str]:
    """
    Generates a list of human-readable cycle insights.
    Parameters
    ----------
    feature_vector   : output of build_feature_vector()
    raw_cycles       : raw cycle history for length analysis
    predicted_length : predicted next cycle length (days)
    confidence       : model confidence score [0,1]
    """
    insights = []

    cleaned_cycles  = clean_cycle_history(raw_cycles)
    cycle_lengths   = derive_cycle_lengths(cleaned_cycles)

    # ── Cycle regularity ──────────────────────────────────────────────────────
    variance    = _get(feature_vector, "cycle_variance")
    avg_cl      = _get(feature_vector, "avg_cycle_length")

    if variance < 4:
        insights.append("Your cycle is very regular — great for accurate predictions.")
    elif variance < 16:
        insights.append("Your cycle shows mild variation, which is common and normal.")
    else:
        insights.append("Your cycle shows significant variation. Tracking consistently will improve prediction accuracy.")

    if cycle_lengths:
        if all(21 <= cl <= 35 for cl in cycle_lengths):
            insights.append("All recent cycles fall within the normal 21–35 day range.")
        elif any(cl < 21 for cl in cycle_lengths):
            insights.append("At least one recent cycle was shorter than 21 days — this may indicate a short luteal phase or anovulation.")
        elif any(cl > 35 for cl in cycle_lengths):
            insights.append("At least one recent cycle was longer than 35 days — stress, hormonal shifts, or PCOS can cause this.")

    # ── Stress impact ─────────────────────────────────────────────────────────
    stress = _get(feature_vector, "stress")
    if stress >= 2.5:
        insights.append("High average stress levels can delay ovulation and lengthen cycles. Consider stress-management techniques.")
    elif stress >= 1.5:
        insights.append("Moderate stress detected. Consistent sleep and exercise may help stabilise your cycle.")

    # ── Sleep impact ──────────────────────────────────────────────────────────
    sleep = _get(feature_vector, "sleep")
    if sleep < 5:
        insights.append("Averaging fewer than 5 hours of sleep may disrupt hormone levels — aim for 7–9 hours.")
    elif sleep >= 7:
        insights.append("Your sleep pattern looks healthy, which supports hormonal balance.")

    # ── Exercise ──────────────────────────────────────────────────────────────
    exercise = _get(feature_vector, "exercise")
    if exercise == 0:
        insights.append("Sedentary lifestyle may worsen cycle irregularity. Light-to-moderate exercise 3–4 times/week is beneficial.")
    elif exercise >= 3:
        insights.append("High-intensity exercise can sometimes suppress ovulation. Ensure adequate calorie intake.")

    # ── Pain patterns ─────────────────────────────────────────────────────────
    pain = _get(feature_vector, "pain")
    if pain >= 4:
        insights.append("Consistently high menstrual pain (4–5/5) could indicate dysmenorrhea or endometriosis — worth discussing with a doctor.")
    elif pain >= 3:
        insights.append("Moderate cycle pain detected. Staying hydrated and reducing inflammatory foods may help.")

    # ── Symptoms ──────────────────────────────────────────────────────────────
    has_cramps     = _get(feature_vector, "has_cramps")
    has_headache   = _get(feature_vector, "has_headache")
    has_mood_swings = _get(feature_vector, "has_mood_swings")
    has_fatigue    = _get(feature_vector, "has_fatigue")
    has_nausea     = _get(feature_vector, "has_nausea")

    symptom_count = sum([has_cramps, has_headache, has_mood_swings, has_fatigue, has_nausea])
    if symptom_count >= 4:
        insights.append("Multiple premenstrual symptoms detected. This may point to PMS or PMDD — keeping a symptom log helps diagnosis.")
    if has_mood_swings and has_fatigue:
        insights.append("Mood swings combined with fatigue are common in the luteal phase; magnesium and B6 supplementation may help.")

    # ── Flow ──────────────────────────────────────────────────────────────────
    flow = _get(feature_vector, "flow")
    if flow >= 2.7:
        insights.append("Heavy average flow may indicate fibroids, polyps, or hormonal imbalance — consider an evaluation if persistent.")
    elif flow <= 1.2:
        insights.append("Light flow could indicate low oestrogen or uterine lining issues.")

    # ── Confidence note ───────────────────────────────────────────────────────
    if confidence < 0.6:
        insights.append("Prediction confidence is low — logging more cycles will significantly improve accuracy.")
    elif confidence >= 0.85:
        insights.append(f"High prediction confidence ({int(confidence * 100)}%) based on your consistent tracking.")

    # Deduplicate and cap
    seen = set()
    final = []
    for ins in insights:
        if ins not in seen:
            seen.add(ins)
            final.append(ins)

    return final[:6]   # dashboard shows top 6