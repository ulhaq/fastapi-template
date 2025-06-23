import logging

from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from src.core.config import settings
from src.core.exceptions import ErrorResponse, InternalServerError

log = logging.getLogger(__name__)


class ErrorHandlingMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        try:
            await self.app(scope, receive, send)
            return
        except Exception as exc:  # pylint: disable=broad-exception-caught
            await self.process_exception(scope, receive, send, exc)
            return

    async def process_exception(
        self, scope: Scope, receive: Receive, send: Send, exc: Exception
    ) -> None:
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
