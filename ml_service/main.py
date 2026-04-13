"""
ml_service/main.py
Flask micro-service exposing ML endpoints.
Django backend calls these internally — they are NOT exposed to the frontend.
All responses use the exact field names from the API contract.
"""

import logging
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# ── Load .env FIRST before any other imports ──────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR.parent / ".env")

# Now safe to add path and import everything else
sys.path.insert(0, str(BASE_DIR))

from flask import Flask, request, jsonify
from data.db_fetcher import fetch_full_user_context, fetch_my_health_responses

from prediction.predict import predict, reload_models
from prediction.feature_extraction import build_feature_vector
from prediction.my_health_scorer import compute_my_health_score
from insights.insight_engine import generate_insights
from insights.risk_engine import detect_cycle_risks, summarise_risk, get_risk_context
from insights.health_engine import generate_health_risk, generate_medical_notes_suggestion
from chatbot.rag import answer_question
from preprocessing.cleaning import clean_cycle_history, derive_cycle_lengths

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)


# ─── Health check ─────────────────────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "service": "syncher-ml"}), 200


# ─── Dashboard prediction ─────────────────────────────────────────────────────

@app.route("/ml/dashboard", methods=["POST"])
def dashboard():
    """
    Called by Django dashboard_app/services.py.
    Body: {"user_id": int}
    Returns full dashboard ML payload.
    """
    data    = request.get_json(force=True)
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    try:
        ctx = fetch_full_user_context(user_id)

        raw_profile    = ctx["profile"]
        raw_cycles     = ctx["cycle_history"]
        raw_cycle_logs = ctx["cycle_logs"]
        raw_daily_logs = ctx["daily_logs"]
        my_health_resp = ctx["my_health"]

        # ── ML predictions ────────────────────────────────────────────────────
        prediction = predict(
            raw_profile, raw_cycles, raw_cycle_logs, raw_daily_logs, my_health_resp
        )

        # ── Feature vector for insights / risk ───────────────────────────────
        fv = build_feature_vector(
            raw_profile, raw_cycles, raw_cycle_logs, raw_daily_logs, my_health_resp
        )

        # ── Insights ──────────────────────────────────────────────────────────
        insights = generate_insights(
            fv, raw_cycles,
            predicted_length=prediction["predicted_length"],
            confidence=prediction["confidence"],
        )

        # ── Risk flags ───────────────────────────────────────────────────────
        risk_flags   = detect_cycle_risks(fv, raw_cycles)
        risk_summary = summarise_risk(risk_flags)
        risk_ctx     = get_risk_context(risk_flags)

        # ── GenAI health risk (Groq llama-3.1-8b-instant) ───────────────────
        my_health_scored = compute_my_health_score(my_health_resp) if my_health_resp else {}
        health_risk = generate_health_risk(ctx, risk_ctx, my_health_scored)

        # ── Recent symptoms (from onboarding / last cycle log) ───────────────
        recent = raw_cycle_logs[0] if raw_cycle_logs else {}
        recent_symptoms = {
            "pain":  recent.get("pain",  raw_profile.get("pain",  0)),
            "mood":  recent.get("mood",  raw_profile.get("mood",  "low")),
            "flow":  recent.get("flow",  raw_profile.get("flow",  "light")),
        }

        # ── Medical history ───────────────────────────────────────────────────
        medical_history = {
            "condition": raw_profile.get("medical_condition", "none"),
            "notes":     raw_profile.get("medical_notes", ""),
        }

        # ── Strip internal fields before returning ────────────────────────────
        prediction.pop("_model_used", None)

        return jsonify({
            **prediction,                             # next_period_date, ovulation_window, etc.
            "health_insights":  insights,
            "health_risk":      health_risk,
            "recent_symptoms":  recent_symptoms,
            "medical_history":  medical_history,
        }), 200

    except Exception as exc:
        logger.exception("Dashboard ML failed for user %d: %s", user_id, exc)
        return jsonify({"error": "ML service error. Please try again."}), 500


# ─── My Health scoring ────────────────────────────────────────────────────────

@app.route("/ml/my-health", methods=["POST"])
def my_health():
    """
    Scores the My Health questionnaire.
    Body: {"q1": "...", "q2": "...", ..., "q10": "..."}
    Returns: {"score": int, "risk_level": str, "insights": [...]}
    API contract: POST /api/my-health
    """
    data = request.get_json(force=True)
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    try:
        result = compute_my_health_score(data)
        return jsonify({
            "responses":   data,
            "score":       result["score"],
            "risk_level":  result["risk_level"],
            "insights":    result["insights"],
        }), 200
    except Exception as exc:
        logger.exception("My Health scoring failed: %s", exc)
        return jsonify({"error": "Scoring failed"}), 500


# ─── Chatbot ──────────────────────────────────────────────────────────────────

@app.route("/ml/chat", methods=["POST"])
def chat():
    """
    RAG + LLM Agent chatbot endpoint.
    Body: {"user_id": int, "question": str}
    Returns: {"answer": str}
    API contract: POST /api/chat

    Agent maintains per-user conversation memory across calls.
    Uses menstllama with 4 live-data tools + RAG knowledge base.
    """
    data     = request.get_json(force=True)
    user_id  = data.get("user_id")
    question = data.get("question", "").strip()

    if not user_id or not question:
        return jsonify({"error": "user_id and question are required"}), 400

    try:
        answer = answer_question(user_id, question)
        return jsonify({"answer": answer}), 200
    except Exception as exc:
        logger.exception("Chat failed for user %d: %s", user_id, exc)
        return jsonify({"error": "Chat service error"}), 500


@app.route("/ml/chat/clear", methods=["POST"])
def chat_clear_history():
    """
    Clear per-user conversation memory.
    Called by Django on logout or 'New Chat' action.
    Body: {"user_id": int}
    """
    data    = request.get_json(force=True)
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
    from chatbot.rag import clear_history
    clear_history(user_id)
    return jsonify({"status": "cleared"}), 200


# ─── Medical notes suggestion (onboarding) ────────────────────────────────────

@app.route("/ml/onboarding-health-suggestion", methods=["POST"])
def onboarding_suggestion():
    """
    Called during onboarding when user submits medical notes / 'Other' condition.
    Body: {"medical_notes": str, "condition": str}
    Returns: {"suggestion": str}
    """
    data          = request.get_json(force=True)
    medical_notes = data.get("medical_notes", "")
    condition     = data.get("condition", "none")

    try:
        suggestion = generate_medical_notes_suggestion(medical_notes, condition)
        return jsonify({"suggestion": suggestion}), 200
    except Exception as exc:
        logger.exception("Onboarding suggestion failed: %s", exc)
        return jsonify({"suggestion": ""}), 200   # non-fatal


# ─── Retrain trigger ──────────────────────────────────────────────────────────

@app.route("/ml/retrain", methods=["POST"])
def trigger_retrain():
    """
    Called by Django Celery worker after prediction feedback accumulates.
    Body: {} (no payload needed — fetches all users' data internally)
    """
    try:
        from retrain import run_retrain
        result = run_retrain()
        reload_models()
        return jsonify({"status": "retrained", **result}), 200
    except Exception as exc:
        logger.exception("Retrain failed: %s", exc)
        return jsonify({"error": "Retrain failed"}), 500


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.getenv("ML_SERVICE_PORT", 8001))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    logger.info("Starting SYNCHER ML Service on port %d", port)
    app.run(host="0.0.0.0", port=port, debug=debug)