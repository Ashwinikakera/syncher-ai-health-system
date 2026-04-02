from apps.cycle_app.models import CycleHistory
from apps.log_app.models import DailyLog


def get_user_context_for_chat(user):
    """
    Collects relevant user data to send as context
    to Dev3's RAG pipeline + Ollama (phi3-mini).

    This is the internal data format from the contract:
    {
        "user_data": {
            "cycle_delay": 4,
            "stress": "high",
            "sleep": 5
        },
        "question": "Why is my period late?"
    }
    """

    # Get latest cycle
    latest_cycle = CycleHistory.objects.filter(
        user=user
    ).order_by('-start_date').first()

    # Get latest daily log
    latest_log = DailyLog.objects.filter(
        user=user
    ).order_by('-date').first()

    # Calculate cycle delay if possible
    cycle_delay = 0
    if latest_cycle:
        from datetime import date, timedelta
        try:
            avg_length  = user.profile.avg_cycle_length
            expected    = latest_cycle.start_date + timedelta(days=avg_length)
            today       = date.today()
            cycle_delay = max(0, (today - expected).days)
        except Exception:
            cycle_delay = 0

    user_data = {
        "cycle_delay": cycle_delay,
        "stress":      latest_log.stress   if latest_log else "unknown",
        "sleep":       latest_log.sleep    if latest_log else 0,
        "pain":        latest_log.pain     if latest_log else 0,
        "mood":        latest_log.mood     if latest_log else "unknown",
    }

    return user_data


def get_chat_response(user, question):
    """
    Main function called by chatbot view.

    Tries to call Dev3's RAG + Ollama pipeline.
    Falls back to stub response if not ready yet.

    Returns exact contract shape:
    {
        "answer": "Your recent high stress levels and low sleep
                   may be contributing to the delay."
    }
    """
    user_data = get_user_context_for_chat(user)

    try:
        # -------------------------------------------------------
        # DEV3 INTEGRATION POINT
        # When Dev3 is ready, uncomment below and remove the stub
        # -------------------------------------------------------
        # import sys
        # sys.path.append('../ml_service')
        # from chatbot.rag import get_rag_response
        #
        # answer = get_rag_response(
        #     user_data = user_data,
        #     question  = question
        # )
        # return {"answer": answer}
        # -------------------------------------------------------

        # STUB — used until Dev3 RAG is ready
        return _stub_chat_response(user_data, question)

    except Exception as e:
        return _stub_chat_response(user_data, question)


def _stub_chat_response(user_data, question):
    """
    Basic rule based responses until Dev3 RAG is ready.
    Keeps Dev2 unblocked for chatbot UI development.
    """
    question_lower = question.lower()

    # Late period
    if any(word in question_lower for word in ['late', 'delay', 'missed', 'overdue']):
        reasons = []
        if user_data.get('stress') == 'high':
            reasons.append("high stress levels")
        if user_data.get('sleep', 8) < 6:
            reasons.append("low sleep")
        if user_data.get('cycle_delay', 0) > 0:
            reasons.append(f"your cycle is {user_data['cycle_delay']} days delayed")

        if reasons:
            answer = f"Based on your recent logs, {' and '.join(reasons)} may be contributing to the delay."
        else:
            answer = "Occasional cycle delays are normal. Keep logging your symptoms for better insights."

    # Pain
    elif any(word in question_lower for word in ['pain', 'cramp', 'hurt']):
        pain = user_data.get('pain', 0)
        if pain >= 7:
            answer = "Your recent pain levels are high. Consider consulting a doctor if pain persists."
        else:
            answer = "Mild cramping is normal during your cycle. Stay hydrated and rest when needed."

    # Mood
    elif any(word in question_lower for word in ['mood', 'sad', 'anxious', 'emotional']):
        answer = "Mood changes are common during different cycle phases. Your logged mood patterns will help us give better insights over time."

    # Sleep
    elif any(word in question_lower for word in ['sleep', 'tired', 'fatigue']):
        sleep = user_data.get('sleep', 8)
        if sleep < 6:
            answer = f"You've been averaging {sleep} hours of sleep recently. Low sleep can affect your cycle regularity."
        else:
            answer = "Your sleep looks okay. Keep maintaining healthy sleep habits."

    # Default
    else:
        answer = "I'm here to help with your menstrual health questions. Keep logging your symptoms daily for more personalized insights."

    return {"answer": answer}