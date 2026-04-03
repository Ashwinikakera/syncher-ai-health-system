from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from apps.cycle_app.models import CycleHistory
from apps.cycle_app.serializers import CycleSerializer
from utils.response_format import success_response, error_response


class CycleView(APIView):
    """
    POST /api/cycle — log a new period
    GET  /api/cycle — get all cycles for this user
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Request:
        {
            "start_date": "2024-03-01",
            "end_date": "2024-03-05"
        }
        Response:
        {
            "message": "Cycle saved"
        }
        """
        serializer = CycleSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(user=request.user)
            return success_response(message="Cycle saved", status=201)

        first_error = list(serializer.errors.values())[0][0]
        return error_response(str(first_error), status=400)

    def get(self, request):
        """
        Response:
        {
            "cycles": [
                {
                    "start_date": "2024-03-01",
                    "end_date": "2024-03-05",
                    "cycle_length": 28
                }
            ]
        }
        """
        cycles = CycleHistory.objects.filter(user=request.user)
        serializer = CycleSerializer(cycles, many=True)
        return success_response(data={"cycles": serializer.data})