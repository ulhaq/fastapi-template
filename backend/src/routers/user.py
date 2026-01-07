from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Path, status

from src.core.dependencies import authenticate
from src.schemas.user import ChangePasswordIn, UserBase, UserIn, UserOut, UserRoleIn
from src.services.user import UserService

router = APIRouter()


@router.get(
    "/users/me", dependencies=[Depends(authenticate)], status_code=status.HTTP_200_OK
)
async def get_authenticated_user(service: Annotated[UserService, Depends()]) -> UserOut:
    return await service.get_authenticated_user()


@router.put(
    "/users/me", dependencies=[Depends(authenticate)], status_code=status.HTTP_200_OK
)
async def update_profile_of_authenticated_user(
    service: Annotated[UserService, Depends()], user_base: UserBase
) -> UserOut:
    return await service.update_profile(user_base)


@router.put(
    "/users/me/change-password",
    dependencies=[Depends(authenticate)],
    status_code=status.HTTP_200_OK,
)
async def change_password_of_authenticated_user(
    service: Annotated[UserService, Depends()], change_password_in: ChangePasswordIn
) -> UserOut:
    return await service.change_password(change_password_in)


@router.post(
    "/users", dependencies=[Depends(authenticate)], status_code=status.HTTP_201_CREATED
)
async def create_a_user(
    bg_tasks: BackgroundTasks,
    service: Annotated[UserService, Depends()],
    user_in: UserIn,
) -> UserOut:
    return await service.create_user(user_in, bg_tasks)


@router.delete(
    "/users/{identifier}",
    dependencies=[Depends(authenticate)],
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_a_user(
    service: Annotated[UserService, Depends()], identifier: Annotated[int, Path()]
) -> None:
    await service.delete_user(identifier)


@router.post(
    "/users/{identifier}/roles",
    dependencies=[Depends(authenticate)],
    status_code=status.HTTP_200_OK,
)
async def manage_roles_of_a_user(
    service: Annotated[UserService, Depends()],
    identifier: Annotated[int, Path()],
    role_in: UserRoleIn,
) -> UserOut:
    return await service.manage_roles(identifier, role_in)
