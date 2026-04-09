# backend/apps/dashboard_app/services.py

from apps.cycle_app.models import CycleHistory
from apps.log_app.models import DailyLog, CycleLog


def get_user_data_for_ml(user):
    """
    Collects all user data from DB and formats it
    for Dev3's ML prediction function.
    """
    cycles = CycleHistory.objects.filter(user=user).order_by("start_date")
    cycle_records = [
        {
            "start_date":   str(c.start_date),
<<<<<<< HEAD
            "cycle_length": c.cycle_length,
=======
            "end_date":     str(c.end_date) if c.end_date else None,
            "cycle_length": c.cycle_length
>>>>>>> d98ae17 (dev 1 editing done)
        }
        for c in cycles
    ]

    logs = DailyLog.objects.filter(user=user).order_by("-date")[:30]
    log_records = [
        {
<<<<<<< HEAD
            "date":     str(l.date),
            "pain":     l.pain,
            "mood":     l.mood,
            "flow":     l.flow,
            "sleep":    l.sleep,
            "stress":   l.stress,
            "exercise": l.exercise,
=======
            "date":             str(l.date),
            "sleep":            l.sleep,
            "stress":           l.stress,
            "exercise":         l.exercise,
            "medication":       l.medication,
            "food":             l.food,
            "white_discharge":  l.white_discharge,
            "hydration":        l.hydration,
            "symptoms":         l.symptoms
>>>>>>> d98ae17 (dev 1 editing done)
        }
        for l in logs
    ]

<<<<<<< HEAD
    return {
        "cycle_records": cycle_records,
        "log_records":   log_records,
=======
    # Get last 30 cycle logs (period days)
    cycle_logs = CycleLog.objects.filter(user=user).order_by('-date')[:30]
    cycle_log_data = [
        {
            "date":     str(cl.date),
            "pain":     cl.pain,
            "mood":     cl.mood,
            "flow":     cl.flow,
            "sleep":    cl.sleep,
            "stress":   cl.stress,
            "exercise": cl.exercise,
        }
        for cl in cycle_logs
    ]

    # Get onboarding profile
    try:
        onboarding = user.onboarding
        profile_data = {
            "age":               onboarding.age,
            "weight":            onboarding.weight,
            "avg_cycle_length":  onboarding.avg_cycle_length,
            "cycle_history":     onboarding.cycle_history,
            "medical_condition": onboarding.medical_condition,
            "medical_notes":     onboarding.medical_notes,
            "pain":              onboarding.pain,
            "mood":              onboarding.mood,
            "flow":              onboarding.flow,
        }
    except Exception:
        profile_data = {
            "avg_cycle_length": 28
        }

    # Get health risk from MyHealth if available
    try:
        health          = user.my_health
        health_risk     = health.risk_level or "Unknown"
    except Exception:
        health_risk     = "Unknown"

    return {
        "profile":    profile_data,
        "cycles":     cycle_data,
        "logs":       log_data,
        "cycle_logs": cycle_log_data,
        "health_risk": health_risk
>>>>>>> d98ae17 (dev 1 editing done)
    }


def get_dashboard_data(user):
    """
    Main function called by dashboard view.
<<<<<<< HEAD
    Calls Dev3's ML predict() directly.
=======
>>>>>>> d98ae17 (dev 1 editing done)

    Returns exact contract shape:
    {
        "next_period_date":       "2024-03-29",
        "ovulation_window":       ["2024-03-14", "2024-03-16"],
        "cycle_regularity_score": 0.85,
<<<<<<< HEAD
        "insights":               ["Your cycle is regular", ...]
=======
        "predicted_length": 28,
        "confidence": 0.78,
        "health_insights": ["..."],
        "health_risk": "Moderate",
        "recent_symptoms": {"pain": 3, "mood": "low", "flow": "medium"},
        "medical_history": {"condition": "PCOS", "notes": "..."}
>>>>>>> d98ae17 (dev 1 editing done)
    }
    """
    user_data = get_user_data_for_ml(user)

    try:
<<<<<<< HEAD
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
=======
        # -------------------------------------------------------
        # DEV3 INTEGRATION POINT
        # When Dev3 is ready, uncomment below and remove the stub
        # -------------------------------------------------------
        # import sys
        # sys.path.append('../ml_service')
        # from prediction.predict import predict
        # from insights.insight_engine import get_insights
        # from insights.risk_engine import get_risks
        #
        # prediction = predict(user_data)
        # insights   = get_insights(user_data)
        # risks      = get_risks(user_data)
        #
        # return {
        #     "next_period_date":       prediction["next_period_date"],
        #     "ovulation_window":       prediction["ovulation_window"],
        #     "cycle_regularity_score": prediction["cycle_regularity_score"],
        #     "predicted_length":       prediction["predicted_length"],
        #     "confidence":             prediction["confidence"],
        #     "health_insights":        insights + risks,
        #     "health_risk":            user_data["health_risk"],
        #     "recent_symptoms":        prediction["recent_symptoms"],
        #     "medical_history":        prediction["medical_history"],
        # }
        # -------------------------------------------------------

        return _stub_dashboard_response(user_data)

    except Exception as e:
>>>>>>> d98ae17 (dev 1 editing done)
        return _stub_dashboard_response(user_data)


def _stub_dashboard_response(user_data):
    """
<<<<<<< HEAD
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
=======
    Stub response until Dev3 ML is ready.
    """
    from datetime import date, timedelta, datetime

    today      = date.today()
    avg_length = user_data["profile"].get("avg_cycle_length", 28)
    cycles     = user_data.get("cycles", [])

    # Next period prediction
    if cycles:
        last_start  = cycles[-1]["start_date"]
        last_date   = datetime.strptime(last_start, "%Y-%m-%d").date()
        next_period = last_date + timedelta(days=avg_length)
    else:
        next_period = today + timedelta(days=avg_length)

    # Ovulation window
    ovulation_start = next_period - timedelta(days=16)
    ovulation_end   = next_period - timedelta(days=12)

    # Regularity score
    if len(cycles) >= 3:
        lengths = [c["cycle_length"] for c in cycles if c.get("cycle_length")]
        if lengths:
            variance = max(lengths) - min(lengths)
            score    = round(max(0.0, 1.0 - (variance / 10)), 2)
        else:
            score = 0.75
>>>>>>> d98ae17 (dev 1 editing done)
    else:
        score = 0.75

    # Basic insights from logs
<<<<<<< HEAD
    insights    = []
    high_stress = sum(1 for l in logs if l.get("stress") == "high")
    low_sleep   = sum(1 for l in logs if (l.get("sleep") or 8) < 6)

    if high_stress > 3:
        insights.append("High stress detected — may delay your cycle")
    if low_sleep > 3:
        insights.append("Low sleep detected — may affect cycle regularity")
=======
    insights = []
    logs = user_data.get("logs", [])
    if logs:
        high_stress = sum(1 for l in logs if l["stress"] == "high")
        low_sleep   = sum(1 for l in logs if l["sleep"] < 6)
        if high_stress > 3:
            insights.append("High stress detected — may delay your cycle")
        if low_sleep > 3:
            insights.append("Low sleep detected — may affect cycle regularity")
>>>>>>> d98ae17 (dev 1 editing done)
    if not insights:
        insights.append("Keep logging daily for better insights")

    # Recent symptoms from latest cycle log
    recent_symptoms = {"pain": 0, "mood": "unknown", "flow": "unknown"}
    cycle_logs = user_data.get("cycle_logs", [])
    if cycle_logs:
        latest = cycle_logs[0]
        recent_symptoms = {
            "pain": latest.get("pain", 0),
            "mood": latest.get("mood", "unknown"),
            "flow": latest.get("flow", "unknown")
        }

    # Medical history from onboarding
    profile = user_data.get("profile", {})
    medical_history = {
        "condition": profile.get("medical_condition", "None"),
        "notes":     profile.get("medical_notes", "")
    }

    return {
        "next_period_date":       str(next_period),
        "ovulation_window":       [str(ovulation_start), str(ovulation_end)],
        "cycle_regularity_score": score,
<<<<<<< HEAD
        "insights":               insights,
=======
        "predicted_length":       avg_length,
        "confidence":             0.75,
        "health_insights":        insights,
        "health_risk":            user_data.get("health_risk", "Unknown"),
        "recent_symptoms":        recent_symptoms,
        "medical_history":        medical_history
>>>>>>> d98ae17 (dev 1 editing done)
    }