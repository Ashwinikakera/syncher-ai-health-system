from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from utils.response_format import success_response, error_response
from apps.chatbot_app.rag import get_rag_response
from apps.chatbot_app.llm import generate_chatbot_answer


def get_user_context(user):
    """
    Collect user health context from their logs.
    Simplified to use only DailyLog (which exists).
    """
    from apps.cycle_app.models import CycleHistory
    from apps.log_app.models import DailyLog
    from datetime import date, timedelta

    # Get latest cycle
    latest_cycle = CycleHistory.objects.filter(user=user).order_by('-start_date').first()
    
    # Get latest daily log
    latest_daily_log = DailyLog.objects.filter(user=user).order_by('-date').first()

    # Calculate cycle delay
    cycle_delay = 0
    if latest_cycle:
        try:
            avg_length = user.onboarding.avg_cycle_length
            expected = latest_cycle.start_date + timedelta(days=avg_length)
            today = date.today()
            cycle_delay = max(0, (today - expected).days)
        except Exception:
            cycle_delay = 0

    return {
        "cycle_delay": cycle_delay,
        "stress": latest_daily_log.stress if latest_daily_log else "unknown",
        "sleep": latest_daily_log.sleep if latest_daily_log else "unknown",
        "exercise": latest_daily_log.exercise if latest_daily_log else "unknown",
        "symptoms": latest_daily_log.symptoms if latest_daily_log else "unknown",
    }


class ChatView(APIView):
    """
    Chatbot endpoint : answers user questions with AI
    POST /api/chat/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        question = request.data.get("question", "").strip()

        if not question:
            return error_response("Question is required", status=400)

        try:
            # Get user's actual health context
            user_data = get_user_context(request.user)

            # Format context
            rag_response = get_rag_response(
                user_data=user_data,
                question=question
            )

            # Generate answer using Gen AI
            answer = generate_chatbot_answer(
                user_data=user_data,
                question=question,
                rag_response=rag_response
            )

            return success_response(data={"answer": answer})

        except Exception as e:
            print(f"[ChatView] Error: {e}")
            import traceback
            traceback.print_exc()
            return error_response(str(e), status=500)