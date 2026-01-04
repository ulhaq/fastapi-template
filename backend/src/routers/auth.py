from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Path, Request, Response
from fastapi.security import OAuth2PasswordRequestForm

from src.core.security import Token
from src.schemas.company import CompanyIn, CompanyOut
from src.schemas.user import EmailIn, NewPasswordIn
from src.services.auth import AuthService

router = APIRouter()


@router.post("/auth/register", status_code=201)
async def create_an_account(
    bg_tasks: BackgroundTasks,
    service: Annotated[AuthService, Depends()],
    company_in: CompanyIn,
) -> CompanyOut:
    return await service.register_company(company_in, bg_tasks)


@router.post("/auth/token", status_code=200)
async def get_access_token(
    response: Response,
    auth_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: Annotated[AuthService, Depends()],
) -> Token:
    return await service.get_access_token(auth_data, response)


@router.post("/auth/refresh", status_code=200)
async def refresh_access_token(
    request: Request,
    response: Response,
    service: Annotated[AuthService, Depends()],
) -> Token | None:
    return await service.refresh_access_token(
        request.cookies.get("refresh_token"), response
    )


@router.post("/auth/logout", status_code=204)
async def logout(
    response: Response, service: Annotated[AuthService, Depends()]
) -> None:
    await service.logout(response)


@router.post("/auth/reset-password", status_code=202)
async def request_password_reset(
    bg_tasks: BackgroundTasks,
    service: Annotated[AuthService, Depends()],
    email_in: EmailIn,
) -> None:
    return await service.request_password_reset(email_in, bg_tasks)


@router.post("/auth/reset-password/{token}", status_code=204)
async def reset_password(
    service: Annotated[AuthService, Depends()],
    token: Annotated[str, Path()],
    new_password_in: NewPasswordIn,
) -> None:
    await service.reset_password(new_password_in, token)
