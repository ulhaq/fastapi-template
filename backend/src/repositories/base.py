from datetime import UTC, datetime
from typing import Any, Sequence

from sqlalchemy import BinaryExpression, Select, exists, func, or_, select
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql.elements import UnaryExpression

from src.core.database import Base
from src.enums import ComparisonOperator
from src.repositories import utils
from src.repositories.abc import ResourceRepositoryABC


class SQLResourceRepository[ModelType: Base](ResourceRepositoryABC[ModelType]):  # pylint: disable=invalid-name
    async def get_one(
        self, identifier: int, include_deleted: bool = False
    ) -> ModelType:
        stmt = select(self.model).filter(getattr(self.model, "id") == identifier)

        stmt = self._include_deleted(stmt, include_deleted)

        rs = await self.db.execute(stmt)
        return rs.unique().scalar_one()

    async def get(
        self, identifier: int, include_deleted: bool = False
    ) -> ModelType | None:
        stmt = select(self.model).filter(getattr(self.model, "id") == identifier)

        stmt = self._include_deleted(stmt, include_deleted)

        rs = await self.db.execute(stmt)
        return rs.unique().scalar_one_or_none()

    async def get_one_by_name(
        self, name: str, include_deleted: bool = False
    ) -> ModelType | None:
        stmt = select(self.model).filter(getattr(self.model, "name") == name)

        stmt = self._include_deleted(stmt, include_deleted)

        rs = await self.db.execute(stmt)
        return rs.unique().scalar_one_or_none()

    async def get_all(self, include_deleted: bool = False) -> Sequence[ModelType]:
        stmt = select(self.model)

        stmt = self._include_deleted(stmt, include_deleted)

        rs = await self.db.execute(stmt)
        return rs.unique().scalars().all()

    async def filter_by(
        self, include_deleted: bool = False, **kwargs: Any
    ) -> Sequence[ModelType]:
        stmt = select(self.model).filter_by(**kwargs)

        stmt = self._include_deleted(stmt, include_deleted)

        rs = await self.db.execute(stmt)
        return rs.unique().scalars().all()

    async def filter_by_ids(
        self, identifiers: list[int], include_deleted: bool = False
    ) -> Sequence[ModelType]:
        stmt = select(self.model).filter(getattr(self.model, "id").in_(identifiers))

        stmt = self._include_deleted(stmt, include_deleted)

        rs = await self.db.execute(stmt)
        return rs.unique().scalars().all()

    async def exists(self, identifier: int, include_deleted: bool = False) -> bool:
        stmt = select(exists().filter(getattr(self.model, "id") == identifier))

        stmt = self._include_deleted(stmt, include_deleted)

        rs = await self.db.execute(stmt)
        return rs.scalar_one()

    async def create(self, *, commit: bool = True, **kwargs: Any) -> ModelType:
        instance = self.model(**kwargs)

        setattr(instance, "created_at", datetime.now(UTC))
        setattr(instance, "updated_at", datetime.now(UTC))

        self.db.add(instance)

        if commit is True:
            await self.db.commit()
        else:
            await self.db.flush()

        await self.db.refresh(instance)

        return instance

    async def update(
        self, model: ModelType, *, commit: bool = True, **kwargs: Any
    ) -> ModelType:
        for attr, value in kwargs.items():
            setattr(model, attr, value)
        setattr(model, "updated_at", datetime.now(UTC))

        self.db.add(model)

        if commit is True:
            await self.db.commit()
        else:
            await self.db.flush()

        await self.db.refresh(model)

        return model

    async def delete(self, model: ModelType, *, commit: bool = True) -> None:
        setattr(model, "deleted_at", datetime.now(UTC))

        if commit is True:
            await self.db.commit()
        else:
            await self.db.flush()

    async def force_delete(self, model: ModelType, *, commit: bool = True) -> None:
        await self.db.delete(model)

        if commit is True:
            await self.db.commit()
        else:
            await self.db.flush()

    async def paginate(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        sort: list[str],
        filters: dict[str, dict],
        page_size: int,
        page_number: int,
        include_deleted: bool = False,
    ) -> tuple[Sequence[ModelType], int]:
        order_expressions = self._get_order_expressions(sort)
        filter_expressions = self._get_filter_expressions(filters)

        stmt = select(self.model)

        if filter_expressions:
            stmt = stmt.filter(or_(*filter_expressions))

        stmt = self._include_deleted(stmt, include_deleted)

        stmt = (
            stmt.order_by(*order_expressions)
            .offset((page_number - 1) * page_size)
            .limit(page_size)
        )

        rs = await self.db.execute(stmt)
        items = rs.unique().scalars().all()

        total = await self.get_total(*filter_expressions, include_deleted=True)

        return items, total

    async def get_total(
        self, *filter_expressions: BinaryExpression, include_deleted: bool = False
    ) -> int:
        stmt = select(
            func.count()  # pylint: disable=not-callable
        ).select_from(self.model)

        if filter_expressions:
            stmt = stmt.filter(or_(*filter_expressions))

        stmt = self._include_deleted(stmt, include_deleted)

        rs = await self.db.execute(stmt)
        total = rs.scalar_one()
        return int(total)

    async def add_relationship(
        self,
        target_model: ModelType,
        related_model: Any,
        relationship_attr: str,
        *related_ids: int,
        commit: bool = True,
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

            if commit is True:
                await self.db.commit()
            else:
                await self.db.flush()

            await self.db.refresh(target_model)

    async def remove_relationship(
        self,
        target_model: ModelType,
        relationship_attr: str,
        *related_ids: int,
        commit: bool = True,
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

        if commit is True:
            await self.db.commit()
        else:
            await self.db.flush()

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

            try:
                operator = ComparisonOperator(filter_data["op"])
            except ValueError as exc:
                raise ValueError(
                    f"Unsupported filter operator: {filter_data['op']}"
                ) from exc

            field = getattr(self.model, field_name, None)
            if not field or not hasattr(field, "type"):
                raise ValueError(f"Invalid filtering field: {field_name}")

            field_type = field.type.python_type
            if operator not in utils.FILTER_OPERATORS_BY_FIELD_TYPE.get(field_type, []):
                raise ValueError(
                    f"Operator '{operator.value}' not supported "
                    f"for '{field_type.__name__}' type"
                )

            values = utils.cast_values_to_type(values, field_type, field_name, operator)

            filter_expression = utils.get_filter_expression(operator, values, field)
            if filter_expression is not None:
                if isinstance(filter_expression, list):
                    filters.extend(filter_expression)
                else:
                    filters.append(filter_expression)

        return filters

    def _include_deleted(self, stmt: Select, include_deleted: bool = False) -> Select:
        if include_deleted is False:
            return stmt.filter(getattr(self.model, "deleted_at").is_(None))
        return stmt
