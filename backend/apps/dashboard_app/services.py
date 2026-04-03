# backend/apps/dashboard_app/services.py

from apps.cycle_app.models import CycleHistory
from apps.log_app.models import DailyLog


def get_user_data_for_ml(user):
    """
    Collects all user data from DB and formats it
    for Dev3's ML prediction function.
    """
    cycles = CycleHistory.objects.filter(user=user).order_by("start_date")
    cycle_records = [
        {
            "start_date":   str(c.start_date),
            "cycle_length": c.cycle_length,
        }
        for c in cycles
    ]

    logs = DailyLog.objects.filter(user=user).order_by("-date")[:30]
    log_records = [
        {
            "date":     str(l.date),
            "pain":     l.pain,
            "mood":     l.mood,
            "flow":     l.flow,
            "sleep":    l.sleep,
            "stress":   l.stress,
            "exercise": l.exercise,
        }
        for l in logs
    ]

    return {
        "cycle_records": cycle_records,
        "log_records":   log_records,
    }


def get_dashboard_data(user):
    """
    Main function called by dashboard view.
    Calls Dev3's ML predict() directly.

    Returns exact contract shape:
    {
        "next_period_date":       "2024-03-29",
        "ovulation_window":       ["2024-03-14", "2024-03-16"],
        "cycle_regularity_score": 0.85,
        "insights":               ["Your cycle is regular", ...]
    }
    """
    user_data = get_user_data_for_ml(user)

    try:
        # ── DEV3 INTEGRATION POINT ────────────────────────────────
        from ml_service.prediction.predict import predict
        result = predict(user_data)

        return {
            "next_period_date":       result["next_period_date"],
            "ovulation_window":       result["ovulation_window"],
            "cycle_regularity_score": result["cycle_regularity_score"],
            "insights":               result["insights"],
        }
        # ─────────────────────────────────────────────────────────

    except ImportError as e:
        # ml_service not found — path issue
        print(f"[dashboard_service] ImportError: {e}")
        return _stub_dashboard_response(user_data)

    except ValueError as e:
        # predict() raised — not enough cycle data
        print(f"[dashboard_service] ValueError: {e}")
        return _stub_dashboard_response(user_data)

    except KeyError as e:
        # predict() returned unexpected shape
        print(f"[dashboard_service] KeyError - unexpected ML response shape: {e}")
        return _stub_dashboard_response(user_data)

    except Exception as e:
        # Any other unexpected error
        print(f"[dashboard_service] Unexpected error: {e}")
        return _stub_dashboard_response(user_data)


def _stub_dashboard_response(user_data):
    """
    Stub response that calculates basic predictions
    using simple date arithmetic.
    Keeps Dev2 unblocked while Dev3 ML is unavailable.
    """
    from datetime import date, timedelta, datetime

    today         = date.today()
    cycles        = user_data.get("cycle_records", [])
    logs          = user_data.get("log_records",   [])

    # Simple next period prediction
    lengths = [c["cycle_length"] for c in cycles if c.get("cycle_length")]
    avg_length = round(sum(lengths) / len(lengths)) if lengths else 28

    if cycles:
        last_start  = datetime.strptime(cycles[-1]["start_date"], "%Y-%m-%d").date()
        next_period = last_start + timedelta(days=avg_length)
    else:
        next_period = today + timedelta(days=avg_length)

    ovulation_start = next_period - timedelta(days=16)
    ovulation_end   = next_period - timedelta(days=12)

    # Basic regularity score
    if len(lengths) >= 3:
        variance = max(lengths) - min(lengths)
        score    = round(max(0.0, 1.0 - (variance / 10)), 2)
    else:
        score = 0.75

    # Basic insights from logs
    insights    = []
    high_stress = sum(1 for l in logs if l.get("stress") == "high")
    low_sleep   = sum(1 for l in logs if (l.get("sleep") or 8) < 6)

    if high_stress > 3:
        insights.append("High stress detected — may delay your cycle")
    if low_sleep > 3:
        insights.append("Low sleep detected — may affect cycle regularity")
    if not insights:
        insights.append("Keep logging daily for better insights")

    return {
        "next_period_date":       str(next_period),
        "ovulation_window":       [str(ovulation_start), str(ovulation_end)],
        "cycle_regularity_score": score,
        "insights":               insights,
    }