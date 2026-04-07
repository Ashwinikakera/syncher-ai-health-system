from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from apps.dashboard_app.services import get_dashboard_data
from utils.response_format import success_response, error_response


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            data = get_dashboard_data(request.user)
            return success_response(data=data)
        except Exception as e:
            print(f"DASHBOARD ERROR: {e}")
            import traceback
            traceback.print_exc()
            return error_response(str(e), status=500)