from sqlalchemy import select
from src.models.user import User
from src.repositories.resource import ResourceRepository


class UserRepository(ResourceRepository[User]):
    def __init__(self):
        super().__init__(User)

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email))
