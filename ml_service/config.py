# ml_service/config.py

import os

# ─── ML Config ────────────────────────────────────────────────
#MODEL_VERSION         = "1.0"
#REGRESSION_MODEL_PATH = "ml_service/saved_models/regression.pkl"
#LSTM_MODEL_PATH       = "ml_service/saved_models/lstm.h5"

# ─── Groq Config ──────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL   = "llama-3.1-8b-instant"
GROQ_TIMEOUT = 30
CYCLE_VARIANCE_THRESHOLD = 7.0


# Base URL of Dev1's Django server
# Local dev  → "http://127.0.0.1:8000"
# Production → "https://your-deployed-api.com"
DJANGO_API_BASE_URL = os.getenv("DJANGO_API_BASE_URL", "http://127.0.0.1:8000")
 
# Internal token so ML service can call Django APIs without user login
# Dev1 must create this token in Django admin for an internal service account
# Django: from rest_framework.authtoken.models import Token
#         Token.objects.create(user=internal_service_user)
DJANGO_INTERNAL_TOKEN = os.getenv("DJANGO_INTERNAL_TOKEN", "your-internal-token-here")

# ─── Feature Config ───────────────────────────────────────────
MOOD_ENCODING = {
    # ── Contract values (what Dev2 actually sends) ──
    "high": 4, 
    "irritated": 3,
    "medium":  2,
    "low":     1,
    

    # ── Keep these as fallback ──
    "happy":   3,
    "neutral": 2,
    "sad":     1,
    "anxious": 0,
}

FLOW_ENCODING = {
    "heavy":    3,
    "medium":   2,
    "light":    1,
    "spotting": 0,
}

# ─── Risk Thresholds ──────────────────────────────────────────
CYCLE_VARIANCE_THRESHOLD = 7    # days — beyond this = irregular
HIGH_PAIN_THRESHOLD      = 7    # out of 10
ABNORMAL_CYCLE_MIN       = 21   # days
ABNORMAL_CYCLE_MAX       = 35   # days