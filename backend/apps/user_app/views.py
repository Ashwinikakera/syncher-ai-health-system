from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from apps.user_app.models import UserProfile
from apps.user_app.serializers import OnboardingSerializer
from utils.response_format import success_response, error_response
from apps.cycle_app.models import CycleHistory
from datetime import datetime, timedelta


class OnboardingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        if request.user.is_onboarded:
            return error_response("User already onboarded", status=400)

        serializer = OnboardingSerializer(data=request.data)

        if serializer.is_valid():

            avg_cycle_length = serializer.validated_data['avg_cycle_length']
            cycle_history    = serializer.validated_data['cycle_history']

            # Save profile
            UserProfile.objects.create(
                user             = request.user,
                age              = serializer.validated_data['age'],
                weight           = serializer.validated_data['weight'],
                cycle_history    = cycle_history,
                avg_cycle_length = avg_cycle_length
            )

            # ── FIX 2: Save each cycle to CycleHistory table ──────
            for i, start_date_str in enumerate(cycle_history):
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                end_date   = start_date + timedelta(days=5)  # default period length

                # cycle_length = gap to next cycle, or avg for last one
                if i < len(cycle_history) - 1:
                    next_start   = datetime.strptime(cycle_history[i + 1], "%Y-%m-%d").date()
                    cycle_length = (next_start - start_date).days
                else:
                    cycle_length = avg_cycle_length

                CycleHistory.objects.create(
                    user         = request.user,
                    start_date   = start_date,
                    end_date     = end_date,
                    cycle_length = cycle_length,
                )
            # ─────────────────────────────────────────────────────

            # Mark user as onboarded
            request.user.is_onboarded = True
            request.user.save()

            return success_response(message="Onboarding completed", status=201)

        first_error = list(serializer.errors.values())[0][0]
        return error_response(str(first_error), status=400)