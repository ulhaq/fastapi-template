from datetime import datetime, timezone
from typing import Annotated, Any
from fastapi import HTTPException, Request, status
from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    type: Annotated[str, Field()]
    message: Annotated[str, Field()]
    time: Annotated[datetime, Field()]
    path: Annotated[str, Field()]
    method: Annotated[str, Field()]

    def __init__(self, request: Request, exception: Exception, **data) -> None:
        super().__init__(
            type=type(exception).__name__,
            message=str(getattr(exception, "detail", None) or exception),
            time=datetime.now(timezone.utc),
            path=str(request.url),
            method=request.method,
            **data,
        )


class ClientException(HTTPException):
    pass


class AlreadyExistsException(ClientException):
    def __init__(self, detail: Any = None, headers: dict | None = None):
        super().__init__(status.HTTP_409_CONFLICT, detail, headers)


class NotAuthenticatedException(ClientException):
    def __init__(self, detail: Any = None, headers: dict | None = None):
        super().__init__(status.HTTP_401_UNAUTHORIZED, detail, headers)


class NotFoundException(ClientException):
    def __init__(self, detail: Any = None, headers: dict | None = None):
        super().__init__(status.HTTP_404_NOT_FOUND, detail, headers)
