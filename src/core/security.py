from time import time

from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt import encode
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr

from src.core.config import settings
from src.core.exceptions import NotAuthenticatedException
from src.models.user import User
from src.repositories.user import UserRepository

user_repository: UserRepository = UserRepository()


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: EmailStr


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


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user: User):
    return encode(
        JWTTokenClaims(
            iss=settings.app_name,
            aud=settings.app_name,
            sub=str(user.id),
            exp=int(time() + settings.access_token_expiry),
            iat=int(time()),
            name=user.name,
            email=user.email,
        ).model_dump(),
        settings.app_secret,
        algorithm=settings.auth_algorithm,
    )


def authenticate_user(auth_data: OAuth2PasswordRequestForm) -> User:
    user = user_repository.get_by_email(auth_data.username)
    if not user or not verify_password(auth_data.password, user.password):
        raise NotAuthenticatedException(
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
