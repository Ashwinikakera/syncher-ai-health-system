from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from utils.response_format import success_response, error_response


def get_user_context(user):
    """
    Collects user context for chatbot.
    """
    from apps.cycle_app.models import CycleHistory
    from apps.log_app.models import DailyLog
    from datetime import date, timedelta

    latest_cycle = CycleHistory.objects.filter(
        user=user
    ).order_by('-start_date').first()

    latest_log = DailyLog.objects.filter(
        user=user
    ).order_by('-date').first()

    cycle_delay = 0
    if latest_cycle:
        try:
            avg_length  = user.onboarding.avg_cycle_length
            expected    = latest_cycle.start_date + timedelta(days=avg_length)
            today       = date.today()
            cycle_delay = max(0, (today - expected).days)
        except Exception:
            cycle_delay = 0

    return {
        "cycle_delay": cycle_delay,
        "stress":      latest_log.stress  if latest_log else "unknown",
        "sleep":       latest_log.sleep   if latest_log else 0,
        "pain":        latest_log.pain    if latest_log else 0,
        "mood":        latest_log.mood    if latest_log else "unknown",
    }


def stub_response(user_data, question):
    """
    Stub until Dev3 completes rag.py and llm.py
    """
    question_lower = question.lower()

    if any(w in question_lower for w in ['late', 'delay', 'missed']):
        reasons = []
        if user_data.get('stress') == 'high':
            reasons.append("high stress levels")
        if user_data.get('sleep', 8) < 6:
            reasons.append("low sleep")
        if user_data.get('cycle_delay', 0) > 0:
            reasons.append(f"your cycle is {user_data['cycle_delay']} days delayed")
        answer = f"Based on your logs, {' and '.join(reasons)} may be contributing." if reasons else "Occasional delays are normal. Keep logging for better insights."

    elif any(w in question_lower for w in ['pain', 'cramp']):
        answer = "High pain levels detected. Stay hydrated and rest. Consult a doctor if pain persists."

    elif any(w in question_lower for w in ['mood', 'sad', 'anxious']):
        answer = "Mood changes are common during cycle phases. Your patterns will improve insights over time."

    elif any(w in question_lower for w in ['sleep', 'tired', 'fatigue']):
        sleep = user_data.get('sleep', 8)
        answer = f"You've been averaging {sleep} hours of sleep. Low sleep can affect cycle regularity." if sleep < 6 else "Your sleep looks okay. Keep maintaining healthy habits."

    else:
        answer = "I'm here to help with your menstrual health questions. Keep logging daily for personalized insights."

    return {"answer": answer}


class ChatView(APIView):
    """
    POST /api/chat
    Request:  { "question": "Why is my period late?" }
    Response: { "answer": "..." }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        question = request.data.get('question', '').strip()

        if not question:
            return error_response("Question is required", status=400)

        user_data = get_user_context(request.user)

        try:
            # -------------------------------------------------------
            # DEV3 INTEGRATION POINT
            # When rag.py and llm.py are ready, uncomment below
            # -------------------------------------------------------
            # from apps.chatbot_app.services.rag import get_rag_response
            # result = get_rag_response(
            #     user_data = user_data,
            #     question  = question
            # )
            # return success_response(data=result)
            # -------------------------------------------------------

            # STUB — until Dev3 completes rag.py + llm.py
            result = stub_response(user_data, question)
            return success_response(data=result)

        except Exception as e:
            return error_response("Could not process your question", status=500)