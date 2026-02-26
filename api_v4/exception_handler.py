from django.http.response import JsonResponse
from rest_framework.views import exception_handler

from api_v3.exceptions import NotAllowedAction


def custom_exception_handler(exc, context):
    if isinstance(exc, NotAllowedAction):
        r = JsonResponse({"detail": f"Action {exc.method} is not allowed."})
        r.status_code = 400
        return r
    response = exception_handler(exc, context)
    return response
