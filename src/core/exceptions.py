from datetime import datetime, timezone
from typing import Annotated, Any

from fastapi import HTTPException, Request, status
from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    type: Annotated[str, Field()]
    msg: Annotated[str, Field()]
    time: Annotated[datetime, Field()]
    path: Annotated[str, Field()]
    method: Annotated[str, Field()]

    def __init__(self, request: Request, exc: Exception, **data) -> None:
        super().__init__(
            type=type(exc).__name__,
            msg=str(getattr(exc, "detail", None) or exc),
            time=datetime.now(timezone.utc),
            path=str(request.url),
            method=request.method,
            **data,
        )


class ClientException(HTTPException):
    pass


class BusinessLogicException(ClientException):
    def __init__(self, detail: Any = None, headers: dict | None = None) -> None:
        super().__init__(status.HTTP_400_BAD_REQUEST, detail, headers)


class ValidationException(ClientException):
    def __init__(
        self, detail: Any = "Validation failed", headers: dict | None = None
    ) -> None:
        super().__init__(status.HTTP_400_BAD_REQUEST, detail, headers)


class NotAuthenticatedException(ClientException):
    def __init__(
        self, detail: Any = "Not authenticated", headers: dict | None = None
    ) -> None:
        super().__init__(status.HTTP_401_UNAUTHORIZED, detail, headers)


class PermissionDeniedException(ClientException):
    def __init__(
        self,
        detail: Any = "You are not authorized to perform this action",
        headers: dict | None = None,
    ) -> None:
        super().__init__(status.HTTP_403_FORBIDDEN, detail, headers)


class NotFoundException(ClientException):
    def __init__(
        self, detail: Any = "Resource not found", headers: dict | None = None
    ) -> None:
        super().__init__(status.HTTP_404_NOT_FOUND, detail, headers)


class AlreadyExistsException(ClientException):
    def __init__(
        self, detail: Any = "Resource already exists", headers: dict | None = None
    ) -> None:
        super().__init__(status.HTTP_409_CONFLICT, detail, headers)


class ServerException(HTTPException):
    pass


class InternalServerError(ServerException):
    def __init__(
        self,
        detail: Any = "Something went wrong on our end",
        headers: dict | None = None,
    ) -> None:
        super().__init__(status.HTTP_500_INTERNAL_SERVER_ERROR, detail, headers)
