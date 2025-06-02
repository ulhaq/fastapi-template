from typing import Annotated

from fastapi import APIRouter, Depends

from src.core.dependencies import get_current_user
from src.core.security import oauth2_scheme
from src.models.user import User
from src.schemas.user import UserIn, UserOut
from src.services.user import UserService

router = APIRouter()


@router.get("/users/me/", response_model=UserOut)
def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user


@router.post("/users", response_model=UserOut)
def create(
    user_in: UserIn,
    service: Annotated[UserService, Depends(UserService)],
    _: Annotated[str, Depends(oauth2_scheme)],
) -> UserOut:
    return service.create(user_in)
