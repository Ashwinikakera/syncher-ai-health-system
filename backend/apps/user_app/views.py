from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from apps.user_app.models import UserProfile
from apps.user_app.serializers import OnboardingSerializer
from utils.response_format import success_response, error_response


class OnboardingView(APIView):
    """
    POST /api/onboarding
    Used only once — first time user logs in.

    Request:
    {
        "age": 22,
        "weight": 55,
        "cycle_history": ["2024-01-01", "2024-01-28", "2024-02-25"],
        "avg_cycle_length": 28
    }

    Response:
    {
        "message": "Onboarding completed"
    }
    """
    permission_classes = [IsAuthenticated]  # Must be logged in

    def post(self, request):

        # Check if user already onboarded
        if request.user.is_onboarded:
            return error_response("User already onboarded", status=400)

        serializer = OnboardingSerializer(data=request.data)

        if serializer.is_valid():
            # Save profile linked to current user
            UserProfile.objects.create(
                user             = request.user,
                age              = serializer.validated_data['age'],
                weight           = serializer.validated_data['weight'],
                cycle_history    = serializer.validated_data['cycle_history'],
                avg_cycle_length = serializer.validated_data['avg_cycle_length']
            )

            # Mark user as onboarded
            request.user.is_onboarded = True
            request.user.save()

            return success_response(message="Onboarding completed", status=201)

        first_error = list(serializer.errors.values())[0][0]
        return error_response(str(first_error), status=400)