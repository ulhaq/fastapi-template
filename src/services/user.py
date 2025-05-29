from src.core.exceptions import AlreadyExistsException
from src.core.security import hash_password
from src.models.user import User
from src.repositories.user import UserRepository
from src.schemas.user import UserIn
from src.services.base import BaseService

user_repository: UserRepository = UserRepository()


class UserService(BaseService):
    def create(self, user_in: UserIn):
        if user_repository.get_by_email(user_in.email):
            raise AlreadyExistsException(detail="Email is already registered.")

        user_in.password = hash_password(user_in.password)
        return user_repository.create(**user_in.model_dump())
