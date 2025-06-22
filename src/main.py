import logging
import logging.config

from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.core.config import settings
from src.core.exceptions import ErrorResponse
from src.core.logging import LOGGING_CONFIG
from src.core.middlewares import ErrorHandlingMiddleware
from src.routers import auth, permission, role, user

logging.config.dictConfig(LOGGING_CONFIG)

log = logging.getLogger(__name__)

if not settings.app_secret:
    raise RuntimeError("Application secret is not set")


app = FastAPI(
    title=settings.app_name,
    debug=settings.app_debug,
    middleware=[
        Middleware(ErrorHandlingMiddleware),
        Middleware(
            CORSMiddleware,
            allow_origins=settings.allow_origins,
            allow_credentials=settings.allow_credentials,
            allow_methods=settings.allow_methods,
            allow_headers=settings.allow_headers,
        ),
    ],
)


@app.exception_handler(HTTPException)
async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
    log.info("%s: %s", exc, request.url, exc_info=settings.log_exc_info)

    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(ErrorResponse(request, exc)),
        headers=exc.headers,
    )


app.include_router(auth.router, tags=["Authentication"])
app.include_router(role.router, tags=["Roles"])
app.include_router(permission.router, tags=["Permissions"])
app.include_router(user.router, tags=["Users"])
