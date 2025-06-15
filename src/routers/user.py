from typing import Annotated

from fastapi import APIRouter, Depends, Path

from src.core.dependencies import authenticate
from src.core.security import get_current_user
from src.schemas.user import UserIn, UserOut, UserRoleIn
from src.services.user import UserService

router = APIRouter()


@router.get(
    "/users/me/",
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


@router.post(
    "/users/{identifier}/roles",
    dependencies=[Depends(authenticate)],
    status_code=200,
    response_model=UserOut,
)
async def add_roles_to_a_user(
    service: Annotated[UserService, Depends()],
    identifier: Annotated[int, Path()],
    role_permission_in: UserRoleIn,
):
    return await service.add_roles(identifier, role_permission_in)


@router.delete(
    "/users/{identifier}/roles",
    dependencies=[Depends(authenticate)],
    status_code=200,
    response_model=UserOut,
)
async def remove_roles_from_a_user(
    service: Annotated[UserService, Depends()],
    identifier: Annotated[int, Path()],
    role_permission_in: UserRoleIn,
):
    return await service.remove_roles(identifier, role_permission_in)
