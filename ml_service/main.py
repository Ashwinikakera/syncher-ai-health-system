# ml_service/main.py

import warnings
warnings.filterwarnings("ignore")
import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

import sys
import tensorflow as tf
tf.get_logger().setLevel("ERROR")


# ── Shared test data ──────────────────────────────────────────────────────────

SAMPLE_CYCLES = [
    {"start_date": "2023-10-01", "cycle_length": 27},
    {"start_date": "2023-10-28", "cycle_length": 30},
    {"start_date": "2023-11-27", "cycle_length": 28},
    {"start_date": "2023-12-25", "cycle_length": 35},
    {"start_date": "2024-01-29", "cycle_length": 26},
]

SAMPLE_LOGS = [
    {"date": "2024-01-30", "pain": 7, "mood": "low",
     "flow": "heavy", "sleep": 5, "stress": "high",
     "exercise": "none"},
    {"date": "2024-01-31", "pain": 3, "mood": "medium",
     "flow": "medium", "sleep": 7, "stress": "medium",
     "exercise": "light"},
]

SAMPLE_CYCLES_DAY3 = [
    {"start_date": "2023-11-01", "cycle_length": 27},
    {"start_date": "2023-11-28", "cycle_length": 30},
    {"start_date": "2023-12-28", "cycle_length": 28},
    {"start_date": "2024-01-25", "cycle_length": 35},
    {"start_date": "2024-03-01", "cycle_length": 26},
]

SAMPLE_LOGS_DAY3 = [
    {"date": "2024-01-05", "pain": 8, "mood": "low",
     "flow": "heavy", "sleep": 5, "stress": "high",
     "exercise": "none"},
    {"date": "2024-01-06", "pain": 4, "mood": "medium",
     "flow": "medium", "sleep": 7, "stress": "medium",
     "exercise": "light"},
    {"date": "2024-01-07", "pain": 2, "mood": "high",
     "flow": "light", "sleep": 8, "stress": "low",
     "exercise": "moderate"},
]


# Environment check
def test_day1():
    print("\n" + "=" * 55)
    print("Environment Check")
    print("=" * 55)

    # Packages
    print("\n Checking Python packages...")
    packages = {
        "pandas":   "pandas",
        "numpy":    "numpy",
        "sklearn":  "scikit-learn",
        "requests": "requests",
        "joblib":   "joblib",
        "groq":     "groq",
    }
    all_ok = True
    for imp, pip in packages.items():
        try:
            __import__(imp)
            print(f"  ✅ {pip}")
        except ImportError:
            print(f"  ❌ {pip}")
            all_ok = False

    if not all_ok:
        print("  ⚠️  Fix missing packages before continuing.")
        sys.exit(1)

    # Groq
    print("\n🤖 Checking Groq API...")
    from ml_service.chatbot.groq_client import check_groq_running, list_available_models

    if not check_groq_running():
        print("  ❌ Groq API not reachable — check GROQ_API_KEY in config.py")
        sys.exit(1)

    models = list_available_models()
    print(f"  ✅ Groq API is reachable")
    print(f"  📋 Model in use: {models[0]}")

    print("\n complete — environment ready\n")



# Preprocessing

def test_day2():
    print("=" * 55)
    print(" Preprocessing Test")
    print("=" * 55)
 
    from ml_service.preprocessing.cleaning import clean_cycle_data, clean_daily_logs
    from ml_service.preprocessing.encoding import get_feature_vector
 
    sample_cycles = [
        {"start_date": "2024-01-01", "cycle_length": 28},
        {"start_date": "2024-01-29", "cycle_length": None},
        {"start_date": "2024-02-26", "cycle_length": 30},
    ]
 
    # Contract field names: pain, mood, flow, sleep, stress, exercise
    sample_logs = [
        {"date": "2024-01-05", "pain": 6, "mood": "low",
         "flow": "heavy", "sleep": 7, "stress": "medium",
         "exercise": "light"},
        {"date": "2024-01-06", "pain": None, "mood": "high",
         "flow": "medium", "sleep": None, "stress": "low",
         "exercise": "none"},
    ]
 
    cycle_df = clean_cycle_data(sample_cycles)
    print("\nCleaned cycles:")
    print(cycle_df[["cycle_length", "cycle_length_normalized", "cycle_variance"]])
 
    log_df = clean_daily_logs(sample_logs)
 
    # Show contract field names — stress and exercise converted to numeric
    print("\nCleaned logs (contract field names):")
    contract_cols = [c for c in ["date", "pain", "mood", "flow", "sleep", "stress", "exercise"]
                     if c in log_df.columns]
    print(log_df[contract_cols].to_string(index=False))
 
    # Show string → number conversion clearly
    print("\n  stress  (contract string → ML number):",
          list(zip([s["stress"] for s in sample_logs], log_df["stress"].tolist())))
    print("  exercise (contract string → ML number):",
          list(zip([s["exercise"] for s in sample_logs], log_df["exercise"].tolist())))
 
    feature_df = get_feature_vector(log_df)
    print("\nFeature vector for ML (contract names kept):")
    print(feature_df)
 
    print("\nDay 2 complete - preprocessing working\n")


#Feature Extraction
def test_day3():
    print("=" * 55)
    print(" Feature Extraction Test")
    print("=" * 55)

    from ml_service.prediction.feature_extraction import (
        extract_cycle_features, extract_symptom_features, build_model_input,
    )

    cycle_feat = extract_cycle_features(SAMPLE_CYCLES_DAY3)
    print("\n📊 Cycle Features:")
    for k, v in cycle_feat.items():
        print(f"  {k:30s}: {v}")

    symptom_feat = extract_symptom_features(SAMPLE_LOGS_DAY3)
    print("\n🩺 Symptom Features:")
    for k, v in symptom_feat.items():
        print(f"  {k:30s}: {v}")

    combined = build_model_input(SAMPLE_CYCLES_DAY3, SAMPLE_LOGS_DAY3)
    print(f"\n✅ Combined input keys ({len(combined)}): {list(combined.keys())}")

    print("\n complete — feature extraction working\n")



# Regression Prediction

def test_day4():
    print("=" * 55)
    print(" Regression Prediction Test")
    print("=" * 55)

    from ml_service.prediction.predict import predict

    user_data = {"cycle_records": SAMPLE_CYCLES, "log_records": SAMPLE_LOGS}
    result = predict(user_data)

    print(f"\n  📅 Next Period Date     : {result['next_period_date']}")
    print(f"  🌸 Ovulation Window     : {result['ovulation_window']}")
    print(f"  📊 Regularity Score     : {result['cycle_regularity_score']}")
    print(f"  📏 Predicted Length     : {result['predicted_cycle_length']} days")
    print(f"  🎯 Confidence           : {result['confidence']}")
    print(f"\n  💡 Insights:")
    for i in result["insights"]:
        print(f"     - {i}")

    print("\n complete — prediction engine working\n")



# LSTM Upgrade

def test_day5():
    print("=" * 55)
    print(" LSTM Prediction Test")
    print("=" * 55)

    from ml_service.prediction.predict import predict

    cycles_day5 = SAMPLE_CYCLES + [
        {"cycle_start_date": "2024-02-24", "cycle_length": 35, "period_length": 6},
    ]
    user_data = {"cycle_records": cycles_day5, "log_records": SAMPLE_LOGS}
    result = predict(user_data)

    print(f"\n  📅 Next Period Date      : {result['next_period_date']}")
    print(f"  🌸 Ovulation Window      : {result['ovulation_window']}")
    print(f"  📊 Regularity Score      : {result['cycle_regularity_score']}")
    print(f"  📏 Predicted Length      : {result['predicted_cycle_length']} days")
    print(f"  🎯 Confidence            : {result['confidence']}")
    print(f"  🤖 Model Used            : {result['model_used']}")
    print(f"\n  📈 Model Comparison:")
    print(f"     Regression            : {result['model_comparison']['regression']} days")
    print(f"     LSTM                  : {result['model_comparison']['lstm']} days")
    print(f"     Models agree          : {result['model_comparison']['agreement']}")
    print(f"\n  💡 Insights:")
    for i in result["insights"]:
        print(f"     - {i}")

    print("\n complete — LSTM working\n")



# RAG Chatbot
def test_day6():
    print("=" * 55)
    print(" RAG Chatbot Test")
    print("=" * 55)

    from ml_service.chatbot.rag import rag_chat, nlp_to_structured

    # Use contract field names exactly
    user_data = {
        "cycle_records": [
            {"start_date": "2023-10-01", "cycle_length": 27},
            {"start_date": "2023-10-28", "cycle_length": 30},
            {"start_date": "2023-11-27", "cycle_length": 28},
            {"start_date": "2023-12-25", "cycle_length": 35},
            {"start_date": "2024-01-29", "cycle_length": 26},
        ],
        "log_records": [
            {"date": "2024-01-30", "pain": 7, "mood": "low",
             "flow": "heavy", "sleep": 5, "stress": "high",
             "exercise": "none"},
            {"date": "2024-01-31", "pain": 3, "mood": "medium",
             "flow": "medium", "sleep": 7, "stress": "medium",
             "exercise": "light"},
        ],
    }

    # Test 1: uses "question" not "query" — matches contract
    print("\n🧪 Test 1: Personalized query")
    result1 = rag_chat(
        question="Why is my period late?",
        user_data=user_data,
    )
    print(f"  Answer: {result1['answer']}")

    # Test 2: General
    print("\n🧪 Test 2: General question")
    result2 = rag_chat(
        question="What foods help with period cramps?",
        user_data={},
    )
    print(f"  Answer: {result2['answer']}")

    # Test 3: NLP conversion using contract field names
    print("\nTest 3: NLP conversion")
    structured = nlp_to_structured(
        "I had terrible cramps today, like an 8 out of 10 pain, "
        "felt really anxious and stressed, flow was heavy, "
        "only slept 4 hours, didn't exercise at all"
    )
    print(f"  Extracted (contract format): {structured}")
# Expected:
# {
#   "pain": 8,
#   "mood": "low",
#   "flow": "heavy",
#   "sleep": 4.0,
#   "stress": "high",      ← string, cleaning.py converts to 8
#   "exercise": "none"     ← string, cleaning.py converts to 0
# }
 
# To verify cleaning.py correctly converts to internal format:
    from ml_service.preprocessing.cleaning import clean_daily_logs
    cleaned = clean_daily_logs([{**structured, "date": "2024-01-05"}])
    print(f"  After cleaning.py         : stress={cleaned['stress'].iloc[0]}, "
        f"exercise={cleaned['exercise'].iloc[0]}")
# Expected: stress=8, exercise=0

def test_day7():
    print("=" * 55)
    print(" Day 7 — Optimization + Retraining")
    print("=" * 55)
 
    # ── Task 1: Model optimization ────────────────────────────────────────────
    print("\n📊 Task 1: Model optimization (Ridge CV)")
    from ml_service.models.optimize_models import run_optimization_test
    run_optimization_test()
 
    # ── Task 2: Chatbot response quality ──────────────────────────────────────
    print("\n🤖 Task 2: Optimized chatbot responses")
    from ml_service.chatbot.rag import rag_chat, nlp_to_structured
 
    user_data = {
        "cycle_records": [
            {"start_date": "2023-10-01", "cycle_length": 27},
            {"start_date": "2023-10-28", "cycle_length": 30},
            {"start_date": "2023-11-27", "cycle_length": 28},
            {"start_date": "2023-12-25", "cycle_length": 35},
            {"start_date": "2024-01-29", "cycle_length": 26},
        ],
        "log_records": [
            {"date": "2024-01-30", "pain": 7, "mood": "low",
             "flow": "heavy", "sleep": 5, "stress": "high", "exercise": "none"},
        ],
    }
 
    result = rag_chat("Why is my period late?", user_data)
    print(f"\n  Q: Why is my period late?")
    print(f"  A: {result['answer']}")
 
    structured = nlp_to_structured(
    "I had terrible cramps, pain was 8 out of 10, "
    "felt very anxious and highly stressed, flow was heavy, "
    "only slept 4 hours, I did not exercise at all today"
)
    print(f"\n  NLP extraction: {structured}")
 
    # Task 3: Retraining trigger
    print("\n🔄 Task 3: Retraining trigger")
    from ml_service.retrain import trigger_retrain

    result = trigger_retrain()
    print(f"  Status       : {result['status']}")
    print(f"  Reason       : {result['reason']}")
    print(f"  Samples used : {result['samples_used']}")
    print(f"  Timestamp    : {result['timestamp']}")
    print("\nRetraining trigger working\n")
 
    print("=" * 55)
    print("   Day 7 COMPLETE")
    print("=" * 55)

 

# ENTRY POINT
if __name__ == "__main__":
    test_day1()
    test_day2()
    test_day3()
    test_day4()
    test_day5()
    test_day6()
    test_day7()

    print("=" * 55)
    print("   ALL COMPLETE — SYNCHER Dev3 Sprint Done!")
    print("=" * 55)