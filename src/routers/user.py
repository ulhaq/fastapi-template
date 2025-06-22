from typing import Annotated

from fastapi import APIRouter, Depends, Path

from src.core.dependencies import authenticate
from src.core.security import get_current_user
from src.schemas.user import UserIn, UserOut, UserRoleIn
from src.services.user import UserService

router = APIRouter()


@router.get(
    "/users/me",
    dependencies=[Depends(authenticate)],
    status_code=200,
    response_model=UserOut,
)
async def get_authenticated_user(service: Annotated[UserService, Depends()]):
    return await service.get(get_current_user().id)


@router.post(
    "/users",
    dependencies=[Depends(authenticate)],
    status_code=201,
    response_model=UserOut,
)
async def create_a_user(
    service: Annotated[UserService, Depends()], user_in: UserIn
) -> UserOut:
    return await service.create_user(user_in)


@router.delete(
    "/users/{identifier}", dependencies=[Depends(authenticate)], status_code=204
)
async def delete_a_user(
    service: Annotated[UserService, Depends()], identifier: Annotated[int, Path()]
) -> None:
    await service.delete_user(identifier)


@router.post(
    "/users/{identifier}/roles",
    dependencies=[Depends(authenticate)],
    status_code=200,
    response_model=UserOut,
)
async def manage_roles_of_a_user(
    service: Annotated[UserService, Depends()],
    identifier: Annotated[int, Path()],
    role_in: UserRoleIn,
):
    return await service.manage_roles(identifier, role_in)
