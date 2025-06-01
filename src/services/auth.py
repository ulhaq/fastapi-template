from fastapi.security import OAuth2PasswordRequestForm

from src.core.exceptions import AlreadyExistsException, NotAuthenticatedException
from src.core.security import (
    Token,
    authenticate_user,
    create_access_token,
    hash_password,
)
from src.models.user import User
from src.repositories.user import UserRepository
from src.schemas.user import UserIn
from src.services.base import BaseService

user_repository: UserRepository = UserRepository()


class AuthService(BaseService):
    def register_user(self, user_in: UserIn) -> User:
        if user_repository.get_by_email(user_in.email):
            raise AlreadyExistsException(detail="Email is already registered.")

        user_in.password = hash_password(user_in.password)
        return user_repository.create(**user_in.model_dump())

    def obtain_access_token(self, auth_data: OAuth2PasswordRequestForm) -> Token:
        user = authenticate_user(auth_data)
        if not user:
            raise NotAuthenticatedException(
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token = create_access_token(user)
        return Token(access_token=access_token, token_type="bearer")
