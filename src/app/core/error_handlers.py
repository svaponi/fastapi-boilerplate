import logging

import fastapi
import starlette
import starlette.exceptions
import starlette.responses
import starlette.status

from app.core.request_context import RequestContext


def build_error_response(
    status_code: int | None = None,
    message: str | None = None,
    **kwargs,
) -> fastapi.responses.JSONResponse:
    if not status_code:
        status_code = 500
    body = {
        "status_code": status_code,
        "message": message,
    }
    body.update(kwargs)
    body["request_id"] = RequestContext.get_request_id()
    return fastapi.responses.JSONResponse(body, status_code=status_code)


def setup_error_handlers(app: fastapi.FastAPI):

    _logger = logging.getLogger("app.exception")

    async def _value_error_handler(
        _: fastapi.Request, exc: ValueError
    ) -> fastapi.responses.JSONResponse:
        _logger.exception(exc)
        return build_error_response(
            status_code=starlette.status.HTTP_400_BAD_REQUEST,
            message=str(exc),
        )

    async def _internal_server_error_handler(
        _: fastapi.Request, exc: Exception
    ) -> fastapi.responses.JSONResponse:
        _logger.exception(exc)
        return build_error_response(
            status_code=starlette.status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Internal server error",
        )

    async def _internal_http_exception_handler(
        _: fastapi.Request, exc: fastapi.HTTPException
    ) -> fastapi.responses.JSONResponse:
        _logger.exception(exc)
        return build_error_response(
            status_code=exc.status_code,
            message=exc.detail,
        )

    app.add_exception_handler(ValueError, _value_error_handler)
    app.add_exception_handler(Exception, _internal_server_error_handler)
    # Override starlette.exceptions.HTTPException response with our handler. Noe that fastapi.HTTPException inherits
    # from starlette.exceptions.HTTPException. See https://fastapi.tiangolo.com/tutorial/handling-errors
    app.add_exception_handler(
        starlette.exceptions.HTTPException, _internal_http_exception_handler
    )
