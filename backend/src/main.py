import logging
import logging.config

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.routers import company
from src.core.config import settings
from src.core.exceptions import ClientException, ErrorResponse, ValidationErrorResponse
from src.core.logging import LOGGING_CONFIG
from src.core.middlewares import ErrorHandlingMiddleware
from src.enums import ErrorCode
from src.routers import auth, permission, role, user

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
            ErrorResponse.from_exception(
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
            ErrorResponse.from_exception(
                request, error_code=exc.error_code, msg=exc.detail
            )
        ),
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def handle_validation_exception(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder(
            ValidationErrorResponse.from_exception(
                request,
                error_code=ErrorCode.VALIDATION_ERROR,
                errors=[
                    ValidationErrorResponse.ValidationDetail(
                        error_code=error["type"],
                        field=error["loc"],
                        msg=error["msg"],
                        ctx=error["ctx"] if "ctx" in error else [],
                    )
                    for error in exc.errors()
                ],
            )
        ),
        headers={},
    )


app.include_router(auth.router, tags=["Authentication"])
app.include_router(company.router, tags=["Companies"])
app.include_router(user.router, tags=["Users"])
app.include_router(role.router, tags=["Roles"])
app.include_router(permission.router, tags=["Permissions"])
