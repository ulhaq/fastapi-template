from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from src.core.config import settings
from src.core.dependencies import authenticate
from src.core.limiter import limiter
from src.core.security import Auth, Token
from src.schemas.user import EmailIn, ResetPasswordIn, UserIn, UserOut
from src.services.auth import AuthService, SwitchTenantIn

router = APIRouter(prefix="/auth")


def _set_refresh_token_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        expires=settings.auth_refresh_token_expiry,
        secure=settings.app_env != "local",
        samesite="lax",
        path="/v1/auth",
    )


def _delete_refresh_token_cookie(response: Response) -> None:
    response.delete_cookie(
        key="refresh_token",
        secure=settings.app_env != "local",
        samesite="lax",
        path="/v1/auth",
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def create_an_account(
    request: Request,  # pylint: disable=unused-argument
    bg_tasks: BackgroundTasks,
    service: Annotated[AuthService, Depends()],
    user_in: UserIn,
) -> UserOut:
    return await service.register_tenant(user_in, bg_tasks.add_task)


@router.post("/token", status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")
async def get_access_token(
    request: Request,  # pylint: disable=unused-argument
    response: Response,
    auth_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: Annotated[AuthService, Depends()],
) -> Token:
    token = await service.get_access_token(auth_data.username, auth_data.password)
    _set_refresh_token_cookie(response, token.refresh_token)
    return token


@router.post("/refresh", status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")
async def refresh_access_token(
    request: Request,
    response: Response,
    service: Annotated[AuthService, Depends()],
) -> Token:
    token = await service.refresh_access_token(request.cookies.get("refresh_token"))
    _set_refresh_token_cookie(response, token.refresh_token)
    return token


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    service: Annotated[AuthService, Depends()],
) -> None:
    await service.logout(request.cookies.get("refresh_token"))
    _delete_refresh_token_cookie(response)


@router.post("/reset-password/request", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("5/minute")
async def request_password_reset(
    request: Request,  # pylint: disable=unused-argument
    bg_tasks: BackgroundTasks,
    service: Annotated[AuthService, Depends()],
    email_in: EmailIn,
) -> None:
    return await service.request_password_reset(email_in, bg_tasks.add_task)


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("5/minute")
async def reset_password(
    request: Request,  # pylint: disable=unused-argument
    service: Annotated[AuthService, Depends()],
    reset_password_in: ResetPasswordIn,
) -> None:
    await service.reset_password(reset_password_in)


@router.post("/switch-tenant", status_code=status.HTTP_200_OK)
async def switch_tenant(
    response: Response,
    service: Annotated[AuthService, Depends()],
    current_user: Annotated[Auth, Depends(authenticate)],
    switch_in: SwitchTenantIn,
) -> Token:
    token = await service.switch_tenant(current_user, switch_in.tenant_id)
    _set_refresh_token_cookie(response, token.refresh_token)
    return token
