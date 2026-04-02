from workers.celery import app
from datetime import date, timedelta


@app.task
def send_period_reminder(user_id):
    """
    Sends period reminder notification to user.
    Triggered 2 days before predicted next period.
    """
    try:
        from apps.auth_app.models import User
        from apps.cycle_app.models import CycleHistory

        user = User.objects.get(id=user_id)

        latest_cycle = CycleHistory.objects.filter(
            user=user
        ).order_by('-start_date').first()

        if latest_cycle:
            avg_length  = user.profile.avg_cycle_length
            next_period = latest_cycle.start_date + timedelta(days=avg_length)
            days_left   = (next_period - date.today()).days

            # Log reminder (replace with actual push notification later)
            print(f"[REMINDER] User {user.email} — period in {days_left} days ({next_period})")

    except Exception as e:
        print(f"[REMINDER ERROR] {e}")


@app.task
def send_ovulation_reminder(user_id):
    """
    Sends ovulation window reminder.
    Triggered when user enters ovulation window.
    """
    try:
        from apps.auth_app.models import User
        from apps.cycle_app.models import CycleHistory

        user = User.objects.get(id=user_id)

        latest_cycle = CycleHistory.objects.filter(
            user=user
        ).order_by('-start_date').first()

        if latest_cycle:
            avg_length      = user.profile.avg_cycle_length
            next_period     = latest_cycle.start_date + timedelta(days=avg_length)
            ovulation_start = next_period - timedelta(days=16)
            ovulation_end   = next_period - timedelta(days=12)

            print(f"[OVULATION] User {user.email} — window {ovulation_start} to {ovulation_end}")

    except Exception as e:
        print(f"[OVULATION ERROR] {e}")


@app.task
def send_daily_log_reminder(user_id):
    """
    Reminds user to log their daily symptoms
    if they haven't logged today.
    """
    try:
        from apps.auth_app.models import User
        from apps.log_app.models import DailyLog

        user = User.objects.get(id=user_id)
        today = date.today()

        already_logged = DailyLog.objects.filter(
            user=user,
            date=today
        ).exists()

        if not already_logged:
            print(f"[LOG REMINDER] User {user.email} hasn't logged today ({today})")

    except Exception as e:
        print(f"[LOG REMINDER ERROR] {e}")


@app.task
def trigger_model_retraining():
    """
    Triggers Dev3's ML model retraining.
    Scheduled to run periodically via Celery Beat.
    Called when enough new data has accumulated.
    """
    try:
        # -------------------------------------------------------
        # DEV3 INTEGRATION POINT
        # When Dev3 is ready, uncomment below
        # -------------------------------------------------------
        # import sys
        # sys.path.append('../ml_service')
        # from models.regression import retrain
        # retrain()
        # -------------------------------------------------------

        print("[RETRAINING] Model retraining triggered")

    except Exception as e:
        print(f"[RETRAINING ERROR] {e}")


@app.task
def check_risk_alerts(user_id):
    """
    Checks user's recent logs for risk patterns
    and triggers alerts if needed.
    High pain > 3 days or irregular cycle detected.
    """
    try:
        from apps.auth_app.models import User
        from apps.log_app.models import DailyLog

        user = User.objects.get(id=user_id)

        # Get last 7 days logs
        recent_logs = DailyLog.objects.filter(
            user=user
        ).order_by('-date')[:7]

        high_pain_days = sum(1 for l in recent_logs if l.pain >= 7)
        high_stress_days = sum(1 for l in recent_logs if l.stress == 'high')

        if high_pain_days >= 3:
            print(f"[RISK ALERT] User {user.email} — high pain for {high_pain_days} days")

        if high_stress_days >= 5:
            print(f"[RISK ALERT] User {user.email} — high stress for {high_stress_days} days")

    except Exception as e:
        print(f"[RISK ALERT ERROR] {e}")