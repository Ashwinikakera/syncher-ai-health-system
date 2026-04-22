"""
ml_service/insights/risk_engine.py
Rule-based cycle risk detector.
Returns structured risk flags consumed by:
  - health_engine.py  → LLM analytical prompt (via get_risk_context)
  - main.py           → dashboard response (via summarise_risk)

No LLM calls here — pure rule logic, same pattern as insight_engine.py.
"""

import logging
from typing import Optional
import numpy as np

from config import FEATURE_COLUMNS
from preprocessing.cleaning import clean_cycle_history, derive_cycle_lengths

logger = logging.getLogger(__name__)


# ─── Feature helper (mirrors insight_engine.py) ───────────────────────────────

def _get(feature_vector: np.ndarray, name: str) -> float:
    """Safe feature lookup by column name."""
    try:
        idx = FEATURE_COLUMNS.index(name)
        return float(feature_vector[idx])
    except (ValueError, IndexError):
        return 0.0


# ─── Risk flag definitions ────────────────────────────────────────────────────
#
# Each flag is a dict:
#   code        : short machine-readable key
#   severity    : "low" | "moderate" | "high"
#   message     : human-readable one-liner for the dashboard
#   detail      : longer context string sent to the LLM prompt
#

def detect_cycle_risks(
    feature_vector: np.ndarray,
    raw_cycles: list[dict],
) -> list[dict]:
    """
    Analyses feature vector + raw cycle history and returns a list of
    risk flag dicts. Empty list = no flags detected.

    Parameters
    ----------
    feature_vector : output of build_feature_vector()
    raw_cycles     : raw cycle history from db_fetcher

    Returns
    -------
    list[dict]  — each dict has keys: code, severity, message, detail
    """
    flags = []

    cleaned_cycles = clean_cycle_history(raw_cycles)
    cycle_lengths  = derive_cycle_lengths(cleaned_cycles)

    variance  = _get(feature_vector, "cycle_variance")
    avg_cl    = _get(feature_vector, "avg_cycle_length")
    stress    = _get(feature_vector, "stress")
    sleep     = _get(feature_vector, "sleep")
    pain      = _get(feature_vector, "pain")
    flow      = _get(feature_vector, "flow")
    exercise  = _get(feature_vector, "exercise")

    has_cramps      = _get(feature_vector, "has_cramps")
    has_headache    = _get(feature_vector, "has_headache")
    has_mood_swings = _get(feature_vector, "has_mood_swings")
    has_fatigue     = _get(feature_vector, "has_fatigue")
    has_nausea      = _get(feature_vector, "has_nausea")

    # ── Cycle length anomalies ────────────────────────────────────────────────

    if cycle_lengths:
        short = [cl for cl in cycle_lengths if cl < 21]
        long_ = [cl for cl in cycle_lengths if cl > 35]

        if short:
            flags.append({
                "code":     "SHORT_CYCLE",
                "severity": "moderate",
                "message":  f"Short cycle(s) detected ({min(short)} days) — below the normal 21-day threshold.",
                "detail":   (
                    f"{len(short)} of {len(cycle_lengths)} recent cycles were shorter than 21 days "
                    f"(shortest: {min(short)} days). May indicate short luteal phase or anovulation."
                ),
            })

        if long_:
            flags.append({
                "code":     "LONG_CYCLE",
                "severity": "moderate",
                "message":  f"Long cycle(s) detected ({max(long_)} days) — above the normal 35-day threshold.",
                "detail":   (
                    f"{len(long_)} of {len(cycle_lengths)} recent cycles exceeded 35 days "
                    f"(longest: {max(long_)} days). Possible causes: PCOS, thyroid issues, high stress."
                ),
            })

    # ── High cycle variance ───────────────────────────────────────────────────

    if variance >= 16:
        flags.append({
            "code":     "HIGH_VARIANCE",
            "severity": "moderate",
            "message":  "Cycle length varies significantly — irregular cycle pattern detected.",
            "detail":   (
                f"Cycle variance is {round(variance, 1)} days². "
                "Significant irregularity may be linked to hormonal imbalance, stress, or lifestyle factors."
            ),
        })

    # ── Cycle length outside healthy average ─────────────────────────────────

    if avg_cl > 0 and (avg_cl < 21 or avg_cl > 35):
        flags.append({
            "code":     "AVG_CYCLE_ANOMALY",
            "severity": "high" if avg_cl < 18 or avg_cl > 45 else "moderate",
            "message":  f"Average cycle length ({round(avg_cl)} days) is outside the normal range.",
            "detail":   (
                f"Average cycle length is {round(avg_cl, 1)} days. "
                "Normal range is 21–35 days. Persistent anomaly warrants medical evaluation."
            ),
        })

    # ── Pain ─────────────────────────────────────────────────────────────────

    if pain >= 4:
        flags.append({
            "code":     "HIGH_PAIN",
            "severity": "high",
            "message":  "Consistently high menstrual pain — possible dysmenorrhea or endometriosis.",
            "detail":   (
                f"Average pain score is {round(pain, 1)}/5. "
                "Severe, recurring pain may indicate dysmenorrhea, endometriosis, or fibroids."
            ),
        })
    elif pain >= 3:
        flags.append({
            "code":     "MODERATE_PAIN",
            "severity": "low",
            "message":  "Moderate menstrual pain logged consistently.",
            "detail":   f"Average pain score is {round(pain, 1)}/5. Monitor for escalation.",
        })

    # ── Flow ─────────────────────────────────────────────────────────────────

    if flow >= 2.7:
        flags.append({
            "code":     "HEAVY_FLOW",
            "severity": "moderate",
            "message":  "Heavy average menstrual flow detected.",
            "detail":   (
                f"Flow score averaging {round(flow, 1)}/3. "
                "Heavy flow may indicate fibroids, polyps, or hormonal imbalance."
            ),
        })
    elif flow <= 1.2 and flow > 0:
        flags.append({
            "code":     "LIGHT_FLOW",
            "severity": "low",
            "message":  "Consistently light menstrual flow logged.",
            "detail":   (
                f"Flow score averaging {round(flow, 1)}/3. "
                "Very light flow may suggest low oestrogen or thin uterine lining."
            ),
        })

    # ── Stress ───────────────────────────────────────────────────────────────

    if stress >= 2.5:
        flags.append({
            "code":     "HIGH_STRESS",
            "severity": "moderate",
            "message":  "Elevated stress levels may be disrupting cycle regularity.",
            "detail":   (
                f"Stress score averaging {round(stress, 1)}/3. "
                "Chronic high stress elevates cortisol, which can delay or suppress ovulation."
            ),
        })

    # ── Sleep ─────────────────────────────────────────────────────────────────

    if sleep < 5:
        flags.append({
            "code":     "POOR_SLEEP",
            "severity": "moderate",
            "message":  "Average sleep below 5 hours — likely impacting hormonal balance.",
            "detail":   (
                f"Average sleep is {round(sleep, 1)} hrs/night. "
                "Chronic sleep deprivation disrupts melatonin, LH, and FSH rhythms."
            ),
        })

    # ── Combined symptom burden ───────────────────────────────────────────────

    symptom_count = sum([
        has_cramps, has_headache, has_mood_swings, has_fatigue, has_nausea
    ])
    if symptom_count >= 4:
        active = [
            name for name, val in [
                ("cramps", has_cramps), ("headaches", has_headache),
                ("mood swings", has_mood_swings), ("fatigue", has_fatigue),
                ("nausea", has_nausea),
            ] if val
        ]
        flags.append({
            "code":     "HIGH_SYMPTOM_BURDEN",
            "severity": "moderate",
            "message":  f"Multiple premenstrual symptoms present: {', '.join(active)}.",
            "detail":   (
                f"{int(symptom_count)} of 5 tracked symptoms are active "
                f"({', '.join(active)}). Pattern consistent with PMS or PMDD."
            ),
        })

    # ── Excessive exercise ────────────────────────────────────────────────────

    if exercise >= 3:
        flags.append({
            "code":     "EXCESSIVE_EXERCISE",
            "severity": "low",
            "message":  "High-intensity exercise frequency may suppress ovulation.",
            "detail":   (
                f"Exercise score {round(exercise, 1)}/3. "
                "High training loads with insufficient caloric intake can cause hypothalamic amenorrhea."
            ),
        })

    logger.info(
        "Risk detection complete — %d flag(s): %s",
        len(flags),
        [f["code"] for f in flags] or "none",
    )
    return flags


# ─── Consumers ────────────────────────────────────────────────────────────────

def summarise_risk(risk_flags: list[dict]) -> dict:
    """
    Returns a compact risk summary for the dashboard JSON response.

    Returns
    -------
    dict:
        overall_severity : "none" | "low" | "moderate" | "high"
        flag_count       : int
        top_flags        : list[str]  — up to 3 human-readable messages
    """
    if not risk_flags:
        return {
            "overall_severity": "none",
            "flag_count":       0,
            "top_flags":        [],
        }

    _rank = {"high": 3, "moderate": 2, "low": 1}
    sorted_flags = sorted(risk_flags, key=lambda f: _rank.get(f["severity"], 0), reverse=True)

    overall = sorted_flags[0]["severity"]

    return {
        "overall_severity": overall,
        "flag_count":       len(risk_flags),
        "top_flags":        [f["message"] for f in sorted_flags[:3]],
    }


def get_risk_context(risk_flags: list[dict]) -> str:
    """
    Builds a concise plain-text summary of all risk flags for the LLM prompt
    in health_engine.py. Keeps the prompt focused and under token limits.

    Returns
    -------
    str — multi-line risk context, or a no-risk message if flags is empty.
    """
    if not risk_flags:
        return "No specific cycle risk flags detected."

    _rank = {"high": 3, "moderate": 2, "low": 1}
    sorted_flags = sorted(risk_flags, key=lambda f: _rank.get(f["severity"], 0), reverse=True)

    lines = []
    for f in sorted_flags:
        lines.append(f"[{f['severity'].upper()}] {f['code']}: {f['detail']}")

    return "\n".join(lines)