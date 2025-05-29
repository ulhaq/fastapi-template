from sqlalchemy.orm import Session

from src.core.database import get_db


class BaseRepository:
    db: Session

    def __init__(self):
        self.db = next(get_db())
