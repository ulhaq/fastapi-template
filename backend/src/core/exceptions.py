from datetime import datetime, timezone
from typing import Annotated, Any, Self

from fastapi import HTTPException, Request, status
from pydantic import BaseModel, Field

from src.enums import ErrorCode


class BaseErrorResponse(BaseModel):
    time: Annotated[datetime, Field()]
    path: Annotated[str, Field()]
    method: Annotated[str, Field()]
    error_code: Annotated[str, Field()]

    @classmethod
    def from_exception(
        cls, request: Request, error_code: ErrorCode, **kwargs: Any
    ) -> Self:
        return cls(
            error_code=error_code.code,
            time=datetime.now(timezone.utc),
            path=str(request.url),
            method=request.method,
            **kwargs,
        )


class ErrorResponse(BaseErrorResponse):
    msg: Annotated[str, Field()]


class ValidationErrorResponse(BaseErrorResponse):
    class ValidationDetail(BaseModel):
        error_code: Annotated[str, Field()]
        field: Annotated[list[str], Field()]
        msg: Annotated[str, Field()]
        ctx: Annotated[Any, Field()]

    errors: Annotated[list[ValidationDetail], Field()]


class ClientException(HTTPException):
    error_code: ErrorCode

    def __init__(
        self,
        status_code: int,
        detail: Any = None,
        /,
        *,
        error_code: ErrorCode,
        headers: dict | None = None,
    ) -> None:
        super().__init__(status_code, detail, headers)

        self.error_code = error_code


class ValidationException(ClientException):
    def __init__(
        self,
        detail: Any = "Validation failed",
        /,
        *,
        error_code: ErrorCode = ErrorCode.VALIDATION_ERROR,
        headers: dict | None = None,
    ) -> None:
        super().__init__(
            status.HTTP_400_BAD_REQUEST, detail, error_code=error_code, headers=headers
        )


class NotAuthenticatedException(ClientException):
    def __init__(
        self,
        detail: Any = "Not authenticated",
        /,
        *,
        error_code: ErrorCode = ErrorCode.UNAUTHORIZED,
        headers: dict | None = None,
    ) -> None:
        super().__init__(
            status.HTTP_401_UNAUTHORIZED, detail, error_code=error_code, headers=headers
        )


class PermissionDeniedException(ClientException):
    def __init__(
        self,
        detail: Any = "You are not authorized to perform this action",
        /,
        *,
        error_code: ErrorCode = ErrorCode.PERMISSION_DENIED,
        headers: dict | None = None,
    ) -> None:
        super().__init__(
            status.HTTP_403_FORBIDDEN, detail, error_code=error_code, headers=headers
        )


class NotFoundException(ClientException):
    def __init__(
        self,
        detail: Any = "Resource not found",
        /,
        *,
        error_code: ErrorCode = ErrorCode.RESOURCE_NOT_FOUND,
        headers: dict | None = None,
    ) -> None:
        super().__init__(
            status.HTTP_404_NOT_FOUND, detail, error_code=error_code, headers=headers
        )


class AlreadyExistsException(ClientException):
    def __init__(
        self,
        detail: Any = "Resource already exists",
        /,
        *,
        error_code: ErrorCode = ErrorCode.RESOURCE_ALREADY_EXISTS,
        headers: dict | None = None,
    ) -> None:
        super().__init__(
            status.HTTP_409_CONFLICT, detail, error_code=error_code, headers=headers
        )
