from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from src.core.security import Token
from src.schemas.user import UserIn, UserOut
from src.services.auth import AuthService

router = APIRouter()


@router.post("/auth/register", status_code=201)
async def create_an_account(
    service: Annotated[AuthService, Depends()], user_in: UserIn
) -> UserOut:
    return await service.register_user(user_in)


@router.post("/auth/token", status_code=200)
async def get_access_token(
    auth_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: Annotated[AuthService, Depends()],
) -> Token:
    return await service.get_access_token(auth_data)
