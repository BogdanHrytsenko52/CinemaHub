from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler


class Conflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "The request conflicts with existing data."
    default_code = "conflict"


def custom_exception_handler(exc, context):
    """Return one predictable JSON envelope for expected API errors."""
    response = exception_handler(exc, context)
    if response is None:
        return response

    status_to_code = {
        400: "bad_request",
        404: "not_found",
        405: "method_not_allowed",
        409: "conflict",
    }
    code = status_to_code.get(response.status_code, "api_error")
    messages = {
        "bad_request": "Request data is invalid.",
        "not_found": "The requested object does not exist.",
        "method_not_allowed": "This HTTP method is not allowed for this endpoint.",
        "conflict": str(getattr(exc, "detail", "The request conflicts with existing data.")),
    }
    response.data = {
        "error": {
            "code": code,
            "message": messages[code],
            "details": response.data,
        }
    }
    return response
