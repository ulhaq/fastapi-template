from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, RedirectResponse
from src.core.exceptions import ErrorResponse
from src.routers import user, auth

app = FastAPI()


@app.exception_handler(HTTPException)
def handle_http_exception(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(ErrorResponse(request, exc)),
        headers=exc.headers,
    )


@app.get("/")
def root():
    return RedirectResponse(url="/docs")


app.include_router(auth.router)
app.include_router(user.router)
