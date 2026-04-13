from apps.cycle_app.models import CycleHistory, PredictionFeedback
from apps.log_app.models import DailyLog, CycleLog


def get_user_data_for_ml(user):
    """
    Collects all user data from DB and formats it
    for Dev3's ML prediction function.
    """
    cycles = CycleHistory.objects.filter(user=user).order_by('start_date')
    cycle_data = [
        {
            "start_date":   str(c.start_date),
            "end_date":     str(c.end_date) if c.end_date else None,
            "cycle_length": c.cycle_length
        }
        for c in cycles
    ]

    logs = DailyLog.objects.filter(user=user).order_by('-date')[:30]
    log_data = [
        {
            "date":            str(l.date),
            "sleep":           l.sleep,
            "stress":          l.stress,
            "exercise":        l.exercise,
            "medication":      l.medication,
            "food":            l.food,
            "white_discharge": l.white_discharge,
            "hydration":       l.hydration,
            "symptoms":        l.symptoms
        }
        for l in logs
    ]

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
        profile_data = {"avg_cycle_length": 28}

    try:
        health      = user.my_health
        health_risk = health.risk_level or "Unknown"
    except Exception:
        health_risk = "Unknown"

    return {
        "profile":    profile_data,
        "cycles":     cycle_data,
        "logs":       log_data,
        "cycle_logs": cycle_log_data,
        "health_risk": health_risk
    }


def get_latest_feedback(user):
    """
    Gets the most recent prediction feedback from user.
    Returns None if no feedback exists.
    """
    return PredictionFeedback.objects.filter(
        user=user
    ).order_by('-created_at').first()


def get_dashboard_data(user):
    """
    Main function called by dashboard view.
    Checks if user has submitted feedback and uses actual_date
    to update predictions accordingly.
    """
    user_data = get_user_data_for_ml(user)

    try:
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
        #     "feedback_submitted":     False,
        # }
        # -------------------------------------------------------

        return _stub_dashboard_response(user_data, user)

    except Exception as e:
        return _stub_dashboard_response(user_data, user)


def _stub_dashboard_response(user_data, user):
    """
    Stub response until Dev3 ML is ready.
    Uses actual_date from feedback if available.
    """
    from datetime import date, timedelta, datetime

    today      = date.today()
    avg_length = user_data["profile"].get("avg_cycle_length", 28)
    cycles     = user_data.get("cycles", [])

    # Check if user has submitted feedback with actual date
    latest_feedback = get_latest_feedback(user)

    # Determine base date for prediction
    # Priority: actual_date from feedback → last cycle start → today
    if latest_feedback and not latest_feedback.prediction_correct:
        # User corrected the date — use their actual date as base
        base_date   = latest_feedback.actual_date
        next_period = base_date + timedelta(days=avg_length)
        feedback_submitted = True
    elif latest_feedback and latest_feedback.prediction_correct:
        # User confirmed prediction was correct
        # Use the confirmed date as base
        base_date   = latest_feedback.actual_date
        next_period = base_date + timedelta(days=avg_length)
        feedback_submitted = True
    elif cycles:
        # No feedback yet — predict from last cycle
        last_start  = cycles[-1]["start_date"]
        last_date   = datetime.strptime(last_start, "%Y-%m-%d").date()
        next_period = last_date + timedelta(days=avg_length)
        feedback_submitted = False
    else:
        # No cycles at all — predict from today
        next_period        = today + timedelta(days=avg_length)
        feedback_submitted = False

    # Check if there's a newer cycle after the feedback
    # If yes — feedback is for old cycle, ask again for new cycle
    if latest_feedback and cycles:
        last_cycle_date = datetime.strptime(
            cycles[-1]["start_date"], "%Y-%m-%d"
        ).date()
        if last_cycle_date > latest_feedback.actual_date:
            # New cycle started after last feedback — reset feedback status
            feedback_submitted = False
            next_period = last_cycle_date + timedelta(days=avg_length)

    # Ovulation window — 12-16 days before next period
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
    else:
        score = 0.75

    # Insights from logs
    insights = []
    logs = user_data.get("logs", [])
    if logs:
        high_stress = sum(1 for l in logs if l["stress"] == "high")
        low_sleep   = sum(1 for l in logs if l["sleep"] < 6)
        if high_stress > 3:
            insights.append("High stress detected — may delay your cycle")
        if low_sleep > 3:
            insights.append("Low sleep detected — may affect cycle regularity")
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
# returns
    return {
        "next_period_date":       str(next_period),
        "ovulation_window":       [str(ovulation_start), str(ovulation_end)],
        "cycle_regularity_score": score,
        "predicted_length":       avg_length,
        "confidence":             0.75,
        "health_insights":        insights,
        "health_risk":            user_data.get("health_risk", "Unknown"),
        "recent_symptoms":        recent_symptoms,
        "medical_history":        medical_history,
        "feedback_submitted":     feedback_submitted  # ← tells frontend whether to show the question
    }
