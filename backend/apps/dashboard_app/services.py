"""
Dashboard Services - Generate health insights with AI
"""

from apps.chatbot_app.llm import generate_dashboard_insights


def get_dashboard_data(user):
    """
    Get comprehensive dashboard data with AI insights.
    """
    from apps.cycle_app.models import CycleHistory
    from apps.log_app.models import DailyLog
    from apps.health_app.models import MyHealth
    from datetime import date, timedelta

    # Get user data
    try:
        health = MyHealth.objects.get(user=user)
        score = health.score
        risk_level = health.risk_level
    except MyHealth.DoesNotExist:
        score = None
        risk_level = "Unknown"

    # Get recent logs (last 7 days)
    seven_days_ago = date.today() - timedelta(days=7)
    recent_logs = DailyLog.objects.filter(
        user=user,
        date__gte=seven_days_ago
    ).order_by('-date').values()

    # Get cycle data
    latest_cycle = CycleHistory.objects.filter(user=user).order_by('-start_date').first()
    
    cycle_status = "No cycle logged"
    next_period = None
    if latest_cycle:
        if latest_cycle.end_date:
            cycle_status = "Completed"
        else:
            cycle_status = "Active"
        
        # Predict next period
        try:
            avg_length = user.onboarding.avg_cycle_length
            if latest_cycle.end_date:
                next_period = latest_cycle.end_date + timedelta(days=avg_length)
            else:
                next_period = latest_cycle.start_date + timedelta(days=avg_length)
        except:
            next_period = None

    # Get recent symptoms
    recent_symptom = None
    if recent_logs:
        recent_log = list(recent_logs)[0]
        recent_symptom = {
            "date": recent_log.get('date'),
            "stress": recent_log.get('stress'),
            "sleep": recent_log.get('sleep'),
            "pain": recent_log.get('pain'),
            "mood": recent_log.get('mood')
        }

    # Prepare user context for AI
    user_context = {
        "stress": recent_symptom.get('stress') if recent_symptom else "unknown",
        "sleep": recent_symptom.get('sleep') if recent_symptom else "unknown",
        "pain": recent_symptom.get('pain') if recent_symptom else "unknown",
        "mood": recent_symptom.get('mood') if recent_symptom else "unknown",
    }

    # Get AI insights
    insights_data = generate_dashboard_insights(
        user_data=user_context,
        recent_logs=list(recent_logs)
    )

    return {
        "health_score": score,
        "risk_level": risk_level,
        "cycle_status": cycle_status,
        "next_period": str(next_period) if next_period else None,
        "recent_symptoms": recent_symptom,
        "ai_insights": insights_data.get("insights"),
        "recent_logs_count": len(recent_logs),
        "last_updated": "now"
    }