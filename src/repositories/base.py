from datetime import UTC, datetime
from typing import Any, Generic, Sequence, TypeVar

from sqlalchemy import BinaryExpression, exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql.elements import UnaryExpression

from src.core.database import Base
from src.repositories import utils


class BaseRepository: ...  # pylint: disable=too-few-public-methods


ModelType = TypeVar("ModelType", bound=Base)  # pylint: disable=invalid-name


class ResourceRepository(BaseRepository, Generic[ModelType]):
    model: type[ModelType]
    db: AsyncSession

    def __init__(self, model: type[ModelType], db: AsyncSession) -> None:
        self.model = model
        self.db = db

    async def get_one(self, identifier: int) -> ModelType:
        return await self.db.get_one(self.model, identifier)

    async def get(self, identifier: int) -> ModelType | None:
        return await self.db.get(self.model, identifier)

    async def get_all(self) -> Sequence[ModelType]:
        stmt = select(self.model)
        rs = await self.db.execute(stmt)
        return rs.unique().scalars().all()

    async def get_total(self, *filter_expressions: BinaryExpression) -> int:
        stmt = (
            select(
                func.count()  # pylint: disable=not-callable
            )
            .select_from(self.model)
            .filter(*filter_expressions)
        )
        rs = await self.db.execute(stmt)
        total = rs.scalar_one()
        return int(total)

    async def paginate(
        self,
        sort: list[str],
        filters: dict[str, dict],
        page_size: int,
        page_number: int,
    ) -> tuple[Sequence[ModelType], int]:
        order_expressions = self._get_order_expressions(sort)
        filter_expressions = self._get_filter_expressions(filters)
        stmt = (
            select(self.model)
            .filter(*filter_expressions)
            .order_by(*order_expressions)
            .offset((page_number - 1) * page_size)
            .limit(page_size)
        )
        rs = await self.db.execute(stmt)
        items = rs.unique().scalars().all()

        total = await self.get_total(*filter_expressions)

        return items, total

    async def exists(self, identifier: int) -> bool:
        stmt = select(exists().where(getattr(self.model, "id") == identifier))
        rs = await self.db.execute(stmt)
        return rs.scalar_one()

    async def get_one_by_name(self, name: str) -> ModelType | None:
        stmt = select(self.model).where(getattr(self.model, "name") == name)
        rs = await self.db.execute(stmt)
        return rs.unique().scalar_one_or_none()

    async def filter_by(self, **kwargs: Any) -> Sequence[ModelType]:
        stmt = select(self.model).filter_by(**kwargs)
        rs = await self.db.execute(stmt)
        return rs.unique().scalars().all()

    async def filter_by_ids(self, identifiers: list[int]) -> Sequence[ModelType]:
        stmt = select(self.model).filter(getattr(self.model, "id").in_(identifiers))
        rs = await self.db.execute(stmt)
        return rs.unique().scalars().all()

    async def create(self, **kwargs: Any) -> ModelType:
        instance = self.model(**kwargs)

        self.db.add(instance)
        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    async def update(self, model: ModelType, **kwargs: Any) -> ModelType:
        for attr, value in kwargs.items():
            setattr(model, attr, value)
        setattr(model, "updated_at", datetime.now(UTC))

        self.db.add(model)
        await self.db.commit()
        await self.db.refresh(model)
        return model

    async def delete(self, model: ModelType) -> None:
        await self.db.delete(model)
        await self.db.commit()

    async def add_relationship(
        self,
        target_model: ModelType,
        related_model: Any,
        relationship_attr: str,
        *related_ids: int,
    ) -> None:
        stmt = select(related_model).filter(related_model.id.in_(related_ids))
        rs = await self.db.execute(stmt)
        related_objects = rs.unique().scalars().all()

        if related_objects:
            current_value = getattr(target_model, relationship_attr)

            if isinstance(current_value, list):
                current_value.extend(related_objects)
            else:
                setattr(target_model, relationship_attr, related_objects[0])

            await self.db.commit()
            await self.db.refresh(target_model)

    async def remove_relationship(
        self, target_model: ModelType, relationship_attr: str, *related_ids: int
    ) -> None:
        current_value = getattr(target_model, relationship_attr)

        if isinstance(current_value, list):
            setattr(
                target_model,
                relationship_attr,
                [
                    related_obj
                    for related_obj in current_value
                    if related_obj.id not in related_ids
                ],
            )
        else:
            setattr(target_model, relationship_attr, None)

        await self.db.commit()
        await self.db.refresh(target_model)

    def _get_order_expressions(self, sort: list[str]) -> list[UnaryExpression]:
        ordering: list[UnaryExpression] = []

        for field_name in sort:
            field_name = field_name.lstrip("+")
            descending = field_name.startswith("-")
            field_name = field_name.lstrip("-")

            field = getattr(self.model, field_name, None)
            if not isinstance(field, InstrumentedAttribute):
                raise ValueError(f"Invalid sort value: {field_name}")

            ordering.append(field.asc() if not descending else field.desc())

        return ordering

    def _get_filter_expressions(
        self, filter_dict: dict[str, dict]
    ) -> list[BinaryExpression]:
        filters = []
        for field_name, filter_data in filter_dict.items():
            values = filter_data["v"]
            if not values:
                continue

            operator = filter_data["op"]

            field = getattr(self.model, field_name, None)
            if not field or not hasattr(field, "type"):
                raise ValueError(f"Invalid filtering field: {field_name}")

            field_type = field.type.python_type
            if operator not in utils.FILTER_OPERATORS_BY_FIELD_TYPE.get(field_type, []):
                raise ValueError(
                    f"Operator '{operator}' not supported "
                    f"for '{field_type.__name__}' type"
                )

            values = utils.cast_values_to_type(values, field_type, field_name)

            filter_expression = utils.get_filter_expression(operator, values, field)
            if filter_expression is not None:
                if isinstance(filter_expression, list):
                    filters.extend(filter_expression)
                else:
                    filters.append(filter_expression)

        return filters
