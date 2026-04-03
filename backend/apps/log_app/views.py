from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from apps.log_app.models import DailyLog
from apps.log_app.serializers import DailyLogSerializer
from utils.response_format import success_response, error_response


class DailyLogView(APIView):
    """
    POST /api/daily-log — save a daily health log
    GET  /api/daily-log — get all logs for this user
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Request:
        {
            "date": "2024-03-10",
            "pain": 3,
            "mood": "low",
            "flow": "medium",
            "sleep": 6,
            "stress": "high",
            "exercise": "light"
        }
        Response:
        {
            "message": "Log saved"
        }
        """
        serializer = DailyLogSerializer(data=request.data)

        if serializer.is_valid():
            # Check if log already exists for this date
            date = serializer.validated_data['date']
            if DailyLog.objects.filter(user=request.user, date=date).exists():
                return error_response("Log already exists for this date", status=400)

            serializer.save(user=request.user)
            return success_response(message="Log saved", status=201)

        first_error = list(serializer.errors.values())[0][0]
        return error_response(str(first_error), status=400)

    def get(self, request):
        """
        Response:
        {
            "logs": [
                {
                    "date": "2024-03-10",
                    "pain": 3,
                    "mood": "low",
                    "flow": "medium",
                    "sleep": 6,
                    "stress": "high",
                    "exercise": "light"
                }
            ]
        }
        """
        logs = DailyLog.objects.filter(user=request.user)
        serializer = DailyLogSerializer(logs, many=True)
        return success_response(data={"logs": serializer.data})