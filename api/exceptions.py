from rest_framework.views import exception_handler

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

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