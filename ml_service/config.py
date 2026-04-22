"""
ml_service/config.py
Central configuration for SYNCHER ML Service.
"""

import os
from pathlib import Path

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
SAVED_MODELS_DIR = BASE_DIR / "saved_models"
SAVED_MODELS_DIR.mkdir(exist_ok=True)

# ─── Model file paths ─────────────────────────────────────────────────────────
REGRESSION_MODEL_PATH = SAVED_MODELS_DIR / "regression.pkl"
LSTM_MODEL_PATH       = SAVED_MODELS_DIR / "lstm_model.keras"
LSTM_SCALER_PATH      = SAVED_MODELS_DIR / "lstm_scaler.pkl"

# ─── Django backend DB connection (used by db_fetcher) ────────────────────────
DJANGO_DB = {
    "host":     os.getenv("DB_HOST",     "localhost"),
    "port":     int(os.getenv("DB_PORT", "5432")),
    "name":     os.getenv("DB_NAME",     "syncher_db"),
    "user":     os.getenv("DB_USER",     "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
}

# ─── Groq API ─────────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Two distinct models as per team spec:
GROQ_HEALTH_MODEL   = "llama-3.1-8b-instant"   # health_engine  → whole-health analysis
GROQ_CHATBOT_MODEL  = "llama-3.3-70b-versatile"              # groq_client    → RAG chatbot

GROQ_MAX_TOKENS     = 1024
GROQ_TEMPERATURE    = 0.3   # low = consistent medical responses

# ─── ML Hyperparameters ───────────────────────────────────────────────────────
LSTM_SEQUENCE_LEN   = 3     # number of past cycles used as input sequence
LSTM_EPOCHS         = 50
LSTM_BATCH_SIZE     = 16
LSTM_UNITS          = 64

REGRESSION_MIN_CYCLES = 2   # minimum cycles needed to run regression

# ─── Prediction rules ─────────────────────────────────────────────────────────
OVULATION_OFFSET_DAYS = 14  # standard LMP - 14 rule; refined per cycle length
OVULATION_WINDOW_DAYS = 3   # ±1 day either side

# ─── Feature list (must match feature_extraction output order) ────────────────
FEATURE_COLUMNS = [
    "age",
    "weight",
    "avg_cycle_length",
    "cycle_length_1",
    "cycle_length_2",
    "cycle_length_3",
    "period_duration_1",
    "period_duration_2",
    "period_duration_3",
    "cycle_variance",
    "pain",
    "flow",
    "mood",
    "sleep",
    "stress",
    "exercise",
    "food",
    "hydration",
    "white_discharge",
    "medication_taken",
    "routine_changed",
    "symptom_count",
    "has_cramps",
    "has_headache",
    "has_fatigue",
    "has_mood_swings",
    "has_nausea",
    "has_pcos",
    "has_pcod",
    "has_uti",
    "has_thyroid",
    "my_health_score",
]

# ─── Encoding maps (single source of truth — used by encoding.py) ─────────────
MOOD_MAP = {
    "low": 1,
    "irritated": 2,
    "happy": 3,
}

FLOW_MAP = {
    "light": 1,
    "medium": 2,
    "heavy": 3,
}

STRESS_MAP = {
    "none": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
}

EXERCISE_MAP = {
    "none": 0,
    "light": 1,
    "moderate": 2,
    "intense": 3,
}

WHITE_DISCHARGE_MAP = {
    "none": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
}

FOOD_MAP = {
    "skipped": 0,
    "junk": 1,
    "home": 2,
    "healthy": 3,
}

HYDRATION_MAP = {
    "no": 0,
    "yes": 1,
}

BINARY_MAP = {
    "no": 0,
    "yes": 1,
}

# My Health Q answer → score map
MY_HEALTH_SCORE_MAP = {
    "q1": {"None": 0, "Mild/occasional": 5, "Persistent/recurrent": 10, "Severe/cystic": 15},
    "q2": {"None": 0, "Mild": 5, "Moderate": 10, "Significant": 15},
    "q3": {"No": 0, "Mild": 5, "Noticeable": 10},
    "q4": {"No": 0, "Mild (2-4 kg)": 5, "Moderate (5-8 kg)": 10, "Significant (>8 kg)": 15},
    "q5": {"No": 0, "Mild (2-4 kg)": 5, "Moderate (5-8 kg)": 10, "Significant (>8 kg)": 15},
    "q6": {"No": 0, "Yes": 10},
    "q7": {"No": 0, "Mild": 5, "Clear/visible": 10},
    "q8": {"Normal": 0, "Slight sleepiness": 5, "Strong fatigue/crashes": 10},
    "q9": {"≥4 times/week": 0, "2-3 times/week": 5, "Rare/none": 10},
    "q10": {"Mostly whole foods": 0, "Mixed": 5, "High sugar/processed/junk": 10},
}

# Risk thresholds for My Health score
MY_HEALTH_RISK_BANDS = [
    (0,  24,  "Low Risk"),
    (25, 49,  "Mild Risk"),
    (50, 74,  "Moderate Risk"),
    (75, 110, "High Risk"),
]