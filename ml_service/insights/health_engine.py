"""
ml_service/insights/health_engine.py

ARCHITECTURE: Dashboard — Analytical AI
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This layer sits between the ML engine and the LLM.
It does NOT call LLM blindly — it:

  1. Collects structured signals from ML (risk_flags, feature_vector,
     my_health score, cycle predictions, open-text fields from logs).
  2. Builds a tightly scoped, data-dense prompt — not a chat prompt.
  3. Calls Groq llama-3.1-8b-instant with temperature=0.2
     for deterministic, structured JSON response.
  4. Parses and returns: risk_level + risk_summary + suggestions list.

This is Analytical AI — NOT a conversational agent.
The chatbot (rag.py) is the conversational agent — completely separate.

Called by: main.py → /ml/dashboard
Model: llama-3.1-8b-instant  (fast, structured output)
"""

import json
import logging
import os
from typing import Optional

from groq import Groq

from config import GROQ_API_KEY, GROQ_HEALTH_MODEL

logger = logging.getLogger(__name__)

_client: Optional[Groq] = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        api_key = GROQ_API_KEY or os.getenv("GROQ_API_KEY", "")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY is not set.")
        _client = Groq(api_key=api_key)
    return _client


# ─── Signal collector ─────────────────────────────────────────────────────────

def _collect_signals(user_context: dict, risk_context: str, my_health_result: dict) -> dict:
    """
    Extracts only the signals relevant to health_risk analysis.
    Returns a compact structured dict — this is the LLM's input,
    not raw user logs. Keeps prompt small and focused.
    """
    profile    = user_context.get("profile", {})
    daily_logs = user_context.get("daily_logs", [])
    cycle_logs = user_context.get("cycle_logs", [])

    # Open-text fields — only these go to LLM (rest is rule-based)
    medications     = []
    routine_changes = []
    for log in daily_logs + cycle_logs:
        if str(log.get("medication", "")).lower() == "yes" and log.get("medication_details"):
            med = log["medication_details"].strip()
            if med and med not in medications:
                medications.append(med)
        if str(log.get("routine_change", "")).lower() == "yes" and log.get("routine_details"):
            rc = log["routine_details"].strip()
            if rc and rc not in routine_changes:
                routine_changes.append(rc)

    # Aggregate numeric lifestyle signals (last 7 days)
    recent = daily_logs[:7]
    avg_sleep = round(
        sum(float(l.get("sleep") or 0) for l in recent) / max(len(recent), 1), 1
    )
    stress_vals = [str(l.get("stress", "none")).lower() for l in recent]
    stress_high_pct = round(
        sum(1 for s in stress_vals if s in ("high", "medium")) / max(len(stress_vals), 1) * 100
    )

    return {
        "age":                profile.get("age"),
        "weight_kg":          profile.get("weight"),
        "diagnosed_condition": profile.get("medical_condition", "none"),
        "medical_notes":      profile.get("medical_notes", ""),
        "medications":        medications,
        "routine_changes":    routine_changes,
        "avg_sleep_hrs":      avg_sleep,
        "stress_high_pct":    stress_high_pct,
        "cycle_risk_flags":   risk_context or "No specific cycle risk flags detected.",
        "my_health_score":    my_health_result.get("score", 0),
        "my_health_risk":     my_health_result.get("risk_level", "Low Risk"),
        "my_health_patterns": my_health_result.get("insights", [])[:2],
    }


# ─── Prompt & schema ──────────────────────────────────────────────────────────

_ANALYTICAL_SYSTEM = (
    "You are a clinical decision-support engine for a women's health app. "
    "You receive structured health signals and return ONLY a JSON object — nothing else. "
    "Be precise, evidence-based, and concise. Never diagnose. "
    "No preamble, no markdown, no text outside the JSON."
)

_JSON_SCHEMA = """{
  "risk_level": "Low | Moderate | High",
  "risk_summary": "One sentence (max 25 words) summarising the overall risk.",
  "suggestions": [
    "Actionable health suggestion 1 (max 20 words)",
    "Actionable health suggestion 2 (max 20 words)",
    "Actionable health suggestion 3 (max 20 words)"
  ],
  "food_suggestions": [
    "Food name: one line why it helps this user's specific condition/symptoms",
    "Food name: one line why it helps this user's specific condition/symptoms",
    "Food name: one line why it helps this user's specific condition/symptoms"
  ],
  "medication_note": "One sentence about medication/cycle interaction, or null.",
  "seek_doctor": true | false
}"""


def _build_analytical_prompt(signals: dict) -> str:
    lines = [
        "Analyse the following structured health signals.",
        "Return ONLY valid JSON matching this schema:",
        "",
        _JSON_SCHEMA,
        "",
        "SIGNALS:",
        f"- Age: {signals['age']}",
        f"- Weight: {signals['weight_kg']} kg",
        f"- Diagnosed condition: {signals['diagnosed_condition']}",
    ]

    if signals["medical_notes"]:
        lines.append(f"- Medical notes: {signals['medical_notes']}")

    if signals["medications"]:
        lines.append(f"- Current medications: {'; '.join(signals['medications'])}")

    if signals["routine_changes"]:
        lines.append(f"- Recent routine changes: {'; '.join(signals['routine_changes'])}")

    lines += [
        f"- Avg sleep last 7 days: {signals['avg_sleep_hrs']} hrs",
        f"- Days with high/medium stress last 7 days: {signals['stress_high_pct']}%",
        "",
        "CYCLE RISK FLAGS (ML engine output):",
        signals["cycle_risk_flags"],
        "",
        f"MY HEALTH SCORE: {signals['my_health_score']}/110  →  {signals['my_health_risk']}",
    ]

    if signals["my_health_patterns"]:
        lines.append("Key My Health patterns:")
        for p in signals["my_health_patterns"]:
            lines.append(f"  • {p}")

    lines += ["", "Return ONLY the JSON object. No extra text.",
              "",
              "FOOD SUGGESTION RULES (for food_suggestions field):",
              "- Give 3 specific foods tailored to THIS user's signals above.",
              "- Format each as: 'Food name: reason why it helps their specific condition'",
              "- Base food choices on:",
              "  • diagnosed_condition (PCOS→low-GI, spearmint, flaxseed; thyroid→selenium foods)",
              "  • cycle risk flags (HIGH_PAIN→turmeric, ginger, omega-3; HIGH_STRESS→magnesium foods, dark chocolate)",
              "  • avg_sleep_hrs < 6 → tryptophan foods (banana, almonds, oats)",
              "  • stress_high_pct > 50% → adaptogen foods (ashwagandha, chamomile tea, leafy greens)",
              "  • HEAVY_FLOW flag → iron-rich foods (spinach, lentils, tofu)",
              "  • my_health_risk High → anti-inflammatory foods (berries, fatty fish, turmeric)",
              "- Never suggest supplements as primary — suggest whole foods first.",
              "Return ONLY the JSON object. No extra text."]
    return "\n".join(lines)


# ─── Response parser ──────────────────────────────────────────────────────────

_FALLBACK = {
    "risk_level":      "Moderate",
    "risk_summary":    "Health risk analysis is temporarily unavailable.",
    "suggestions":     [
        "Continue tracking your cycle regularly.",
        "Maintain consistent sleep and exercise.",
        "Consult your doctor if you have ongoing concerns.",
    ],
    "food_suggestions": [
        "Leafy greens (spinach, kale): rich in iron and magnesium to support hormonal balance.",
        "Flaxseeds: contain lignans that help regulate oestrogen levels.",
        "Ginger tea: natural anti-inflammatory that reduces menstrual cramps.",
    ],
    "medication_note": None,
    "seek_doctor":     False,
}


def _parse_response(raw: str) -> dict:
    """Strip markdown fences and parse JSON. Return fallback on failure."""
    try:
        clean = raw.strip()
        if clean.startswith("```"):
            parts = clean.split("```")
            clean = parts[1] if len(parts) > 1 else clean
            if clean.lower().startswith("json"):
                clean = clean[4:]
        parsed = json.loads(clean.strip())

        # Validate required keys
        required = {"risk_level", "risk_summary", "suggestions", "seek_doctor"}
        missing  = required - set(parsed.keys())
        if missing:
            raise ValueError(f"Missing JSON keys: {missing}")

        parsed["suggestions"]     = (parsed.get("suggestions")     or [])[:3]
        parsed["food_suggestions"] = (parsed.get("food_suggestions") or [])[:3]
        return parsed

    except Exception as exc:
        logger.warning("health_engine parse failed (%s) — using fallback.", exc)
        return _FALLBACK.copy()


# ─── Public API ───────────────────────────────────────────────────────────────

def generate_health_risk(
    user_context:     dict,
    risk_context:     str,
    my_health_result: Optional[dict] = None,
) -> dict:
    """
    Dashboard Analytical AI entry point.

    Parameters
    ----------
    user_context     : from db_fetcher.fetch_full_user_context()
    risk_context     : from risk_engine.get_risk_context()
    my_health_result : from my_health_scorer.compute_my_health_score()
                       pass {} or None if user hasn't done My Health yet

    Returns
    -------
    dict:
        risk_level      : str   "Low" | "Moderate" | "High"
        risk_summary    : str
        suggestions     : list[str]  (3 items)
        medication_note : str | None
        seek_doctor     : bool
    """
    if my_health_result is None:
        my_health_result = {}

    signals = _collect_signals(user_context, risk_context, my_health_result)
    prompt  = _build_analytical_prompt(signals)

    try:
        client   = _get_client()
        response = client.chat.completions.create(
            model=GROQ_HEALTH_MODEL,
            messages=[
                {"role": "system", "content": _ANALYTICAL_SYSTEM},
                {"role": "user",   "content": prompt},
            ],
            max_tokens=400,
            temperature=0.2,   # low = deterministic, structured
        )
        raw    = response.choices[0].message.content
        result = _parse_response(raw)
        logger.info(
            "Dashboard health analysis: risk=%s seek_doctor=%s",
            result.get("risk_level"), result.get("seek_doctor"),
        )
        return result

    except Exception as exc:
        logger.error("health_engine Groq call failed: %s", exc)
        return _FALLBACK.copy()


def generate_medical_notes_suggestion(medical_notes: str, condition: str) -> str:
    """
    Onboarding only — called when user types free text in medical notes.
    Returns a brief (2–3 sentence) health suggestion string.
    Non-fatal: returns empty string on failure.
    """
    if not medical_notes or not medical_notes.strip():
        return ""

    prompt = (
        f"User condition: '{condition}'. User note: \"{medical_notes.strip()}\"\n"
        "In 2–3 sentences, give a compassionate health suggestion. "
        "Do not diagnose. Recommend professional consultation if concerning. "
        "Return plain text only."
    )
    try:
        client = _get_client()
        response = client.chat.completions.create(
            model=GROQ_HEALTH_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=120,
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        logger.error("medical_notes_suggestion failed: %s", exc)
        return ""