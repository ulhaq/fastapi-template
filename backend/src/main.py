import logging
import logging.config
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from src.core.config import settings
from src.core.exceptions import ClientException
from src.core.logging import LOGGING_CONFIG
from src.core.middlewares import ErrorHandlingMiddleware
from src.enums import ErrorCode
from src.routers import auth, company, permission, role, user
from src.schemas.common import ErrorResponse, ValidationDetail, ValidationErrorResponse

logging.config.dictConfig(LOGGING_CONFIG)

log = logging.getLogger(__name__)

if not settings.app_secret:
    raise RuntimeError("Application secret is not set")


app = FastAPI(
    title=settings.app_name,
    debug=settings.app_debug,
    middleware=[
        Middleware(
            CORSMiddleware,
            allow_origins=settings.allow_origins,
            allow_credentials=settings.allow_credentials,
            allow_methods=settings.allow_methods,
            allow_headers=settings.allow_headers,
        ),
        Middleware(ErrorHandlingMiddleware),
    ],
)


@app.exception_handler(HTTPException)
async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
    log.info("%s: %s", exc, request.url, exc_info=settings.log_exc_info)

    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(
            ErrorResponse(
                request,
                error_code=ErrorCode.SERVER_ERROR
                if exc.status_code != 401
                else ErrorCode.UNAUTHORIZED,
                msg=exc.detail,
            )
        ),
        headers=exc.headers,
    )


@app.exception_handler(ClientException)
async def handle_client_exception(
    request: Request, exc: ClientException
) -> JSONResponse:
    log.info("%s: %s", exc, request.url, exc_info=settings.log_exc_info)

    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(
            ErrorResponse(request, error_code=exc.error_code, msg=exc.detail)
        ),
        headers=exc.headers,
    )


@app.exception_handler(ValidationError)
async def handle_validation_error(
    request: Request, exc: ValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder(
            ValidationErrorResponse(
                request,
                error_code=ErrorCode.VALIDATION_ERROR,
                msg=ErrorCode.VALIDATION_ERROR.description,
                errors=exc.errors(),
            )
        ),
        headers={},
    )


@app.exception_handler(RequestValidationError)
async def handle_request_validation_error(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    if any(
        error.get("type", None) == ErrorCode.JSON_INVALID.code for error in exc.errors()
    ):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=jsonable_encoder(
                ErrorResponse(
                    request,
                    error_code=ErrorCode.JSON_INVALID,
                    msg=ErrorCode.JSON_INVALID.description,
                )
            ),
            headers={},
        )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder(
            ValidationErrorResponse(
                request,
                error_code=ErrorCode.VALIDATION_ERROR,
                msg=ErrorCode.VALIDATION_ERROR.description,
                errors=exc.errors(),
            )
        ),
        headers={},
    )


@app.exception_handler(ValueError)
async def handle_value_error(request: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder(
            ErrorResponse(request, error_code=ErrorCode.VALIDATION_ERROR, msg=str(exc))
        ),
        headers={},
    )


app.include_router(auth.router, tags=["Authentication"])
app.include_router(company.router, tags=["Companies"])
app.include_router(user.router, tags=["Users"])
app.include_router(role.router, tags=["Roles"])
app.include_router(permission.router, tags=["Permissions"])


def custom_openapi() -> dict[str, Any]:
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        summary=app.summary,
        description=app.description,
        routes=app.routes,
    )

    openapi_schema["components"]["schemas"]["ErrorResponse"] = (
        ErrorResponse.model_json_schema()
    )

    openapi_schema["components"]["schemas"]["ValidationDetail"] = (
        ValidationDetail.model_json_schema()
    )

    openapi_schema["components"]["schemas"]["ValidationErrorResponse"] = (
        ValidationErrorResponse.model_json_schema(
            ref_template="#/components/schemas/{model}"
        )
    )

    for path_item in openapi_schema["paths"].values():
        for method, operation in path_item.items():
            if "responses" not in operation:
                operation["responses"] = {}

            if "400" not in operation["responses"]:
                operation["responses"]["400"] = {
                    "description": "Bad Request",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                        }
                    },
                }

            if (
                method.lower() in ["get", "put", "delete"]
                and "404" not in operation["responses"]
            ):
                operation["responses"]["404"] = {
                    "description": "Not Found",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                        }
                    },
                }

            if "422" in operation["responses"]:
                operation["responses"]["422"] = {
                    "description": "Validation Error",
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/ValidationErrorResponse"
                            }
                        }
                    },
                }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


setattr(app, "openapi", custom_openapi)
