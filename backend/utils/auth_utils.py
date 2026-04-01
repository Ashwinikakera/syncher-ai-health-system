from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from apps.auth_app.models import User


def get_tokens_for_user(user):
    """
    Generates both access and refresh tokens for a user.
    Returns:
    {
        "access":  "eyJ...",
        "refresh": "eyJ..."
    }
    """
    refresh = RefreshToken.for_user(user)
    return {
        "access":  str(refresh.access_token),
        "refresh": str(refresh)
    }


def get_user_from_token(token):
    """
    Extracts user from a JWT access token string.
    Returns User object or None if invalid.

    Usage:
        user = get_user_from_token(request.headers.get('Authorization').split(' ')[1])
    """
    try:
        from rest_framework_simplejwt.tokens import AccessToken
        decoded = AccessToken(token)
        user_id = decoded['user_id']
        return User.objects.get(id=user_id)
    except (TokenError, User.DoesNotExist, Exception):
        return None


def is_token_valid(token):
    """
    Checks if a JWT token is valid and not expired.
    Returns True or False.
    """
    try:
        from rest_framework_simplejwt.tokens import AccessToken
        AccessToken(token)
        return True
    except TokenError:
        return False