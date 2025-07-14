from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Path

from src.core.dependencies import authenticate
from src.schemas.user import UserIn, UserOut, UserRoleIn
from src.services.user import UserService

router = APIRouter()


@router.get("/users/me", dependencies=[Depends(authenticate)], status_code=200)
async def get_authenticated_user(service: Annotated[UserService, Depends()]) -> UserOut:
    return await service.get_authenticated_user()


@router.post("/users", dependencies=[Depends(authenticate)], status_code=201)
async def create_a_user(
    bg_tasks: BackgroundTasks,
    service: Annotated[UserService, Depends()],
    user_in: UserIn,
) -> UserOut:
    return await service.create_user(user_in, bg_tasks)


@router.delete(
    "/users/{identifier}", dependencies=[Depends(authenticate)], status_code=204
)
async def delete_a_user(
    service: Annotated[UserService, Depends()], identifier: Annotated[int, Path()]
) -> None:
    await service.delete_user(identifier)


@router.post(
    "/users/{identifier}/roles", dependencies=[Depends(authenticate)], status_code=200
)
async def manage_roles_of_a_user(
    service: Annotated[UserService, Depends()],
    identifier: Annotated[int, Path()],
    role_in: UserRoleIn,
) -> UserOut:
    return await service.manage_roles(identifier, role_in)
