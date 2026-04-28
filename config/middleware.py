import time
import logging

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()

        response = self.get_response(request)

        duration = (time.time() - start_time) * 1000  # ms

        method = request.method
        path = request.get_full_path()
        status_code = response.status_code

        logger.info(
            f"{method} {path} {status_code} {duration:.2f}ms"
        )

        return response