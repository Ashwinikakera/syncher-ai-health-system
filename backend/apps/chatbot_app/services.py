# backend/apps/chatbot_app/services.py

from apps.cycle_app.models import CycleHistory
from apps.log_app.models import DailyLog


def get_chat_response(user, question):
    """
    Main function called by chatbot view.
    Calls Dev3's RAG pipeline directly.

    Returns exact contract shape:
    {
        "answer": "Your recent high stress levels and low sleep
                   may be contributing to the delay."
    }
    """
    try:
        # Build the data format Dev3's rag_chat expects
        cycle_records = list(
            CycleHistory.objects.filter(user=user)
            .order_by("start_date")
            .values("start_date", "cycle_length")
        )

        log_records = list(
            DailyLog.objects.filter(user=user)
            .order_by("-date")[:30]
            .values("date", "pain", "mood", "flow", "sleep", "stress", "exercise")
        )

        # Convert date objects to strings for JSON serialization
        for r in cycle_records:
            r["start_date"] = str(r["start_date"])
        for r in log_records:
            r["date"] = str(r["date"])

        user_data = {
            "cycle_records": cycle_records,
            "log_records":   log_records,
        }

        # ── DEV3 INTEGRATION POINT ────────────────────────────────
        from ml_service.chatbot.rag import rag_chat
        return rag_chat(question=question, user_data=user_data)


    except ImportError as e:
        # ml_service not found — path issue
        print(f"[chatbot_service] ImportError: {e}")
        return _stub_chat_response(user, question)

    except ConnectionError as e:
        # Groq API unreachable
        print(f"[chatbot_service] ConnectionError: {e}")
        return _stub_chat_response(user, question)

    except RuntimeError as e:
        # Groq API error (from groq_client.py)
        print(f"[chatbot_service] RuntimeError: {e}")
        return _stub_chat_response(user, question)

    except Exception as e:
        # Any other unexpected error
        print(f"[chatbot_service] Unexpected error: {e}")
        return _stub_chat_response(user, question)


def _stub_chat_response(user, question):
    """
    Fallback rule-based responses if Dev3 RAG is unreachable.
    Keeps Dev2 unblocked for chatbot UI development.
    """
    # Get latest log for basic context
    latest_log = DailyLog.objects.filter(user=user).order_by("-date").first()

    question_lower = question.lower()

    # Late period
    if any(word in question_lower for word in ["late", "delay", "missed", "overdue"]):
        reasons = []
        if latest_log:
            if latest_log.stress == "high":
                reasons.append("high stress levels")
            if latest_log.sleep and latest_log.sleep < 6:
                reasons.append("low sleep")
        if reasons:
            answer = f"Based on your recent logs, {' and '.join(reasons)} may be contributing to the delay."
        else:
            answer = "Occasional cycle delays are normal. Keep logging your symptoms for better insights."

    # Pain
    elif any(word in question_lower for word in ["pain", "cramp", "hurt"]):
        pain = latest_log.pain if latest_log else 0
        if pain and pain >= 7:
            answer = "Your recent pain levels are high. Consider consulting a doctor if pain persists."
        else:
            answer = "Mild cramping is normal during your cycle. Stay hydrated and rest when needed."

    # Mood
    elif any(word in question_lower for word in ["mood", "sad", "anxious", "emotional"]):
        answer = "Mood changes are common during different cycle phases. Your logged mood patterns will help us give better insights over time."

    # Sleep
    elif any(word in question_lower for word in ["sleep", "tired", "fatigue"]):
        sleep = latest_log.sleep if latest_log else 8
        if sleep and sleep < 6:
            answer = f"You've been averaging {sleep} hours of sleep recently. Low sleep can affect your cycle regularity."
        else:
            answer = "Your sleep looks okay. Keep maintaining healthy sleep habits."

    # Default
    else:
        answer = "I'm here to help with your menstrual health questions. Keep logging your symptoms daily for more personalized insights."

    return {"answer": answer}