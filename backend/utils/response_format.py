from rest_framework.response import Response
from rest_framework.views import exception_handler


def success_response(data=None, message=None, status=200):
    """
    Standard success response format.
    Usage:
        return success_response(message="User registered successfully")
        return success_response(data={"token": "abc", "is_onboarded": False})
    """
    if message:
        payload = {"message": message}
    else:
        payload = data
    return Response(payload, status=status)


def error_response(message="Something went wrong", status=400):
    """
    Standard error response format.
    Always returns: {"error": "..."}
    Usage:
        return error_response("Invalid data")
        return error_response("User not found", status=404)
    """
    return Response({"error": message}, status=status)


def custom_exception_handler(exc, context):
    """
    Overrides DRF default error format.
    Without this, DRF returns {"detail": "..."} 
    With this, we always return {"error": "..."}
    Plugged into settings.py → REST_FRAMEWORK → EXCEPTION_HANDLER
    """
    response = exception_handler(exc, context)

    if response is not None:
        error_message = None

        # Extract the actual error message from DRF response
        if isinstance(response.data, dict):
            # Try common DRF keys
            error_message = (
                response.data.get('detail') or
                response.data.get('non_field_errors') or
                str(response.data)
            )
        elif isinstance(response.data, list):
            error_message = response.data[0]

        response.data = {"error": str(error_message)}

    return response