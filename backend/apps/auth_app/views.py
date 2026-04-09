from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

from apps.auth_app.models import User, Onboarding
from apps.auth_app.serializers import (
    RegisterSerializer,
    LoginSerializer,
    OnboardingSerializer
)
from utils.response_format import success_response, error_response


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token)


class RegisterView(APIView):
    """
    POST /api/register
    Request:
    {
        "username": "user1",
        "email": "user@gmail.com",
        "password": "123456",
        "confirm_password": "123456"
    }
    Response:
    {
        "message": "User registered successfully"
    }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return success_response(message="User registered successfully", status=201)

        first_error = list(serializer.errors.values())[0][0]
        return error_response(str(first_error), status=400)


class LoginView(APIView):
    """
    POST /api/login
    Request:
    {
        "email": "user@gmail.com",
        "password": "123456"
    }
    Response:
    {
        "token": "jwt_token_here",
        "is_onboarded": false
    }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if not serializer.is_valid():
            first_error = list(serializer.errors.values())[0][0]
            return error_response(str(first_error), status=400)

        email    = serializer.validated_data['email']
        password = serializer.validated_data['password']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return error_response("Invalid email or password", status=401)

        user = authenticate(request, username=email, password=password)
        if user is None:
            return error_response("Invalid email or password", status=401)

        token = get_tokens_for_user(user)

        return success_response(data={
            "token":        token,
            "is_onboarded": user.is_onboarded
        })


class OnboardingView(APIView):
    """
    POST /api/onboarding
    Request:
    {
        "age": 22,
        "weight": 55,
        "cycle_history": [
            {"start_date": "2024-01-01", "end_date": "2024-01-05"},
            {"start_date": "2024-01-28", "end_date": "2024-02-01"}
        ],
        "avg_cycle_length": 28,
        "pain": 3,
        "mood": "low",
        "flow": "medium",
        "medical_condition": "PCOS",
        "medical_notes": "missed periods in last 6 months"
    }
    Response:
    {
        "message": "Onboarding completed"
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.is_onboarded:
            return error_response("User already onboarded", status=400)

        serializer = OnboardingSerializer(data=request.data)

        if serializer.is_valid():
            # Save onboarding data
            Onboarding.objects.create(
                user              = request.user,
                age               = serializer.validated_data['age'],
                weight            = serializer.validated_data['weight'],
                cycle_history     = serializer.validated_data['cycle_history'],
                avg_cycle_length  = serializer.validated_data['avg_cycle_length'],
                pain              = serializer.validated_data['pain'],
                mood              = serializer.validated_data['mood'],
                flow              = serializer.validated_data['flow'],
                medical_condition = serializer.validated_data.get('medical_condition', ''),
                medical_notes     = serializer.validated_data.get('medical_notes', '')
            )

            # Mark user as onboarded
            request.user.is_onboarded = True
            request.user.save()

            return success_response(message="Onboarding completed", status=201)

        first_error = list(serializer.errors.values())[0][0]
        return error_response(str(first_error), status=400)