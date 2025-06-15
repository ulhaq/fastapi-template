import logging

from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from src.core.config import settings
from src.core.exceptions import ErrorResponse, InternalServerError

log = logging.getLogger(__name__)


class ErrorHandlingMiddleware:
    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        try:
            await self.app(scope, receive, send)
            return
        except Exception as exc:  # pylint: disable=broad-exception-caught
            query_string = scope.get("query_string")
            log.error(
                "%s %s%s -> %s",
                scope.get("method"),
                scope.get("path"),
                "?" + query_string.decode("utf-8") if query_string else "",
                exc,
                exc_info=settings.log_exc_info,
            )

            detail = None
            if settings.app_debug:
                detail = exc

            response = JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=jsonable_encoder(
                    ErrorResponse(Request(scope), InternalServerError(detail))
                ),
            )

            await response(scope, receive, send)
            return
