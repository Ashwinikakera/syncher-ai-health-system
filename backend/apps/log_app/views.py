from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from apps.log_app.models import DailyLog, CycleLog
from apps.log_app.serializers import DailyLogSerializer, CycleLogSerializer
from utils.response_format import success_response, error_response


class DailyLogView(APIView):
    """
    POST /api/daily-log — save a daily health log (non-period days)
    GET  /api/daily-log — get all daily logs for this user
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Request:
        {
            "date": "2024-03-10",
            "sleep": 6,
            "stress": "high",
            "exercise": "light",
            "medication": "yes",
            "medication_details": "painkiller",
            "food": "junk",
            "routine_change": "yes",
            "routine_details": "travel",
            "white_discharge": "medium",
            "hydration": "yes",
            "symptoms": ["cramps", "fatigue"]
        }
        Response: { "message": "Log saved" }
        """
        serializer = DailyLogSerializer(data=request.data)

        if serializer.is_valid():
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
            "logs": [...]
        }
        """
        logs       = DailyLog.objects.filter(user=request.user)
        serializer = DailyLogSerializer(logs, many=True)
        return success_response(data={"logs": serializer.data})


class CycleLogView(APIView):
    """
    POST /api/cycle-log — save a period day log
    GET  /api/cycle-log — get all period day logs for this user
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Request:
        {
            "date": "2024-03-02",
            "pain": 4,
            "mood": "low",
            "flow": "heavy",
            "sleep": 5,
            "stress": "high",
            "exercise": "none",
            "medication": "yes",
            "medication_details": "tablet",
            "hydration": "no"
        }
        Response: { "message": "Cycle log saved" }
        """
        serializer = CycleLogSerializer(data=request.data)

        if serializer.is_valid():
            date = serializer.validated_data['date']

            if CycleLog.objects.filter(user=request.user, date=date).exists():
                return error_response("Cycle log already exists for this date", status=400)

            serializer.save(user=request.user)
            return success_response(message="Cycle log saved", status=201)

        first_error = list(serializer.errors.values())[0][0]
        return error_response(str(first_error), status=400)

    def get(self, request):
        """
        Response:
        {
            "cycle_logs": [...]
        }
        """
        logs       = CycleLog.objects.filter(user=request.user)
        serializer = CycleLogSerializer(logs, many=True)
        return success_response(data={"cycle_logs": serializer.data})