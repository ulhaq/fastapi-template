from typing import Generic, Sequence, Type, TypeVar

from sqlalchemy import exists, select

from src.core.database import Base
from src.repositories.base import BaseRepository

ModelType = TypeVar("ModelType", bound=Base)  # pylint: disable=invalid-name


class ResourceRepository(Generic[ModelType], BaseRepository):
    def __init__(self, model: Type[ModelType]):
        super().__init__()
        self.model = model

    def get(self, identifier: int) -> ModelType | None:
        return self.db.get(self.model, identifier)

    def get_or_fail(self, identifier: int) -> ModelType:
        return self.db.get_one(self.model, identifier)

    def exists(self, identifier: int) -> bool:
        return self.db.execute(
            select(
                exists(1).where(
                    self.model.id == identifier  # type: ignore[attr-defined]
                )
            )
        ).scalar_one()

    def get_all(self) -> Sequence[ModelType]:
        return self.db.scalars(select(self.model)).all()

    def filter_by(self, **kwargs) -> Sequence[ModelType]:
        return self.db.scalars(select(self.model).filter_by(**kwargs)).all()

    def create(self, **kwargs) -> ModelType:
        instance = self.model(**kwargs)
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def update(self, model: ModelType, **kwargs) -> ModelType:
        for attr, value in kwargs.items():
            setattr(model, attr, value)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model

    def delete(self, model: ModelType) -> None:
        self.db.delete(model)
        self.db.commit()
