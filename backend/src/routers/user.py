from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Path, status

from src.core.dependencies import require_permission
from src.core.security import Auth
from src.enums import Permission
from src.schemas.user import (
    ChangePasswordIn,
    UserBase,
    UserIn,
    UserOut,
    UserPatch,
    UserRoleIn,
    UserTransferIn,
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


@router.get("/{identifier}", status_code=status.HTTP_200_OK)
async def get_a_user(
    service: Annotated[UserService, Depends()],
    _: Annotated[Auth, Depends(require_permission(Permission.READ_USER))],
    identifier: Annotated[int, Path()],
) -> UserOut:
    return await service.get_user(identifier)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_a_user(
    bg_tasks: BackgroundTasks,
    service: Annotated[UserService, Depends()],
    _: Annotated[Auth, Depends(require_permission(Permission.CREATE_USER))],
    user_in: UserIn,
) -> UserOut:
    return await service.create_user(user_in, bg_tasks.add_task)


@router.delete("/{identifier}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_a_user(
    service: Annotated[UserService, Depends()],
    _: Annotated[Auth, Depends(require_permission(Permission.DELETE_USER))],
    identifier: Annotated[int, Path()],
) -> None:
    await service.delete_user(identifier)


@router.post("/{identifier}/roles", status_code=status.HTTP_200_OK)
async def manage_roles_of_a_user(
    service: Annotated[UserService, Depends()],
    _: Annotated[Auth, Depends(require_permission(Permission.MANAGE_USER_ROLE))],
    identifier: Annotated[int, Path()],
    role_in: UserRoleIn,
) -> UserOut:
    return await service.manage_roles(identifier, role_in)


@router.post("/{identifier}/transfer", status_code=status.HTTP_200_OK)
async def transfer_a_user(
    service: Annotated[UserService, Depends()],
    _: Annotated[Auth, Depends(require_permission(Permission.TRANSFER_USER))],
    identifier: Annotated[int, Path()],
    transfer_in: UserTransferIn,
) -> UserOut:
    return await service.transfer_user(identifier, transfer_in)
