from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Path, status

from src.core.dependencies import authenticate
from src.core.security import Auth
from src.schemas.user import (
    ChangePasswordIn,
    UserBase,
    UserIn,
    UserOut,
    UserPatch,
    UserRoleIn,
)
from src.services.user import UserService

router = APIRouter(prefix="/users")


@router.get("/me", status_code=status.HTTP_200_OK)
async def get_authenticated_user(service: Annotated[UserService, Depends()]) -> UserOut:
    return await service.get_authenticated_user()


@router.put("/me", status_code=status.HTTP_200_OK)
async def update_profile_of_authenticated_user(
    service: Annotated[UserService, Depends()], user_base: UserBase
) -> UserOut:
    return await service.update_profile(user_base)


@router.patch("/me", status_code=status.HTTP_200_OK)
async def patch_profile_of_authenticated_user(
    service: Annotated[UserService, Depends()], user_patch: UserPatch
) -> UserOut:
    return await service.patch_profile(user_patch)


@router.put("/me/change-password", status_code=status.HTTP_200_OK)
async def change_password_of_authenticated_user(
    service: Annotated[UserService, Depends()], change_password_in: ChangePasswordIn
) -> UserOut:
    return await service.change_password(change_password_in)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_a_user(
    bg_tasks: BackgroundTasks,
    service: Annotated[UserService, Depends()],
    current_user: Annotated[Auth, Depends(authenticate)],
    user_in: UserIn,
) -> UserOut:
    current_user.authorize("create_user")
    return await service.create_user(user_in, bg_tasks.add_task)


@router.delete("/{identifier}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_a_user(
    service: Annotated[UserService, Depends()],
    current_user: Annotated[Auth, Depends(authenticate)],
    identifier: Annotated[int, Path()],
) -> None:
    current_user.authorize("delete_user")
    await service.delete_user(identifier)


@router.post("/{identifier}/roles", status_code=status.HTTP_200_OK)
async def manage_roles_of_a_user(
    service: Annotated[UserService, Depends()],
    current_user: Annotated[Auth, Depends(authenticate)],
    identifier: Annotated[int, Path()],
    role_in: UserRoleIn,
) -> UserOut:
    current_user.authorize("manage_user_role")
    return await service.manage_roles(identifier, role_in)
