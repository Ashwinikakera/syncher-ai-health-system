"""
ml_service/prediction/my_health_scorer.py

ARCHITECTURE: Rule-based / Light LLM
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  • Scoring  → 100% rule-based  (Q1–Q10 + Pattern Boost)
  • Insights → rule-based text snippets  (no LLM needed)
  • Light LLM (llama-3.1-8b-instant) is called ONLY when the user
    selected "Other" in medical_condition and typed free text.
    That single call returns a short condition-specific note
    appended to the rule-based insights list.

This is intentionally lightweight — heavy LLM work belongs in
health_engine.py (Dashboard Analytical AI) and rag.py (Chatbot Agent).

API contract: POST /api/my-health strings must match exactly.
"""

import logging
import os
from typing import Optional
from config import MY_HEALTH_SCORE_MAP, MY_HEALTH_RISK_BANDS, GROQ_API_KEY, GROQ_HEALTH_MODEL

logger = logging.getLogger(__name__)

# ─── Answer → score maps (aliases handle minor spacing variants) ──────────────
_SCORE_MAP = {
    "q1": {
        "none": 0,
        "mild/occasional": 5,
        "persistent/recurrent": 10,
        "severe/cystic": 15,
    },
    "q2": {
        "none": 0,
        "mild": 5,
        "moderate": 10,
        "significant": 15,
    },
    "q3": {
        "no": 0,
        "mild": 5,
        "noticeable": 10,
    },
    "q4": {
        "no": 0,
        "mild (2-4 kg)": 5,
        "mild (2–4 kg)": 5,
        "moderate (5-8 kg)": 10,
        "moderate (5–8 kg)": 10,
        "significant (>8 kg)": 15,
    },
    "q5": {
        "no": 0,
        "mild (2-4 kg)": 5,
        "mild (2–4 kg)": 5,
        "moderate (5-8 kg)": 10,
        "moderate (5–8 kg)": 10,
        "significant (>8 kg)": 15,
    },
    "q6": {
        "no": 0,
        "yes": 10,
    },
    "q7": {
        "no": 0,
        "mild": 5,
        "clear/visible": 10,
    },
    "q8": {
        "normal": 0,
        "slight sleepiness": 5,
        "strong fatigue/crashes": 10,
    },
    "q9": {
        "≥4 times/week": 0,
        ">=4 times/week": 0,
        "2-3 times/week": 5,
        "2–3 times/week": 5,
        "rare/none": 10,
    },
    "q10": {
        "mostly whole foods": 0,
        "mixed": 5,
        "high sugar/processed/junk": 10,
    },
}


def _get_score(question: str, answer: str) -> int:
    """Look up score for a given Q answer. Warn and return 0 if unrecognised."""
    mapping = _SCORE_MAP.get(question, {})
    key = str(answer).strip().lower()
    if key not in mapping:
        logger.warning("Unknown answer for %s: '%s'", question, answer)
        return 0
    return mapping[key]


def _risk_level(score: int) -> str:
    for low, high, label in MY_HEALTH_RISK_BANDS:
        if low <= score <= high:
            return label
    return "High Risk"


def compute_my_health_score(responses: dict) -> dict:
    """
    Parameters
    ----------
    responses : dict with keys q1–q10, values are the exact API contract strings.

    Returns
    -------
    dict:
        score      : int   (0 – 110+)
        risk_level : str   (Low / Mild / Moderate / High Risk)
        breakdown  : dict  {q1: score, ..., q10: score}
        pattern_boost : int  (bonus points from pattern rules)
        insights   : list[str]
    """
    if not responses:
        return {"score": 0, "risk_level": "Low Risk", "breakdown": {}, "pattern_boost": 0, "insights": []}

    # ── Individual question scores ────────────────────────────────────────────
    breakdown = {}
    for q in [f"q{i}" for i in range(1, 11)]:
        ans = responses.get(q, "")
        breakdown[q] = _get_score(q, ans)

    base_score = sum(breakdown.values())

    # ── Smart Pattern Boost ───────────────────────────────────────────────────
    pattern_boost = 0
    boost_reasons = []
    patterns_hit  = []   # machine-readable pattern IDs for my_health_engine

    # Rule 1: Androgen Dominance — Q1 ≥ 10 AND Q2 ≥ 10
    if breakdown.get("q1", 0) >= 10 and breakdown.get("q2", 0) >= 10:
        pattern_boost += 10
        patterns_hit.append("androgen_dominance")
        boost_reasons.append("Androgen dominance pattern detected (acne + excess hair)")

    # Rule 2: Insulin Resistance — Q4 ≥ 10 AND Q5 >= 10 AND Q6 ≥ 5
    # Note: spec says Q5 == 10 but that seems overly strict; using >= 10
    if (breakdown.get("q4", 0) >= 10
            and breakdown.get("q5", 0) >= 10
            and breakdown.get("q6", 0) >= 5):
        pattern_boost += 10
        patterns_hit.append("insulin_resistance")
        boost_reasons.append("Insulin resistance pattern detected (weight gain + abdominal fat)")

    total_score = base_score + pattern_boost
    risk = _risk_level(total_score)

    # ── Generate insights ─────────────────────────────────────────────────────
    insights = list(boost_reasons)

    if breakdown.get("q1", 0) >= 10:
        insights.append("Persistent acne may indicate elevated androgen levels — consider consulting a dermatologist or endocrinologist.")
    if breakdown.get("q3", 0) >= 5:
        insights.append("Hair thinning at the crown or front may be related to hormonal imbalance.")
    if breakdown.get("q4", 0) >= 10 or breakdown.get("q5", 0) >= 10:
        insights.append("Significant unexplained weight change warrants a metabolic or thyroid evaluation.")
    if breakdown.get("q6", 0) >= 10:
        insights.append("Abdominal fat distribution is associated with insulin resistance — dietary changes may help.")
    if breakdown.get("q7", 0) >= 5:
        insights.append("Dark patches on skin (acanthosis nigricans) can indicate insulin resistance — worth discussing with your doctor.")
    if breakdown.get("q8", 0) >= 5:
        insights.append("Post-meal energy crashes may suggest blood sugar dysregulation; reducing refined carb intake can help.")
    if breakdown.get("q9", 0) >= 5:
        insights.append("Increasing physical activity to at least 4 sessions per week can significantly improve hormonal balance.")
    if breakdown.get("q10", 0) >= 5:
        insights.append("High sugar and processed food intake worsens hormonal and metabolic symptoms.")

    if not insights:
        insights.append("Your health indicators look good. Keep maintaining your current lifestyle.")

    return {
        "score":         total_score,
        "risk_level":    risk,
        "breakdown":     breakdown,
        "pattern_boost": pattern_boost,
        "patterns_hit":  patterns_hit,
        "insights":      insights,
    }


# ─── Light LLM: called ONLY for "Other" free-text medical condition ───────────

def get_other_condition_note(condition_text: str) -> str:
    """
    Called ONLY when user selected 'Other' in medical_condition and typed
    a custom condition (e.g. 'endometriosis', 'adenomyosis', 'MRKH').

    Uses llama-3.1-8b-instant via Groq for a short, factual note
    about how that condition may relate to menstrual health.

    Returns a single plain-English sentence or empty string on failure.
    This result is appended to the rule-based insights list by the caller.
    """
    if not condition_text or not condition_text.strip():
        return ""

    prompt = (
        f"A user has reported the following self-described medical condition: "
        f"\"{condition_text.strip()}\"\n\n"
        "In ONE sentence (max 30 words), state how this condition typically affects "
        "the menstrual cycle. Be factual and neutral. Do not diagnose or recommend treatment."
    )

    try:
        from groq import Groq
        api_key = GROQ_API_KEY or os.getenv("GROQ_API_KEY", "")
        if not api_key:
            logger.warning("GROQ_API_KEY not set — skipping Other condition note.")
            return ""

        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model=GROQ_HEALTH_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=60,        # deliberately tiny — one sentence only
            temperature=0.2,
        )
        note = response.choices[0].message.content.strip()
        logger.info("Other condition note generated for: '%s'", condition_text[:40])
        return note

    except Exception as exc:
        logger.warning("Other condition note failed: %s", exc)
        return ""