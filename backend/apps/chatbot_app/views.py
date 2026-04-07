from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from apps.chatbot_app.services import get_chat_response
from utils.response_format import success_response, error_response


class ChatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        question = request.data.get("question", "").strip()

        if not question:
            return error_response("Question is required", status=400)

        try:
            result = get_chat_response(request.user, question)
            return success_response(data=result)
        except Exception as e:
            print(f"[ChatView] Error: {e}")
            return error_response(str(e), status=500)
