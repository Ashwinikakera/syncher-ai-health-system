from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from apps.dashboard_app.services import get_dashboard_data
from utils.response_format import success_response, error_response


class DashboardView(APIView):
    """
    GET /api/dashboard

    Returns prediction + insights for the logged in user.
    Internally calls Dev3 ML service via services.py

    Response:
    {
        "next_period_date": "2024-03-29",
        "ovulation_window": ["2024-03-14", "2024-03-16"],
        "cycle_regularity_score": 0.85,
        "insights": [
            "Your cycle is regular",
            "High stress may delay cycle"
        ]
    }
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            data = get_dashboard_data(request.user)
            return success_response(data=data)
        except Exception as e:
            return error_response("Could not load dashboard data", status=500)