"""
test_ml.py
Standalone test for all 3 layers of SYNCHER ML service.
No Django DB needed — uses mock data.
Run from inside ml_service/ folder:
  python test_ml.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

# Load .env manually
from dotenv import load_dotenv
load_dotenv()

print("=" * 60)
print("SYNCHER ML SERVICE — STANDALONE TEST")
print("=" * 60)

# ── Mock user data (same shape as db_fetcher would return) ────────────────────

MOCK_PROFILE = {
    "age": 24,
    "weight": 58,
    "avg_cycle_length": 28,
    "medical_condition": "pcos",
    "medical_notes": "missed periods in last 3 months",
    "pain": 3,
    "mood": "low",
    "flow": "medium",
}

MOCK_CYCLES = [
    {"start_date": "2024-10-01", "end_date": "2024-10-05"},
    {"start_date": "2024-10-30", "end_date": "2024-11-03"},
    {"start_date": "2024-11-27", "end_date": "2024-12-01"},
]

MOCK_CYCLE_LOGS = [
    {"date": "2024-12-01", "pain": 4, "mood": "low",      "flow": "heavy",
     "sleep": 6, "stress": "high", "exercise": "none",
     "medication": "yes", "medication_details": "ibuprofen", "hydration": "yes"},
    {"date": "2024-11-28", "pain": 3, "mood": "irritated", "flow": "medium",
     "sleep": 7, "stress": "medium", "exercise": "light",
     "medication": "no",  "medication_details": "",          "hydration": "yes"},
]

MOCK_DAILY_LOGS = [
    {"date": "2024-12-05", "sleep": 5, "stress": "high",   "exercise": "none",
     "food": "junk",  "medication": "no",  "medication_details": "",
     "routine_change": "no",  "routine_details": "",
     "white_discharge": "medium", "hydration": "yes",
     "symptoms": ["cramps", "fatigue"]},
    {"date": "2024-12-06", "sleep": 7, "stress": "medium", "exercise": "light",
     "food": "home",  "medication": "no",  "medication_details": "",
     "routine_change": "yes", "routine_details": "started new job, irregular meals",
     "white_discharge": "low",    "hydration": "yes",
     "symptoms": ["headache", "mood_swings"]},
]

MOCK_MY_HEALTH_RESPONSES = {
    "q1": "Persistent/recurrent",
    "q2": "Moderate",
    "q3": "Noticeable",
    "q4": "Moderate (5-8 kg)",
    "q5": "No",
    "q6": "Yes",
    "q7": "Mild",
    "q8": "Strong fatigue/crashes",
    "q9": "2-3 times/week",
    "q10": "Mixed",
}


# ─────────────────────────────────────────────────────────────────────────────
# TEST 1: Preprocessing (cleaning + encoding)
# ─────────────────────────────────────────────────────────────────────────────
print("\n[ TEST 1 ] Preprocessing — cleaning & encoding")
try:
    from preprocessing.cleaning import (
        clean_profile, clean_cycle_history,
        derive_cycle_lengths, clean_cycle_log, clean_daily_log,
    )
    from preprocessing.encoding import (
        encode_cycle_log, encode_daily_log, encode_medical_condition,
    )

    profile  = clean_profile(MOCK_PROFILE)
    cycles   = clean_cycle_history(MOCK_CYCLES)
    lengths  = derive_cycle_lengths(cycles)
    cond     = encode_medical_condition(profile["medical_condition"])
    enc_cl   = encode_cycle_log(clean_cycle_log(MOCK_CYCLE_LOGS[0]))
    enc_dl   = encode_daily_log(clean_daily_log(MOCK_DAILY_LOGS[0]))

    print(f"  ✓ Profile cleaned     : age={profile['age']}, weight={profile['weight']}")
    print(f"  ✓ Cycle lengths       : {lengths}")
    print(f"  ✓ Condition flags     : {cond}")
    print(f"  ✓ Cycle log encoded   : pain={enc_cl['pain']}, flow={enc_cl['flow']}, mood={enc_cl['mood']}")
    print(f"  ✓ Daily log encoded   : stress={enc_dl['stress']}, symptoms={enc_dl['symptom_count']}")
    print("  PASSED ✅")
except Exception as e:
    print(f"  FAILED ❌ — {e}")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 2: Feature extraction (33-feature vector)
# ─────────────────────────────────────────────────────────────────────────────
print("\n[ TEST 2 ] Feature Extraction — 33-feature vector")
try:
    from prediction.feature_extraction import build_feature_vector, build_lstm_sequence
    from config import FEATURE_COLUMNS

    fv = build_feature_vector(
        MOCK_PROFILE, MOCK_CYCLES,
        MOCK_CYCLE_LOGS, MOCK_DAILY_LOGS,
        my_health_responses=MOCK_MY_HEALTH_RESPONSES,
    )
    print(f"  ✓ Feature vector shape : {fv.shape}  (expected: ({len(FEATURE_COLUMNS)},))")
    print(f"  ✓ Sample values:")
    for name in ["age", "cycle_length_3", "cycle_variance", "stress", "has_pcos", "my_health_score"]:
        idx = FEATURE_COLUMNS.index(name)
        print(f"      {name:<22} = {fv[idx]:.2f}")

    seq = build_lstm_sequence(
        MOCK_PROFILE, MOCK_CYCLES,
        MOCK_CYCLE_LOGS, MOCK_DAILY_LOGS,
        my_health_responses=MOCK_MY_HEALTH_RESPONSES,
    )
    print(f"  ✓ LSTM sequence shape  : {seq.shape}  (expected: (1, 3, {len(FEATURE_COLUMNS)}))")
    print("  PASSED ✅")
except Exception as e:
    print(f"  FAILED ❌ — {e}")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 3: My Health Scorer (rule-based Q1-Q10)
# ─────────────────────────────────────────────────────────────────────────────
print("\n[ TEST 3 ] My Health Scorer — rule-based Q1-Q10")
try:
    from prediction.my_health_scorer import compute_my_health_score

    result = compute_my_health_score(MOCK_MY_HEALTH_RESPONSES)
    print(f"  ✓ Score        : {result['score']}/110")
    print(f"  ✓ Risk level   : {result['risk_level']}")
    print(f"  ✓ Pattern boost: +{result['pattern_boost']} {result.get('patterns_hit', [])}")
    print(f"  ✓ Breakdown    : {result['breakdown']}")
    print("  PASSED ✅")
except Exception as e:
    print(f"  FAILED ❌ — {e}")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 4: ML Prediction (statistical fallback — no model trained yet)
# ─────────────────────────────────────────────────────────────────────────────
print("\n[ TEST 4 ] ML Prediction — statistical fallback (no model trained yet)")
try:
    from prediction.predict import predict

    result = predict(
        MOCK_PROFILE, MOCK_CYCLES,
        MOCK_CYCLE_LOGS, MOCK_DAILY_LOGS,
        my_health_responses=MOCK_MY_HEALTH_RESPONSES,
    )
    print(f"  ✓ Next period date      : {result['next_period_date']}")
    print(f"  ✓ Ovulation window      : {result['ovulation_window']}")
    print(f"  ✓ Predicted length      : {result['predicted_length']} days")
    print(f"  ✓ Regularity score      : {result['cycle_regularity_score']}")
    print(f"  ✓ Confidence            : {result['confidence']}")
    print(f"  ✓ Model used            : {result.get('_model_used', 'N/A')}")
    print("  PASSED ✅")
except Exception as e:
    print(f"  FAILED ❌ — {e}")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 5: Insight Engine (analytical AI, no LLM)
# ─────────────────────────────────────────────────────────────────────────────
print("\n[ TEST 5 ] Insight Engine — analytical rule-based insights")
try:
    from prediction.feature_extraction import build_feature_vector
    from insights.insight_engine import generate_insights

    fv = build_feature_vector(
        MOCK_PROFILE, MOCK_CYCLES,
        MOCK_CYCLE_LOGS, MOCK_DAILY_LOGS,
        my_health_responses=MOCK_MY_HEALTH_RESPONSES,
    )
    insights = generate_insights(fv, MOCK_CYCLES, predicted_length=29, confidence=0.72)
    print(f"  ✓ Generated {len(insights)} insights:")
    for i, ins in enumerate(insights, 1):
        print(f"     {i}. {ins}")
    print("  PASSED ✅")
except Exception as e:
    print(f"  FAILED ❌ — {e}")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 6: Layer 1 — My Health AI Engine (Groq)
# ─────────────────────────────────────────────────────────────────────────────
print("\n[ TEST 6 ] LAYER 1 — My Health AI Engine (Groq llama-3.1-8b-instant)")
try:
    from prediction.my_health_scorer import compute_my_health_score
    from insights.my_health_engine import analyse_my_health
    from preprocessing.cleaning import clean_cycle_history, derive_cycle_lengths

    score_result   = compute_my_health_score(MOCK_MY_HEALTH_RESPONSES)
    cleaned_cycles = clean_cycle_history(MOCK_CYCLES)
    cycle_lengths  = derive_cycle_lengths(cleaned_cycles)

    analysis = analyse_my_health(
        score_result   = score_result,
        user_profile   = MOCK_PROFILE,
        raw_cycles     = MOCK_CYCLES,
        cycle_lengths  = cycle_lengths,
        avg_pain       = 3.5,
        avg_flow_str   = "medium",
    )
    print(f"  ✓ AI Analysis received ({len(analysis)} chars):")
    print(f"  ─────────────────────────────────────────")
    print(f"  {analysis[:500]}...")
    print("  PASSED ✅")
except Exception as e:
    print(f"  FAILED ❌ — {e}")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 7: Layer 2 — Dashboard Health Engine (Groq)
# ─────────────────────────────────────────────────────────────────────────────
print("\n[ TEST 7 ] LAYER 2 — Dashboard Health Engine (Groq llama-3.1-8b-instant)")
try:
    from insights.health_engine import generate_health_risk

    # Stage 1: onboarding only (no logs)
    ctx_stage1 = {
        "profile":       MOCK_PROFILE,
        "cycle_history": MOCK_CYCLES,
        "cycle_logs":    [],
        "daily_logs":    [],
        "my_health":     {},
    }
    result_s1 = generate_health_risk(ctx_stage1, risk_context="No cycle risk flags at this stage.", my_health_result={})
    print(f"  ✓ Stage 1 (onboarding only) — risk={result_s1['risk_level']}, seek_doctor={result_s1['seek_doctor']}")
    print(f"  {result_s1['risk_summary']}")

    print()

    # Stage 2: with logs
    ctx_stage2 = {
        "profile":       MOCK_PROFILE,
        "cycle_history": MOCK_CYCLES,
        "cycle_logs":    MOCK_CYCLE_LOGS,
        "daily_logs":    MOCK_DAILY_LOGS,
        "my_health":     {"score": 85, "risk_level": "High Risk"},
    }
    mh_result = {"score": 85, "risk_level": "High Risk", "insights": ["Androgen dominance pattern detected."]}
    result_s2 = generate_health_risk(ctx_stage2, risk_context="High stress detected. Irregular sleep pattern.", my_health_result=mh_result)
    print(f"  ✓ Stage 2 (with logs) — risk={result_s2['risk_level']}, seek_doctor={result_s2['seek_doctor']}")
    print(f"  {result_s2['risk_summary']}")
    print(f"  Suggestions:")
    for s in result_s2.get("suggestions", []):
        print(f"    • {s}")
    print("  PASSED ✅")
except Exception as e:
    print(f"  FAILED ❌ — {e}")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 8: Layer 3 — Chatbot RAG (Groq menstllama)
# ─────────────────────────────────────────────────────────────────────────────
print("\n[ TEST 8 ] LAYER 3 — Chatbot RAG (menstllama)")
try:
    from chatbot.rag import _retrieve_rag_context, answer_question, _build_system_prompt

    # Test retrieval without DB
    question  = "Why is my period delayed and I have cramps?"
    rag_ctx   = _retrieve_rag_context(question, top_k=3)
    chunks    = [line.lstrip("• ") for line in rag_ctx.splitlines() if line.startswith("•")]
    print(f"  ✓ RAG retrieved {len(chunks)} context chunks for: '{question}'")
    for i, c in enumerate(chunks, 1):
        print(f"     Chunk {i}: {c[:80]}...")

    # Test actual Groq call via answer_question
    # answer_question requires a real user_id for DB tool calls, so we call
    # groq_client directly with the retrieved context instead.
    from chatbot.groq_client import raw_completion
    system = _build_system_prompt(rag_ctx)
    messages = [
        {"role": "system",  "content": system},
        {"role": "user",    "content": question},
    ]
    response_msg = raw_completion(messages=messages, tools=None, max_tokens=256)
    answer = response_msg.get("content", "").strip()
    print(f"\n  ✓ menstllama answer ({len(answer)} chars):")
    print(f"  {answer[:400]}...")
    print("  PASSED ✅")
except Exception as e:
    print(f"  FAILED ❌ — {e}")


# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("TEST RUN COMPLETE")
print("=" * 60)
print("Tests 1-5 : No Groq needed (pure Python/ML)")
print("Tests 6-8 : Groq API calls (need GROQ_API_KEY in .env)")
print()
print("If Tests 1-5 pass  → preprocessing + ML pipeline is working")
print("If Tests 6-8 pass  → all 3 AI layers are working")
print("If Tests 6-8 fail  → check GROQ_API_KEY in .env")
print("=" * 60)