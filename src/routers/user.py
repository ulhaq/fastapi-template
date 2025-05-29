from typing import Annotated
from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.models.user import User
from src.schemas.user import UserBase, UserIn
from src.services.user import UserService

router = APIRouter()


@router.get("/users", response_model=list[UserBase])
async def get_all(
    service: Annotated[UserService, Depends(UserService)],
) -> list[UserBase]:
    return service.get_all()


# @router.get("/users/{id}", response_model=UserBase)
# async def get(id: Annotated[int, Path()], db: Session = Depends(get_db)):
#     return User.get_or_fail(db, id)


@router.post("/users")
async def create(
    db: Annotated[Session, Depends(get_db)],
    create_input: Annotated[UserIn, Body()],
) -> UserBase:
    user = User(
        name=create_input.name,
        email=create_input.email,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return UserBase.model_validate(user)
