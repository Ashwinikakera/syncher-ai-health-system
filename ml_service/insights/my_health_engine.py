"""
ml_service/insights/my_health_engine.py
LAYER 1 — My Health AI Engine.

Input : Q1-Q10 score + patterns + user cycle data + existing diagnosis
Output: PCOS/PCOD stage analysis (or screening) + health suggestions
        + doctor consult warning for High Risk.

Two paths:
  Path A — User already diagnosed (PCOS/PCOD from onboarding):
           → Acknowledge diagnosis, analyse STAGE, give stage-specific advice.
  Path B — No diagnosis / "none" / "other":
           → Screen for PCOS/PCOD symptoms from Q scores + cycle data.
           → Flag if likely, suggest getting diagnosed.
"""

import logging
import os
from config import GROQ_HEALTH_MODEL, GROQ_API_KEY, GROQ_MAX_TOKENS, GROQ_TEMPERATURE
from groq import Groq

logger = logging.getLogger(__name__)
_client = None


def _groq() -> Groq:
    global _client
    if _client is None:
        key = GROQ_API_KEY or os.getenv("GROQ_API_KEY", "")
        if not key:
            raise RuntimeError("GROQ_API_KEY not set.")
        _client = Groq(api_key=key)
    return _client


# ─── Prompt builder ────────────────────────────────────────────────────────────

def _build_prompt(
    score_result:    dict,
    user_profile:    dict,
    cycle_summary:   dict,
) -> str:
    score        = score_result["score"]
    risk         = score_result["risk_level"]
    breakdown    = score_result["breakdown"]
    patterns     = score_result["patterns_hit"]
    boost        = score_result["pattern_boost"]
    condition    = str(user_profile.get("medical_condition", "none")).lower()
    age          = user_profile.get("age", "unknown")
    already_diagnosed = condition in ("pcos", "pcod")

    # Cycle summary fields
    avg_cl       = cycle_summary.get("avg_cycle_length", 28)
    regularity   = cycle_summary.get("regularity_score", 1.0)
    cycle_count  = cycle_summary.get("cycle_count", 0)
    avg_pain     = cycle_summary.get("avg_pain", 1)
    avg_flow     = cycle_summary.get("avg_flow", "medium")

    lines = [
        "You are a women's health AI specialising in hormonal and menstrual health.",
        "Analyse the following user data and provide a structured health assessment.",
        "",
        f"USER AGE: {age}",
        f"KNOWN DIAGNOSIS: {condition.upper() if condition != 'none' else 'None reported'}",
        "",
        f"MY HEALTH QUESTIONNAIRE SCORE: {score}/110",
        f"RISK LEVEL: {risk}",
        f"SCORE BREAKDOWN: {breakdown}",
    ]

    if patterns:
        pattern_labels = {
            "androgen_dominance": "Androgen Dominance (persistent acne + excess body hair)",
            "insulin_resistance": "Insulin Resistance (significant weight change + abdominal fat)",
        }
        lines.append(f"CLINICAL PATTERNS DETECTED: {', '.join(pattern_labels.get(p, p) for p in patterns)}")
        lines.append(f"PATTERN BOOST APPLIED: +{boost} points")

    lines += [
        "",
        "CYCLE DATA:",
        f"  - Average cycle length  : {avg_cl} days",
        f"  - Cycle regularity score: {regularity} (1.0 = perfectly regular)",
        f"  - Number of cycles logged: {cycle_count}",
        f"  - Average menstrual pain : {avg_pain}/5",
        f"  - Average flow           : {avg_flow}",
        "",
    ]

    if already_diagnosed:
        lines += [
            f"TASK — PATH A (User already diagnosed with {condition.upper()}):",
            "1. Acknowledge the existing diagnosis warmly.",
            f"2. Based on the score ({score}/110) and patterns, determine the STAGE:",
            "   - Score 0-24  → Mild stage: well-managed or early",
            "   - Score 25-49 → Moderate stage: symptoms present but manageable",
            "   - Score 50-74 → Active stage: significant symptoms",
            "   - Score 75+   → Severe/Advanced stage: urgent attention needed",
            "3. Give 3-4 personalised health suggestions tailored to their stage.",
            "4. Address their cycle irregularity if regularity score < 0.7.",
            "5. If risk is High (score >= 75): add a clear doctor consultation warning.",
            "6. Add a FOOD SUGGESTIONS section with 4-5 specific foods/drinks that directly",
            f"   help manage {condition.upper()} at their current stage. Be specific:",
            "   - Name the exact food (e.g. 'Spearmint tea', 'Flaxseeds', 'Broccoli')",
            "   - Give ONE line on why it helps their specific condition and symptoms",
            "   - Consider their pain level, flow, and stress from cycle data above",
            "   - If androgen_dominance pattern: include anti-androgen foods (spearmint, flaxseed, pumpkin seeds)",
            "   - If insulin_resistance pattern: include low-GI foods (oats, lentils, cinnamon, berries)",
            "   - If high pain (avg_pain >= 3): include anti-inflammatory foods (turmeric, ginger, omega-3)",
            "7. Keep tone compassionate and empowering. Max 250 words.",
        ]
    else:
        lines += [
            "TASK — PATH B (No confirmed diagnosis):",
            "1. Based on the score, patterns, and cycle data, screen for PCOS/PCOD:",
            "   - If score >= 50 OR androgen_dominance OR insulin_resistance pattern:",
            "     → State the user MAY have PCOS/PCOD symptoms. Do NOT diagnose.",
            "     → Strongly suggest consulting a gynaecologist for proper diagnosis.",
            "   - If score < 50 and no patterns:",
            "     → Reassure the user — no strong indicators detected.",
            "2. Give 3 general health suggestions based on their specific Q scores.",
            "3. Address cycle irregularity if regularity_score < 0.7.",
            "4. If risk is High (score >= 75): add a strong doctor consultation warning.",
            "5. Add a FOOD SUGGESTIONS section with 4-5 specific foods that support",
            "   hormonal balance and menstrual health based on their Q scores:",
            "   - If high acne/hair score (q1/q2 >= 10): spearmint tea, zinc-rich foods (pumpkin seeds, chickpeas)",
            "   - If weight/insulin scores (q4/q5/q6 >= 10): cinnamon, berries, oats, lentils, leafy greens",
            "   - If fatigue/energy score (q8 >= 5): iron-rich foods (spinach, lentils), vitamin C foods",
            "   - If poor diet score (q10 >= 5): specific whole foods to replace their junk/processed intake",
            "   - Always include: name of food + one-line reason why it helps their specific symptoms",
            "6. Keep tone compassionate. Max 250 words.",
        ]

    lines += [
        "",
        "FORMAT YOUR RESPONSE AS:",
        "**Assessment:** [1-2 sentence summary]",
        "**Health Suggestions:**",
        "- [suggestion 1]",
        "- [suggestion 2]",
        "- [suggestion 3]",
        "**Food Suggestions:**",
        "- [Food name]: [one line — why it specifically helps this user's condition/symptoms]",
        "- [Food name]: [one line — why it specifically helps this user's condition/symptoms]",
        "- [Food name]: [one line — why it specifically helps this user's condition/symptoms]",
        "- [Food name]: [one line — why it specifically helps this user's condition/symptoms]",
        "**Doctor Consultation:** [only include this section if High Risk or PCOS suspected]",
    ]

    return "\n".join(lines)


# ─── Main function ─────────────────────────────────────────────────────────────

def analyse_my_health(
    score_result:  dict,
    user_profile:  dict,
    raw_cycles:    list[dict],
    cycle_lengths: list[int],
    avg_pain:      float,
    avg_flow_str:  str,
) -> str:
    """
    Called by main.py after compute_score().
    Returns the AI-generated health analysis string.
    """
    cycle_summary = {
        "avg_cycle_length":  user_profile.get("avg_cycle_length", 28),
        "regularity_score":  _regularity_score(cycle_lengths),
        "cycle_count":       len(raw_cycles),
        "avg_pain":          round(avg_pain, 1),
        "avg_flow":          avg_flow_str,
    }

    prompt = _build_prompt(score_result, user_profile, cycle_summary)

    try:
        resp = _groq().chat.completions.create(
            model=GROQ_HEALTH_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a compassionate women's health assistant. "
                        "Provide evidence-based, personalised health guidance. "
                        "Never diagnose. Recommend professional consultation for high-risk cases."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=GROQ_MAX_TOKENS,
            temperature=GROQ_TEMPERATURE,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.error("my_health_engine Groq call failed: %s", e)
        return (
            "Health analysis is temporarily unavailable. "
            "Your score has been saved. Please consult a healthcare professional "
            "if you have concerns about your hormonal health."
        )


def _regularity_score(lengths: list) -> float:
    import numpy as np
    if not lengths: return 1.0
    arr  = np.array(lengths, dtype=float)
    mean = np.mean(arr)
    if mean == 0: return 1.0
    cv   = np.std(arr) / mean
    return round(float(max(0.0, min(1.0, 1.0 - cv))), 2)