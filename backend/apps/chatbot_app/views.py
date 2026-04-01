from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from apps.chatbot_app.services import get_chat_response
from utils.response_format import success_response, error_response


class ChatView(APIView):
    """
    POST /api/chat

    Request:
    {
        "question": "Why is my period late?"
    }

    Response:
    {
        "answer": "Your recent high stress levels and low sleep
                   may be contributing to the delay."
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        question = request.data.get('question', '').strip()

        if not question:
            return error_response("Question is required", status=400)

        try:
            result = get_chat_response(request.user, question)
            return success_response(data=result)
        except Exception as e:
            return error_response("Could not process your question", status=500)