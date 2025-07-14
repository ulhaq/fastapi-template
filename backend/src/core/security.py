from contextvars import ContextVar
from time import time
from typing import Any, Literal, Self

from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from jwt import encode
from passlib.context import CryptContext
from pydantic import BaseModel

from src.core.config import settings
from src.core.exceptions import NotAuthenticatedException, PermissionDeniedException
from src.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")
current_user: ContextVar["Auth"] = ContextVar("current_user")


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

    def authorize(self, permission: str) -> None:
        if self.has_permission(permission):
            return
        raise PermissionDeniedException


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class JWTTokenClaims(BaseModel):
    iss: str
    sub: str
    aud: str
    exp: int
    iat: int

    name: str | None = None
    email: str | None = None


type SignSalt = Literal["welcome", "new-user", "reset-password"]


def sign(data: Any, salt: SignSalt) -> str:
    s = URLSafeTimedSerializer(secret_key=settings.app_secret, salt=salt)
    return s.dumps(data)


def unsign(token: str, salt: SignSalt, max_age: int = 10 * 60) -> Any:
    try:
        s = URLSafeTimedSerializer(secret_key=settings.app_secret, salt=salt)
        return s.loads(token, max_age=max_age)
    except SignatureExpired as exc:
        raise NotAuthenticatedException("Signature expired") from exc
    except BadSignature as exc:
        raise NotAuthenticatedException("Signature invalid") from exc


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
            exp=int(time() + settings.auth_access_token_expiry),
            iat=int(time()),
            name=user.name,
            email=user.email,
        ).model_dump(),
        settings.app_secret,
        algorithm=settings.auth_algorithm,
    )


def create_refresh_token(user: User) -> str:
    return encode(
        JWTTokenClaims(
            iss=settings.app_name,
            aud=settings.app_name,
            sub=str(user.id),
            exp=int(time() + settings.auth_refresh_token_expiry),
            iat=int(time()),
        ).model_dump(exclude_unset=True),
        settings.app_secret,
        algorithm=settings.auth_algorithm,
    )


def authenticate_user(
    auth_data: OAuth2PasswordRequestForm, user: User | None
) -> User | None:
    if user and verify_password(auth_data.password, user.password):
        return user
    return None


def get_current_user() -> Auth:
    if user := current_user.get():
        return user

    raise NotAuthenticatedException(headers={"WWW-Authenticate": "Bearer"})
