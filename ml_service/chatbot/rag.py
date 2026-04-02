# ml_service/chatbot/rag.py
# Fixed: NLP now extracts stress and exercise in API contract format

import json
from ml_service.chatbot.groq_client import generate_response
from ml_service.prediction.feature_extraction import (
    extract_cycle_features,
    extract_symptom_features,
)


SYSTEM_PROMPT = """
You are SYNCHER, a warm, knowledgeable women's health assistant.
You specialize in menstrual health, cycle tracking, and hormonal wellness.

Your rules:
- Be empathetic, supportive, and evidence-based
- Answer in 2 to 4 sentences maximum - be concise and direct
- Do NOT repeat or rephrase the user's question in your answer
- Never diagnose - suggest consulting a doctor for medical concerns
- Use the user's cycle data when provided to personalize your response
- If cycle data is irrelevant to the question, answer generally
- Mention the relevant cycle phase (menstrual, follicular, ovulation, luteal) when helpful
"""

# ── NLP system prompt — fixed to match API contract field names ───────────────
# Contract field names:
#   pain      → integer 0-10
#   mood      → "low" | "medium" | "high"
#   flow      → "heavy" | "medium" | "light" | "spotting"
#   sleep     → float hours
#   stress    → "low" | "medium" | "high"      ← STRING not integer
#   exercise  → "none" | "light" | "moderate" | "heavy"  ← STRING not integer

NLP_SYSTEM_PROMPT = """
You are a health data extraction assistant.
Extract health information from the user's message and return ONLY a valid JSON object.
No explanation, no markdown, no backticks — just raw JSON.

STRICT rules:
- stress must be one of: "low", "medium", "high" — or null if not mentioned
- exercise must be one of: "none", "light", "moderate", "heavy" — or null if not mentioned
- mood must be one of: "low", "medium", "high" — or null if not mentioned
- flow must be one of: "heavy", "medium", "light", "spotting" — or null if not mentioned
- pain is an integer 0-10 — or null if not mentioned
- sleep is a float (hours) — or null if not mentioned

Stress mapping guide:
  "stressed", "very stressed", "anxious", "overwhelmed" → "high"
  "a bit stressed", "somewhat stressed", "worried"      → "medium"
  "calm", "relaxed", "fine", "not stressed"             → "low"

Exercise mapping guide:
  "didn't exercise", "no workout", "rested", "sedentary" → "none"
  "walked", "light walk", "yoga", "stretching"            → "light"
  "jogged", "gym", "workout", "ran"                       → "moderate"
  "intense", "HIIT", "heavy lifting", "marathon"          → "heavy"

JSON format (use EXACT field names):
{
  "pain":     <integer 0-10 or null>,
  "mood":     <"low"|"medium"|"high" or null>,
  "flow":     <"heavy"|"medium"|"light"|"spotting" or null>,
  "sleep":    <float or null>,
  "stress":   <"low"|"medium"|"high" or null>,
  "exercise": <"none"|"light"|"moderate"|"heavy" or null>
}
"""


# ── Context builder ───────────────────────────────────────────────────────────

def build_context(user_data: dict) -> str:
    cycle_records = user_data.get("cycle_records", [])
    log_records   = user_data.get("log_records",   [])
    context_parts = []

    if cycle_records:
        try:
            cycle_feat = extract_cycle_features(cycle_records)
            context_parts.append(
                f"CYCLE DATA:\n"
                f"- Average cycle length: {cycle_feat.get('avg_cycle_length')} days\n"
                f"- Is irregular: {cycle_feat.get('is_irregular')}\n"
                f"- Cycle trend: {cycle_feat.get('cycle_trend')}\n"
                f"- Last cycle started: {cycle_feat.get('last_cycle_start')}\n"
                f"- Last cycle length: {cycle_feat.get('last_cycle_length')} days"
            )
        except Exception as e:
            context_parts.append(f"CYCLE DATA: Could not process - {e}")

    if log_records:
        try:
            symptom_feat = extract_symptom_features(log_records)
            context_parts.append(
                f"SYMPTOM DATA:\n"
                f"- Average pain level: {symptom_feat.get('avg_pain')} / 10\n"
                f"- Dominant mood: {symptom_feat.get('dominant_mood')}\n"
                f"- Average sleep: {symptom_feat.get('avg_sleep')} hours\n"
                f"- Average stress level: {symptom_feat.get('avg_stress')} / 10"
            )
        except Exception as e:
            context_parts.append(f"SYMPTOM DATA: Could not process - {e}")

    if not context_parts:
        return "No personal health data available for this user."

    return "\n\n".join(context_parts)


# ── RAG pipeline ──────────────────────────────────────────────────────────────

def rag_chat(question: str, user_data: dict) -> dict:
    """
    Main RAG function - called by Dev1's chatbot_app/services.py
    Returns: {"answer": "..."}
    """
    if not question or not question.strip():
        return {"answer": "Please ask me a question about your health."}

    context = build_context(user_data)
    has_data = bool(
        user_data.get("cycle_records") or user_data.get("log_records")
    )

    if has_data:
        prompt = (
            f"User's health data:\n{context}\n\n"
            f"Question: {question}\n\n"
            f"Give a short, personalized answer using the data above."
        )
    else:
        prompt = f"Question: {question}\n\nGive a short, helpful answer."

    answer = generate_response(
        prompt=prompt,
        system_prompt=SYSTEM_PROMPT,
        mode="chat",
    )
    return {"answer": answer}


# ── NLP: Convert natural language → structured log data ──────────────────────

def nlp_to_structured(user_message: str) -> dict:
    """
    Converts natural language → structured daily log dict.
    Output uses API contract field names:
    pain, mood, flow, sleep, stress (string), exercise (string)

    cleaning.py will convert stress/exercise strings → numbers automatically.
    """
    # Few-shot example baked into the prompt for reliability
    few_shot = (
        'Example input: "I had bad cramps, pain was 7, felt really anxious and stressed, '
        'flow was heavy, barely slept 4 hours, didn\'t exercise today"\n'
        'Example output: {"pain": 7, "mood": "low", "flow": "heavy", '
        '"sleep": 4.0, "stress": "high", "exercise": "none"}\n\n'
    )

    prompt = (
        few_shot
        + f'Now extract from this message: "{user_message}"'
    )

    raw = generate_response(
        prompt=prompt,
        system_prompt=NLP_SYSTEM_PROMPT,
        mode="nlp",
    )

    clean = raw.strip().replace("```json", "").replace("```", "").strip()

    try:
        extracted = json.loads(clean)
        # Ensure all contract fields are present (null if missing)
        return {
            "pain":     extracted.get("pain"),
            "mood":     extracted.get("mood"),
            "flow":     extracted.get("flow"),
            "sleep":    extracted.get("sleep"),
            "stress":   extracted.get("stress"),
            "exercise": extracted.get("exercise"),
        }
    except json.JSONDecodeError:
        return {
            "pain":     None,
            "mood":     None,
            "flow":     None,
            "sleep":    None,
            "stress":   None,
            "exercise": None,
        }