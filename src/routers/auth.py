from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from src.core.security import Token
from src.schemas.user import UserIn, UserOut
from src.services.auth import AuthService

router = APIRouter()


@router.post("/auth/register", response_model=UserOut)
def register_user(
    user_in: UserIn, service: Annotated[AuthService, Depends(AuthService)]
):
    return service.register_user(user_in)


@router.post("/auth/token")
def obtain_access_token(
    auth_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: Annotated[AuthService, Depends(AuthService)],
) -> Token:
    return service.obtain_access_token(auth_data)
