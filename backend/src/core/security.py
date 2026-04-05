from time import time
from typing import Any, Literal, Self
from uuid import uuid4

from fastapi.security import OAuth2PasswordBearer
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from jwt import ExpiredSignatureError, InvalidTokenError, decode, encode
from passlib.context import CryptContext
from pydantic import BaseModel

from src.core.config import settings
from src.core.exceptions import NotAuthenticatedException, PermissionDeniedException
from src.enums import ErrorCode
from src.models.user import User

crypt_context = CryptContext(schemes=["argon2"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="v1/auth/token", auto_error=False)
BEARER_HEADERS: dict[str, str] = {"WWW-Authenticate": "Bearer"}


class Auth(BaseModel):
    id: int
    name: str
    email: str
    tenant_id: int
    roles: list[str]
    permissions: list[str]

    @classmethod
    def from_user_model(cls, user_model: User, active_tenant_id: int) -> Self:
        tenant_roles = [r for r in user_model.roles if r.tenant_id == active_tenant_id]
        return cls(
            id=user_model.id,
            name=user_model.name,
            email=user_model.email,
            tenant_id=active_tenant_id,
            permissions=list(
                dict.fromkeys(
                    permission.name
                    for role in tenant_roles
                    for permission in role.permissions
                )
            ),
            roles=[role.name for role in tenant_roles],
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
    jti: str
    roles: list[str]

    name: str | None = None
    email: str | None = None
    tid: int | None = None


type SignSalt = Literal["reset-password", "email-verification", "complete-registration", "invite"]


def sign(data: Any, salt: SignSalt) -> str:
    s = URLSafeTimedSerializer(
        secret_key=settings.app_secret.get_secret_value(), salt=salt
    )
    return s.dumps(data)


def unsign(token: str, salt: SignSalt, max_age: int = 10 * 60) -> Any:
    try:
        s = URLSafeTimedSerializer(
            secret_key=settings.app_secret.get_secret_value(), salt=salt
        )
        return s.loads(token, max_age=max_age)
    except SignatureExpired as exc:
        raise NotAuthenticatedException(
            "Signature expired", error_code=ErrorCode.SIGNATURE_EXPIRED
        ) from exc
    except BadSignature as exc:
        raise NotAuthenticatedException(
            "Signature invalid", error_code=ErrorCode.SIGNATURE_INVALID
        ) from exc


def hash_secret(secret: str) -> str:
    return crypt_context.hash(secret)


def verify_secret(plain_secret: str, hashed_secret: str) -> bool:
    try:
        return crypt_context.verify(plain_secret, hashed_secret)
    except Exception:  # pylint: disable=broad-except
        return False


def decode_token(token: str) -> dict:
    try:
        return decode(
            token,
            settings.app_secret.get_secret_value(),
            algorithms=[settings.auth_algorithm],
            audience=settings.app_name,
        )
    except ExpiredSignatureError as exc:
        raise NotAuthenticatedException(
            "Token expired", error_code=ErrorCode.TOKEN_EXPIRED, headers=BEARER_HEADERS
        ) from exc
    except InvalidTokenError as exc:
        raise NotAuthenticatedException(headers=BEARER_HEADERS) from exc


def create_token(
    user: User,
    expiry: int,
    *,
    include_user_claims: bool = True,
    tenant_id: int | None = None,
) -> str:
    claims = JWTTokenClaims(
        iss=settings.app_name,
        aud=settings.app_name,
        sub=str(user.id),
        exp=int(time() + expiry),
        iat=int(time()),
        jti=str(uuid4()),
        roles=[role.name for role in user.roles],
    )
    if include_user_claims:
        claims.name = user.name
        claims.email = user.email
        claims.tid = tenant_id
    return encode(
        claims.model_dump(exclude_none=True),
        settings.app_secret.get_secret_value(),
        algorithm=settings.auth_algorithm,
    )


def authenticate_user(password: str, user: User | None) -> User | None:
    if user and verify_secret(password, user.password):
        return user
    return None
