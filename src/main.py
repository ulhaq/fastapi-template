from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.middleware import Middleware
from fastapi.responses import JSONResponse

from src.core.exceptions import ErrorResponse
from src.core.middlewares import ErrorHandlingMiddleware
from src.routers import auth, user

app = FastAPI(middleware=[Middleware(ErrorHandlingMiddleware)])


@app.exception_handler(HTTPException)
def handle_http_exception(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(ErrorResponse(request, exc)),
        headers=exc.headers,
    )


app.include_router(auth.router, tags=["Authentication"])
app.include_router(user.router, tags=["Users"])
