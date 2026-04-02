# ml_service/prediction/predict.py

from datetime import datetime, timedelta
from ml_service.models.regression import load_model, predict_next_cycle_length
from ml_service.models.lstm import load_lstm, predict_with_lstm
from ml_service.prediction.feature_extraction import build_model_input
from ml_service.config import CYCLE_VARIANCE_THRESHOLD


def predict(user_data: dict) -> dict:
    """
    Master prediction function — called by Dev1's dashboard_app/services.py

    Now runs BOTH regression and LSTM, picks the best result,
    and returns a comparison so Dev1 can expose it in the API.

    Args:
        user_data = {
            "cycle_records": [...],
            "log_records":   [...],
        }

    Returns:
        {
            "next_period_date":         "2024-04-15",
            "ovulation_window":         ["2024-04-01", "2024-04-03"],
            "cycle_regularity_score":   0.85,
            "predicted_cycle_length":   28.3,
            "confidence":               "high",
            "model_used":               "lstm",
            "model_comparison": {
                "regression": 27.9,
                "lstm":        28.3,
                "agreement":   True,
            },
            "insights": [...],
        }
    """
    cycle_records = user_data.get("cycle_records", [])
    log_records   = user_data.get("log_records", [])

    if not cycle_records:
        raise ValueError("cycle_records are required for prediction.")

    # ── Step 1: Extract features ──────────────────────────────────
    features = build_model_input(cycle_records, log_records)

    # ── Step 2: Regression prediction (Day 4 model) ───────────────
    reg_model        = load_model()
    reg_prediction   = predict_next_cycle_length(reg_model, features)

    # ── Step 3: LSTM prediction (Day 5 model) ─────────────────────
    lstm_model, scaler          = load_lstm()
    lstm_prediction, lstm_conf  = predict_with_lstm(
        lstm_model, scaler, cycle_records
    )

    # ── Step 4: Pick best model ───────────────────────────────────
    # Use LSTM if we have enough cycles (≥3), else fall back to regression
    cycle_count  = features.get("cycle_count", 0)
    use_lstm     = cycle_count >= 3
    final_length = lstm_prediction if use_lstm else reg_prediction
    model_used   = "lstm" if use_lstm else "regression"

    # ── Step 5: Agreement check ───────────────────────────────────
    agreement = abs(reg_prediction - lstm_prediction) <= 2.0  # within 2 days

    # ── Step 6: Next period date ──────────────────────────────────
    last_start = features.get("last_cycle_start")
    last_start_date = (
        datetime.strptime(last_start, "%Y-%m-%d") if last_start
        else datetime.today()
    )
    next_period_date = last_start_date + timedelta(days=final_length)

    # ── Step 7: Ovulation window ──────────────────────────────────
    ovulation_day   = next_period_date - timedelta(days=14)
    ovulation_start = ovulation_day - timedelta(days=1)
    ovulation_end   = ovulation_day + timedelta(days=1)

    # ── Step 8: Regularity score ──────────────────────────────────
    std = features.get("std_cycle_length", 0)
    regularity_score = round(max(0.0, 1.0 - (std / CYCLE_VARIANCE_THRESHOLD)), 2)

    # ── Step 9: Confidence ────────────────────────────────────────
    if cycle_count >= 6 and lstm_conf >= 0.75:
        confidence = "high"
    elif cycle_count >= 3 and lstm_conf >= 0.5:
        confidence = "medium"
    else:
        confidence = "low"

    # ── Step 10: Insights ─────────────────────────────────────────
    insights = _generate_basic_insights(features, regularity_score)

    return {
        "next_period_date":         next_period_date.strftime("%Y-%m-%d"),
        "ovulation_window":         [
            ovulation_start.strftime("%Y-%m-%d"),
            ovulation_end.strftime("%Y-%m-%d"),
        ],
        "cycle_regularity_score":   regularity_score,
        "predicted_cycle_length":   final_length,
        "confidence":               confidence,
        "model_used":               model_used,
        "model_comparison": {
            "regression":   reg_prediction,
            "lstm":         lstm_prediction,
            "agreement":    agreement,
        },
        "insights":                 insights,
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _generate_basic_insights(features: dict, regularity_score: float) -> list[str]:
    """Generate human-readable insight strings from features."""
    insights = []

    if regularity_score < 0.5:
        insights.append(
            "Your cycle shows significant variation. "
            "Consider tracking stress and sleep patterns."
        )

    avg_stress = features.get("avg_stress")
    if avg_stress and avg_stress >= 7:
        insights.append(
            "High average stress detected. "
            "Stress can delay your cycle by several days."
        )

    avg_sleep = features.get("avg_sleep")
    if avg_sleep and avg_sleep < 6:
        insights.append(
            "Poor sleep detected. "
            "Sleep deprivation can affect hormonal balance."
        )

    high_pain = features.get("high_pain_days", 0)
    if high_pain >= 2:
        insights.append(
            f"You logged high pain on {high_pain} days. "
            "Consider speaking with a healthcare provider."
        )

    trend = features.get("cycle_trend")
    if trend == "increasing":
        insights.append(
            "Your cycles have been gradually getting longer recently."
        )
    elif trend == "decreasing":
        insights.append(
            "Your cycles have been gradually getting shorter recently."
        )

    if not insights:
        insights.append("Your cycle looks healthy and regular. Keep it up!")

    return insights