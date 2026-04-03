from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

from apps.auth_app.models import User
from apps.auth_app.serializers import RegisterSerializer, LoginSerializer
from utils.response_format import success_response, error_response


def get_tokens_for_user(user):
    """
    Generates JWT token for a user.
    Returns access token string.
    """
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token)


class RegisterView(APIView):
    """
    POST /api/register
    Request:
    {
        "email": "user@gmail.com",
        "password": "123456",
        "confirm_password": "123456"
    }
    Response:
    {
        "message": "User registered successfully"
    }
    """
    permission_classes = [AllowAny]  # No auth needed to register

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return success_response(message="User registered successfully", status=201)

        # Return first error message
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
    permission_classes = [AllowAny]  # No auth needed to login

    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if not serializer.is_valid():
            first_error = list(serializer.errors.values())[0][0]
            return error_response(str(first_error), status=400)

        email    = serializer.validated_data['email']
        password = serializer.validated_data['password']

        # Check if user exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return error_response("Invalid email or password", status=401)

        # Check password
        user = authenticate(request, username=email, password=password)
        if user is None:
            return error_response("Invalid email or password", status=401)

        # Generate token
        token = get_tokens_for_user(user)

        return success_response(data={
            "token":        token,
            "is_onboarded": user.is_onboarded
        })