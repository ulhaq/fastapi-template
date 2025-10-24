import logging

from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from src.core.config import settings
from src.core.exceptions import BaseErrorResponse, ErrorResponse
from src.enums import ErrorCode

log = logging.getLogger(__name__)


class ErrorHandlingMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        response_started = False

        async def send_wrapper(message: Message) -> None:
            nonlocal response_started, send

            if message["type"] == "http.response.body":
                response_started = True

            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
            return
        except Exception as exc:  # pylint: disable=broad-exception-caught
            await self.process_exception(scope, receive, send, response_started, exc)
            return

    async def process_exception(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
        response_started: bool,
        exc: Exception,
    ) -> None:
        query_string = (
            "?" + scope.get("query_string", b"").decode("utf-8")
            if scope.get("query_string")
            else ""
        )
        log.error(
            "%s %s%s -> %s",
            scope.get("method"),
            scope.get("path"),
            query_string,
            exc,
            exc_info=settings.log_exc_info,
        )

        error_content: BaseErrorResponse | ErrorResponse
        if not settings.app_debug:
            error_content = BaseErrorResponse.from_exception(
                Request(scope), error_code=ErrorCode.SERVER_ERROR
            )
        else:
            error_content = ErrorResponse.from_exception(
                Request(scope), error_code=ErrorCode.SERVER_ERROR, msg=str(exc)
            )

        response = JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=jsonable_encoder(error_content),
        )

        if not response_started:
            await response(scope, receive, send)
