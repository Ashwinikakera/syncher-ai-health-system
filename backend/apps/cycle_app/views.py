from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from apps.cycle_app.models import CycleHistory, PredictionFeedback
from apps.cycle_app.serializers import (
    CycleStartSerializer,
    CycleEndSerializer,
    CycleListSerializer,
    PredictionFeedbackSerializer
)
from utils.response_format import success_response, error_response


class CycleStartView(APIView):
    """
    POST /api/cycle/start
    Request:  { "start_date": "2024-03-01" }
    Response: { "message": "Cycle started" }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CycleStartSerializer(data=request.data)

        if serializer.is_valid():
            # Check if there's already an open cycle (no end_date)
            open_cycle = CycleHistory.objects.filter(
                user     = request.user,
                end_date = None
            ).first()

            if open_cycle:
                return error_response("Please end your current cycle first", status=400)

            # Create new cycle with just start_date
            cycle = CycleHistory.objects.create(
                user       = request.user,
                start_date = serializer.validated_data['start_date']
            )

            # Calculate cycle length
            cycle.cycle_length = cycle.calculate_cycle_length()
            cycle.save()

            return success_response(message="Cycle started", status=201)

        first_error = list(serializer.errors.values())[0][0]
        return error_response(str(first_error), status=400)


class CycleEndView(APIView):
    """
    POST /api/cycle/end
    Request:  { "end_date": "2024-03-05" }
    Response: { "message": "Cycle ended" }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CycleEndSerializer(data=request.data)

        if serializer.is_valid():
            # Find the open cycle
            open_cycle = CycleHistory.objects.filter(
                user     = request.user,
                end_date = None
            ).first()

            if not open_cycle:
                return error_response("No active cycle found. Please start a cycle first.", status=400)

            end_date = serializer.validated_data['end_date']

            # Validate end_date is after start_date
            if end_date <= open_cycle.start_date:
                return error_response("end_date must be after start_date", status=400)

            open_cycle.end_date = end_date
            open_cycle.save()

            return success_response(message="Cycle ended", status=200)

        first_error = list(serializer.errors.values())[0][0]
        return error_response(str(first_error), status=400)


class CycleListView(APIView):
    """
    GET /api/cycle
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
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cycles     = CycleHistory.objects.filter(user=request.user)
        serializer = CycleListSerializer(cycles, many=True)
        return success_response(data={"cycles": serializer.data})


class PredictionFeedbackView(APIView):
    """
    POST /api/prediction-feedback
    Request:
    {
        "prediction_correct": false,
        "actual_date": "2024-03-30"
    }
    Response:
    {
        "message": "Feedback saved"
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PredictionFeedbackSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(user=request.user)
            return success_response(message="Feedback saved", status=201)

        first_error = list(serializer.errors.values())[0][0]
        return error_response(str(first_error), status=400)