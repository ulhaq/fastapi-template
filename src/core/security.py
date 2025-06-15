from contextvars import ContextVar
from time import time
from typing import Self

from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt import encode
from passlib.context import CryptContext
from pydantic import BaseModel

from src.core.config import settings
from src.core.exceptions import NotAuthenticatedException
from src.models.user import User


class Auth(BaseModel):
    id: int
    name: str
    email: str
    roles: list[str]
    permissions: list[str]

    @classmethod
    def from_user_model(cls, user_model: User) -> Self:
        return cls(
            id=user_model.id,
            name=user_model.name,
            email=user_model.email,
            permissions=[
                permission.name
                for role in user_model.roles
                for permission in role.permissions
            ],
            roles=[role.name for role in user_model.roles],
        )

    def has_permission(self, permission_name: str) -> bool:
        return permission_name in self.permissions


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class JWTTokenClaims(BaseModel):
    iss: str
    sub: str
    aud: str
    exp: int
    iat: int

    name: str
    email: str


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user: User) -> str:
    return encode(
        JWTTokenClaims(
            iss=settings.app_name,
            aud=settings.app_name,
            sub=str(user.id),
            exp=int(time() + settings.auth_token_expiry),
            iat=int(time()),
            name=user.name,
            email=user.email,
        ).model_dump(),
        settings.app_secret,
        algorithm=settings.auth_algorithm,
    )


def authenticate_user(
    auth_data: OAuth2PasswordRequestForm, user: User | None
) -> User | None:
    if user and verify_password(auth_data.password, user.password):
        return user
    return None


current_user: ContextVar[Auth] = ContextVar("current_user")


def get_current_user() -> Auth:
    if user := current_user.get():
        return user

    raise NotAuthenticatedException(
        detail="Authentication failed.", headers={"WWW-Authenticate": "Bearer"}
    )
