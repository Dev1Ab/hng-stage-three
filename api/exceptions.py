from rest_framework.views import exception_handler
from rest_framework.exceptions import Throttled
from rest_framework.response import Response

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if isinstance(exc, Throttled):
        return Response({
            "status": "error",
            "message": "Rate limit exceeded. Try again later."
        }, status=429)

    if response is not None:
        message = ""

        if isinstance(response.data, dict):
            
            message = next(iter(response.data.values()))
            if isinstance(message, list):
                message = message[0]
        else:
            message = str(response.data)

        response.data = {
            "status": "error",
            "message": message
        }

    return response