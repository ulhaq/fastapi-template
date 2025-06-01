import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.concurrency import asynccontextmanager
from fastapi.encoders import jsonable_encoder
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse


from src.core.config import settings
from src.core.exceptions import ErrorResponse
from src.core.middlewares import ErrorHandlingMiddleware
from src.routers import auth, user

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    if not settings.app_secret:
        raise RuntimeError("Application secret is missing.")

    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
    )
    yield


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
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
def handle_http_exception(request: Request, exc: HTTPException):
    log.info("%s: %s", exc, request.url)

    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(ErrorResponse(request, exc)),
        headers=exc.headers,
    )


app.include_router(auth.router, tags=["Authentication"])
app.include_router(user.router, tags=["Users"])
