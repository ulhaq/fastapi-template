from typing import Annotated
from fastapi import APIRouter, Depends
from src.schemas.user import UserBase, UserIn
from src.services.user import UserService
from src.core.security import oauth2_scheme

router = APIRouter()


@router.post("/users", response_model=UserBase)
def create(
    user_in: UserIn,
    service: Annotated[UserService, Depends(UserService)],
    _: Annotated[str, Depends(oauth2_scheme)],
) -> UserBase:
    return service.create(user_in)
