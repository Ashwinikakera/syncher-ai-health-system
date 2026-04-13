"""
ml_service/chatbot/rag.py

ARCHITECTURE: Chatbot — RAG + LLM Agent
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This is a full LLM Agent, not a simple Q&A pipeline.

Agent capabilities:
  1. MEMORY       — Maintains per-user conversation history (in-memory,
                    keyed by user_id). The full history is passed to the
                    model on every turn so it can refer back to earlier
                    parts of the conversation.

  2. TOOLS        — The agent can call internal tools to look up live
                    user data mid-conversation:
                      • get_cycle_summary   → fetch & summarise cycle history
                      • get_daily_log_summary → fetch & summarise recent logs
                      • get_my_health_score   → fetch My Health score
                      • get_next_period_date  → call predict() for latest date
                    Tools are defined as Groq tool-call schemas. The agent
                    decides when to call them based on the question.

  3. RAG           — Before the first agent turn, relevant passages from the
                    static knowledge base are injected as a system context
                    block. This grounds the agent in domain knowledge without
                    polluting every tool call.

  4. AGENT LOOP   — Supports multi-step reasoning:
                    LLM → [tool_call] → tool result → LLM → answer
                    Loop capped at MAX_TOOL_ROUNDS to prevent runaway calls.

Model: menstllama via groq_client.py
Called by: main.py → /ml/chat
"""

import json
import logging
from typing import Optional
from datetime import date

from data.db_fetcher import (
    fetch_full_user_context,
    fetch_cycle_history,
    fetch_recent_daily_logs,
    fetch_recent_cycle_logs,
    fetch_my_health_responses,
)
from chatbot.groq_client import raw_completion
from preprocessing.cleaning import clean_cycle_history, derive_cycle_lengths
from config import GROQ_CHATBOT_MODEL

logger = logging.getLogger(__name__)

# ─── Constants ────────────────────────────────────────────────────────────────
MAX_TOOL_ROUNDS   = 3      # max LLM→tool→LLM iterations per message
MAX_HISTORY_TURNS = 10     # max past (user+assistant) pairs kept in memory
MAX_ANSWER_TOKENS = 512

# ─── Per-user conversation memory ────────────────────────────────────────────
# { user_id: [ {"role": "user"|"assistant", "content": str}, ... ] }
_conversation_memory: dict[int, list[dict]] = {}


def clear_history(user_id: int):
    """Clear conversation history for a user (e.g. on logout)."""
    _conversation_memory.pop(user_id, None)


def _get_history(user_id: int) -> list[dict]:
    return _conversation_memory.get(user_id, [])


def _append_history(user_id: int, role: str, content: str):
    history = _conversation_memory.setdefault(user_id, [])
    history.append({"role": role, "content": content})
    # Trim to last MAX_HISTORY_TURNS pairs = 2*N messages
    if len(history) > MAX_HISTORY_TURNS * 2:
        _conversation_memory[user_id] = history[-(MAX_HISTORY_TURNS * 2):]


# ─── Static knowledge base (RAG retrieval) ───────────────────────────────────
_KNOWLEDGE_BASE: list[dict] = [
    {
        "keywords": ["late", "delayed", "missed", "period late"],
        "text": "Periods can be delayed by stress, significant weight changes, thyroid disorders, PCOS, pregnancy, or extreme exercise. A delay of up to 7 days is common. Consistently late periods warrant medical evaluation.",
    },
    {
        "keywords": ["cramps", "pain", "dysmenorrhea"],
        "text": "Menstrual cramps (dysmenorrhea) are caused by prostaglandins. Severe or worsening cramps could indicate endometriosis or adenomyosis. Heat therapy, anti-inflammatory foods, and NSAIDs can provide relief.",
    },
    {
        "keywords": ["ovulation", "fertile", "fertility", "ovulate"],
        "text": "Ovulation typically occurs 14 days before the next period. The fertile window is 5 days before ovulation plus ovulation day. Signs include cervical mucus changes, mild cramping (mittelschmerz), and a slight temperature rise.",
    },
    {
        "keywords": ["pcos", "pcod", "polycystic"],
        "text": "PCOS is a hormonal disorder causing irregular cycles, excess androgens, and sometimes ovarian cysts. Lifestyle changes (diet, exercise), and medical management (Metformin, hormonal therapy) are common treatments.",
    },
    {
        "keywords": ["heavy flow", "menorrhagia", "heavy bleeding"],
        "text": "Heavy menstrual flow (menorrhagia) is defined as soaking a pad/tampon every hour for several hours. Causes include fibroids, polyps, hormone imbalance, or clotting disorders. Medical evaluation is recommended.",
    },
    {
        "keywords": ["mood", "mood swings", "pms", "pmdd", "irritable"],
        "text": "PMS symptoms (mood swings, irritability, bloating) occur in the luteal phase. PMDD is a severe form. Calcium, magnesium, and B6 supplements, along with regular exercise, can reduce symptoms.",
    },
    {
        "keywords": ["thyroid", "hypothyroid", "hyperthyroid"],
        "text": "Thyroid disorders significantly affect menstrual cycles. Hypothyroidism often causes heavy, irregular periods; hyperthyroidism can cause light or absent periods. TSH testing is recommended if cycle irregularity persists.",
    },
    {
        "keywords": ["stress", "anxiety", "cortisol"],
        "text": "Chronic stress elevates cortisol, which can suppress GnRH and delay ovulation, causing irregular cycles. Stress management (yoga, mindfulness, adequate sleep) supports hormonal balance.",
    },
    {
        "keywords": ["discharge", "white discharge", "leucorrhoea"],
        "text": "Vaginal discharge varies throughout the cycle. Clear/white discharge is normal; it becomes stretchy near ovulation. Unusual colour, smell, or consistency may indicate infection and warrants a medical check.",
    },
    {
        "keywords": ["regularity", "irregular", "cycle length"],
        "text": "A normal cycle is 21–35 days. Cycles consistently outside this range, or varying by more than 7–9 days cycle-to-cycle, are considered irregular and may have hormonal causes.",
    },
    {
        "keywords": ["sleep", "insomnia", "rest"],
        "text": "Poor sleep disrupts melatonin and cortisol rhythms, which can affect LH/FSH secretion and delay ovulation. 7–9 hours of consistent sleep supports a healthy cycle.",
    },
    {
        "keywords": ["exercise", "workout", "physical activity"],
        "text": "Moderate exercise (3–4 times/week) improves insulin sensitivity and reduces cycle irregularity. Excessive high-intensity training can suppress ovulation through hypothalamic amenorrhea.",
    },
    {
        "keywords": ["diet", "food", "nutrition", "eat"],
        "text": "A diet rich in whole grains, leafy greens, healthy fats, and lean protein supports hormonal balance. High sugar and processed food intake can worsen PCOS symptoms and increase inflammation.",
    },
    {
        "keywords": ["next period", "when period", "period date", "period coming"],
        "text": "Next period predictions are based on cycle history using both statistical and ML models. The prediction improves with more tracked cycles.",
    },
    # ── Food & nutrition knowledge base ───────────────────────────────────────
    {
        "keywords": ["food", "eat", "diet", "nutrition", "what to eat", "foods for period"],
        "text": "For menstrual health: iron-rich foods (spinach, lentils, tofu) replace blood lost during periods. Anti-inflammatory foods (turmeric, ginger, berries, fatty fish) reduce cramps and inflammation. Magnesium-rich foods (dark chocolate, almonds, leafy greens) ease PMS and mood swings.",
    },
    {
        "keywords": ["pcos food", "pcod food", "pcos diet", "hormonal food", "hormone balance food"],
        "text": "For PCOS/PCOD: low-GI foods (oats, lentils, brown rice, berries) stabilise insulin. Spearmint tea reduces androgen levels. Flaxseeds regulate oestrogen. Cinnamon improves insulin sensitivity. Avoid high-sugar, processed, and refined carb foods which worsen PCOS symptoms.",
    },
    {
        "keywords": ["cramp food", "period pain food", "pain relief food", "dysmenorrhea food"],
        "text": "For period cramps: ginger tea is a natural anti-inflammatory comparable to ibuprofen in studies. Turmeric with black pepper reduces prostaglandins. Omega-3 rich foods (salmon, walnuts, chia seeds) reduce inflammatory cramps. Avoid caffeine and salty foods which worsen cramps.",
    },
    {
        "keywords": ["heavy flow food", "heavy period food", "bleeding food", "menorrhagia food"],
        "text": "For heavy flow: iron-rich foods prevent anaemia (spinach, red meat, lentils, pumpkin seeds). Vitamin C foods (oranges, bell peppers) boost iron absorption. Vitamin K foods (kale, broccoli) support blood clotting. Avoid alcohol and blood thinners like excess ginger during heavy flow.",
    },
    {
        "keywords": ["stress food", "anxiety food", "mood food", "pms food", "pmdd food"],
        "text": "For stress and PMS: magnesium-rich foods (dark chocolate 70%+, spinach, almonds) reduce cortisol. Chamomile tea calms anxiety. Tryptophan foods (banana, oats, turkey) boost serotonin. Calcium-rich foods (yoghurt, milk, broccoli) significantly reduce PMS symptoms.",
    },
    {
        "keywords": ["sleep food", "insomnia food", "sleep better food"],
        "text": "For better sleep: tryptophan foods (banana, warm milk, almonds, oats) promote melatonin production. Chamomile or ashwagandha tea before bed reduces cortisol. Avoid caffeine after 2pm and heavy meals 2 hours before sleep.",
    },
    {
        "keywords": ["thyroid food", "hypothyroid food", "hyperthyroid food"],
        "text": "For thyroid health: selenium-rich foods (Brazil nuts — just 2/day, tuna, eggs) support T3/T4 conversion. Iodine foods (seaweed, fish, dairy) are essential for thyroid hormone production. Avoid raw cruciferous vegetables in excess if hypothyroid — cooking neutralises goitrogens.",
    },
    {
        "keywords": ["irregular period food", "cycle food", "regulate cycle food"],
        "text": "To regulate cycles: flaxseeds support oestrogen balance. Ashwagandha reduces cortisol which disrupts cycles. Vitamin B6 foods (bananas, potatoes, chickpeas) support progesterone. Zinc-rich foods (pumpkin seeds, chickpeas, cashews) regulate hormones and reduce acne.",
    },
]


def _retrieve_rag_context(question: str, top_k: int = 3) -> str:
    """
    Keyword-based retrieval. Returns a formatted context string.
    Production upgrade path: replace with sentence-transformer cosine similarity.
    """
    q = question.lower()
    scored = [
        (sum(1 for kw in entry["keywords"] if kw in q), entry["text"])
        for entry in _KNOWLEDGE_BASE
    ]
    scored = [(s, t) for s, t in scored if s > 0]
    scored.sort(key=lambda x: x[0], reverse=True)
    top = [t for _, t in scored[:top_k]]

    if not top:
        return ""
    return "HEALTH KNOWLEDGE BASE:\n" + "\n".join(f"• {t}" for t in top)


# ─── Agent tools ─────────────────────────────────────────────────────────────
# Defined as Groq tool-call schema (OpenAI-compatible function calling).

_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_cycle_summary",
            "description": (
                "Fetch the user's recent cycle history and return a plain-text summary "
                "including average cycle length, last period date, and regularity."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_daily_log_summary",
            "description": (
                "Fetch the user's recent daily logs and return a plain-text summary "
                "of sleep, stress, exercise, food, and symptoms over the last 7 days."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_my_health_score",
            "description": (
                "Fetch the user's My Health questionnaire score and risk level. "
                "Use when the user asks about their PCOS risk, health score, or metabolic health."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_next_period_date",
            "description": (
                "Get the predicted next period date and ovulation window for the user. "
                "Use when the user asks when their next period is coming, fertile window, or ovulation."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
]


# ─── Tool executors ───────────────────────────────────────────────────────────

def _tool_get_cycle_summary(user_id: int) -> str:
    try:
        raw_cycles = fetch_cycle_history(user_id, limit=6)
        if not raw_cycles:
            return "No cycle history found for this user."
        cleaned = clean_cycle_history(raw_cycles)
        lengths = derive_cycle_lengths(cleaned)
        last = cleaned[-1]["start_date"].isoformat() if cleaned else "unknown"
        avg  = round(sum(lengths) / len(lengths), 1) if lengths else "unknown"
        variance = round(
            sum((x - float(avg)) ** 2 for x in lengths) / len(lengths), 1
        ) if len(lengths) > 1 else 0

        regularity = (
            "Very regular" if variance < 4
            else "Mildly irregular" if variance < 16
            else "Significantly irregular"
        )
        return (
            f"Cycle history: {len(cleaned)} cycles tracked. "
            f"Last period started: {last}. "
            f"Average cycle length: {avg} days. "
            f"Cycle variance: {variance}. "
            f"Regularity: {regularity}."
        )
    except Exception as exc:
        logger.warning("Tool get_cycle_summary failed: %s", exc)
        return "Could not retrieve cycle history."


def _tool_get_daily_log_summary(user_id: int) -> str:
    try:
        logs = fetch_recent_daily_logs(user_id, limit=7)
        if not logs:
            return "No daily logs found for this user in the last 7 days."

        sleep_vals = [float(l.get("sleep") or 0) for l in logs]
        avg_sleep  = round(sum(sleep_vals) / len(sleep_vals), 1)

        stress_vals = [str(l.get("stress", "none")).lower() for l in logs]
        high_stress = sum(1 for s in stress_vals if s in ("high", "medium"))

        exercise_vals = [str(l.get("exercise", "none")).lower() for l in logs]
        active_days   = sum(1 for e in exercise_vals if e != "none")

        food_vals = [str(l.get("food", "home")).lower() for l in logs]
        junk_days = sum(1 for f in food_vals if f == "junk")

        all_symptoms = []
        for l in logs:
            s = l.get("symptoms")
            if isinstance(s, list):
                all_symptoms.extend(s)
            elif isinstance(s, str) and s:
                all_symptoms.extend(s.split(","))
        symptom_summary = (
            ", ".join(set(x.strip() for x in all_symptoms if x.strip()))
            or "none"
        )

        return (
            f"Last 7 daily logs summary — "
            f"Avg sleep: {avg_sleep} hrs/night. "
            f"High/medium stress days: {high_stress}/7. "
            f"Active exercise days: {active_days}/7. "
            f"Days with junk food: {junk_days}/7. "
            f"Reported symptoms: {symptom_summary}."
        )
    except Exception as exc:
        logger.warning("Tool get_daily_log_summary failed: %s", exc)
        return "Could not retrieve daily log summary."


def _tool_get_my_health_score(user_id: int) -> str:
    try:
        mh = fetch_my_health_responses(user_id)
        if not mh:
            return "User has not completed the My Health questionnaire yet."
        score     = mh.get("score", "N/A")
        risk      = mh.get("risk_level", "N/A")
        insights  = mh.get("insights", [])
        top_2     = "; ".join(insights[:2]) if insights else "No insights available."
        return (
            f"My Health score: {score}/110. Risk level: {risk}. "
            f"Top insights: {top_2}"
        )
    except Exception as exc:
        logger.warning("Tool get_my_health_score failed: %s", exc)
        return "Could not retrieve My Health score."


def _tool_get_next_period_date(user_id: int) -> str:
    try:
        from data.db_fetcher import (
            fetch_user_profile, fetch_cycle_history,
            fetch_recent_cycle_logs, fetch_recent_daily_logs,
            fetch_my_health_responses,
        )
        from prediction.predict import predict

        profile    = fetch_user_profile(user_id)    or {}
        cycles     = fetch_cycle_history(user_id)
        clogs      = fetch_recent_cycle_logs(user_id)
        dlogs      = fetch_recent_daily_logs(user_id)
        mh         = fetch_my_health_responses(user_id)

        result = predict(profile, cycles, clogs, dlogs, mh)
        next_date = result.get("next_period_date", "unknown")
        ov_window = result.get("ovulation_window", [])
        conf      = result.get("confidence", 0)
        length    = result.get("predicted_length", "?")

        ov_str = f"{ov_window[0]} to {ov_window[1]}" if len(ov_window) == 2 else "unknown"

        return (
            f"Predicted next period: {next_date} "
            f"(predicted cycle length: {length} days, confidence: {int(conf * 100)}%). "
            f"Estimated ovulation window: {ov_str}."
        )
    except Exception as exc:
        logger.warning("Tool get_next_period_date failed: %s", exc)
        return "Could not calculate next period date."


_TOOL_EXECUTORS = {
    "get_cycle_summary":      _tool_get_cycle_summary,
    "get_daily_log_summary":  _tool_get_daily_log_summary,
    "get_my_health_score":    _tool_get_my_health_score,
    "get_next_period_date":   _tool_get_next_period_date,
}


# ─── System prompt ────────────────────────────────────────────────────────────

def _get_food_suggestions_for_condition(condition: str, risk_flags: list[str]) -> str:
    """
    Returns a targeted food suggestion block based on user's condition
    and active risk flags. Injected into system prompt.
    """
    foods = []
    condition = condition.lower() if condition else "none"

    if condition in ("pcos", "pcod"):
        foods.append("PCOS/PCOD foods: spearmint tea (reduces androgens), flaxseeds (balances oestrogen), oats/lentils (low-GI for insulin), cinnamon (improves insulin sensitivity), berries (antioxidants).")
    if "HIGH_PAIN" in risk_flags or "MODERATE_PAIN" in risk_flags:
        foods.append("Pain-relief foods: ginger tea (anti-inflammatory), turmeric with black pepper (reduces prostaglandins), omega-3 foods like salmon or walnuts (reduce cramp severity).")
    if "HEAVY_FLOW" in risk_flags:
        foods.append("Heavy flow foods: spinach, lentils, pumpkin seeds (iron to prevent anaemia), oranges or bell peppers (vitamin C boosts iron absorption), kale/broccoli (vitamin K).")
    if "HIGH_STRESS" in risk_flags:
        foods.append("Stress-relief foods: dark chocolate 70%+ (magnesium, cortisol reduction), chamomile tea (calming), bananas (tryptophan for serotonin), almonds (magnesium + B2).")
    if "POOR_SLEEP" in risk_flags:
        foods.append("Sleep-support foods: warm milk or almonds before bed (tryptophan → melatonin), chamomile tea, oats (complex carbs stabilise blood sugar overnight).")
    if condition == "thyroid":
        foods.append("Thyroid foods: 2 Brazil nuts/day (selenium for T3/T4 conversion), fish or eggs (iodine), avoid raw cabbage/kale in excess if hypothyroid.")
    if not foods:
        foods.append("General hormonal balance foods: leafy greens (iron, magnesium), flaxseeds (oestrogen balance), ginger tea (anti-inflammatory), berries (antioxidants), zinc-rich foods like pumpkin seeds.")

    return "\n".join(foods)


def _build_system_prompt(rag_context: str, condition: str = "none", risk_flags: list[str] = None) -> str:
    food_block = _get_food_suggestions_for_condition(condition, risk_flags or [])
    base = (
        "You are SYNCHER, a compassionate and knowledgeable AI health assistant "
        "specialising in menstrual health and women's wellbeing.\n\n"
        "You have access to the user's personal health data through tools. "
        "Use tools proactively when the question requires real user data — "
        "do not guess or make up numbers.\n\n"
        "Guidelines:\n"
        "• Be warm, non-judgmental, and evidence-based.\n"
        "• Personalise answers using tool results when relevant.\n"
        "• Never diagnose. Recommend consulting a doctor for medical concerns.\n"
        "• Keep answers concise (under 200 words) unless detail is needed.\n"
        "• You remember the current conversation — refer back to earlier messages when helpful.\n"
        "• If you don't know something, say so honestly.\n\n"
        "FOOD SUGGESTION RULE — IMPORTANT:\n"
        "For EVERY health problem, symptom, or condition the user asks about:\n"
        "1. First answer their question fully (cause, explanation, what helps).\n"
        "2. Then ALWAYS end your response with a 'Foods that can help:' section.\n"
        "3. List 3-4 specific foods with ONE line each explaining why it helps their issue.\n"
        "4. Make food suggestions specific to their condition, not generic.\n\n"
        f"USER'S CONDITION-SPECIFIC FOOD GUIDANCE:\n{food_block}\n"
    )
    if rag_context:
        base += f"\n{rag_context}\n"
    return base


# ─── Agent loop ───────────────────────────────────────────────────────────────

def answer_question(user_id: int, question: str) -> str:
    """
    Full RAG + LLM Agent pipeline:

    1.  Retrieve RAG context (static knowledge base).
    2.  Fetch user condition for personalised food suggestions.
    3.  Build message list: system + conversation history + new user message.
    4.  Call LLM with tools defined.
    5.  If model requests a tool call → execute tool → append result → loop.
    6.  Return final text answer (always includes food suggestions for health questions).
    7.  Persist turn (user + assistant) to conversation memory.

    Called by: Django chatbot_app/services.py
    """
    if not question or not question.strip():
        return "Please ask me a question about your menstrual health."

    # Step 1: RAG retrieval
    rag_context = _retrieve_rag_context(question)

    # Step 2: Fetch user condition for personalised food suggestions
    condition  = "none"
    risk_flags = []
    try:
        from data.db_fetcher import fetch_user_profile
        profile = fetch_user_profile(user_id)
        if profile:
            condition = str(profile.get("medical_condition", "none")).lower()
    except Exception:
        pass   # non-fatal — fallback to generic food suggestions

    # Step 3: Build messages
    system_prompt = _build_system_prompt(rag_context, condition, risk_flags)
    history       = _get_history(user_id)

    messages: list[dict] = [
        {"role": "system", "content": system_prompt},
        *history,
        {"role": "user", "content": question},
    ]

    # Step 3–4: Agent loop
    final_answer = ""
    for round_num in range(MAX_TOOL_ROUNDS + 1):
        response_msg = raw_completion(
            messages   = messages,
            tools      = _TOOLS,
            max_tokens = MAX_ANSWER_TOKENS,
        )

        # raw_completion itself failed (API error) — answer from RAG only
        if response_msg.get("content", "").startswith("I'm sorry, I couldn't"):
            # FIX: Instead of returning the error fallback, retry without tools
            # so the model answers from RAG knowledge base alone.
            fallback_msg = raw_completion(
                messages   = messages,
                tools      = None,    # no tools — pure RAG + knowledge answer
                max_tokens = MAX_ANSWER_TOKENS,
            )
            final_answer = fallback_msg.get("content", "").strip()
            if not final_answer:
                final_answer = (
                    "I'm sorry, I'm having trouble connecting right now. "
                    "Based on general knowledge: menstrual cramps are caused by "
                    "prostaglandins. Heat therapy and anti-inflammatory foods can help. "
                    "If pain is severe, please consult a doctor."
                )
            break

        # No tool call → we have the final answer
        if not response_msg.get("tool_calls"):
            final_answer = response_msg.get("content", "").strip()
            break

        # Tool call(s) requested
        # Append assistant message (with tool_calls) to messages.
        # FIX: Groq requires each tool_call to have "type": "function".
        # raw_completion returns tool_calls without this field, causing 400.
        tool_calls_with_type = [
            {
                "id":       tc["id"],
                "type":     "function",          # ← required by Groq API
                "function": tc["function"],
            }
            for tc in response_msg["tool_calls"]
        ]
        messages.append({
            "role":       "assistant",
            "content":    response_msg.get("content") or "",
            "tool_calls": tool_calls_with_type,
        })

        # Execute each tool and append results
        for tc in tool_calls_with_type:
            tool_name = tc["function"]["name"]
            tool_id   = tc["id"]
            executor  = _TOOL_EXECUTORS.get(tool_name)

            if executor:
                logger.info("Agent calling tool '%s' for user %d", tool_name, user_id)
                try:
                    tool_result = executor(user_id)
                except Exception as exc:
                    tool_result = f"Tool error: {exc}"
            else:
                tool_result = f"Unknown tool: {tool_name}"

            messages.append({
                "role":         "tool",
                "tool_call_id": tool_id,
                "content":      tool_result,
            })

        if round_num == MAX_TOOL_ROUNDS:
            # Force a final answer without tools
            messages.append({
                "role":    "user",
                "content": "Please now give me your final answer based on the tool results above.",
            })
            final_msg = raw_completion(messages=messages, tools=None, max_tokens=MAX_ANSWER_TOKENS)
            final_answer = final_msg.get("content", "").strip()
            break

    if not final_answer:
        final_answer = "I'm sorry, I wasn't able to generate an answer. Please try again."

    # Step 6: Persist to memory
    _append_history(user_id, "user",      question)
    _append_history(user_id, "assistant", final_answer)

    return final_answer