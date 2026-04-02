from apps.cycle_app.models import CycleHistory
from apps.log_app.models import DailyLog


def get_user_data_for_ml(user):
    """
    Collects all user data from DB and formats it
    for Dev3's ML prediction function.

    This is the data package sent to Dev3's predict()
    """
    # Get all cycles
    cycles = CycleHistory.objects.filter(user=user).order_by('start_date')
    cycle_data = [
        {
            "start_date":   str(c.start_date),
            "end_date":     str(c.end_date),
            "cycle_length": c.cycle_length
        }
        for c in cycles
    ]

    # Get last 30 daily logs
    logs = DailyLog.objects.filter(user=user).order_by('-date')[:30]
    log_data = [
        {
            "date":     str(l.date),
            "pain":     l.pain,
            "mood":     l.mood,
            "flow":     l.flow,
            "sleep":    l.sleep,
            "stress":   l.stress,
            "exercise": l.exercise
        }
        for l in logs
    ]

    # Get user profile
    try:
        profile = user.profile
        profile_data = {
            "age":              profile.age,
            "weight":           profile.weight,
            "avg_cycle_length": profile.avg_cycle_length,
            "cycle_history":    profile.cycle_history
        }
    except Exception:
        profile_data = {
            "avg_cycle_length": 28
        }

    return {
        "profile":  profile_data,
        "cycles":   cycle_data,
        "logs":     log_data
    }


def get_dashboard_data(user):
    """
    Main function called by dashboard view.

    Tries to call Dev3's ML service.
    Falls back to stub response if ML service not ready yet.

    Returns exact contract shape:
    {
        "next_period_date": "2024-03-29",
        "ovulation_window": ["2024-03-14", "2024-03-16"],
        "cycle_regularity_score": 0.85,
        "insights": [
            "Your cycle is regular",
            "High stress may delay cycle"
        ]
    }
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
        #     "insights":               insights + risks
        # }
        # -------------------------------------------------------

        # STUB — used until Dev3 ML is ready
        return _stub_dashboard_response(user_data)

    except Exception as e:
        # If ML fails for any reason, return stub
        return _stub_dashboard_response(user_data)


def _stub_dashboard_response(user_data):
    """
    Stub response that calculates basic predictions
    using simple date arithmetic.
    Keeps Dev2 unblocked while Dev3 builds the ML.
    """
    from datetime import date, timedelta

    today = date.today()

    # Simple prediction — last cycle start + avg cycle length
    avg_length = user_data["profile"].get("avg_cycle_length", 28)

    cycles = user_data.get("cycles", [])
    if cycles:
        last_start = cycles[-1]["start_date"]
        from datetime import datetime
        last_date = datetime.strptime(last_start, "%Y-%m-%d").date()
        next_period = last_date + timedelta(days=avg_length)
    else:
        next_period = today + timedelta(days=avg_length)

    # Ovulation is roughly 14 days before next period
    ovulation_start = next_period - timedelta(days=16)
    ovulation_end   = next_period - timedelta(days=12)

    # Basic regularity score
    if len(cycles) >= 3:
        lengths = [c["cycle_length"] for c in cycles if c["cycle_length"]]
        if lengths:
            variance = max(lengths) - min(lengths)
            score = round(max(0.0, 1.0 - (variance / 10)), 2)
        else:
            score = 0.75
    else:
        score = 0.75

    # Basic insights from logs
    insights = []
    logs = user_data.get("logs", [])
    if logs:
        high_stress = sum(1 for l in logs if l["stress"] == "high")
        if high_stress > 3:
            insights.append("High stress detected — may delay your cycle")
        low_sleep = sum(1 for l in logs if l["sleep"] < 6)
        if low_sleep > 3:
            insights.append("Low sleep detected — may affect cycle regularity")

    if not insights:
        insights.append("Keep logging daily for better insights")

    return {
        "next_period_date":       str(next_period),
        "ovulation_window":       [str(ovulation_start), str(ovulation_end)],
        "cycle_regularity_score": score,
        "insights":               insights
    }