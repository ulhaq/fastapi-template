from datetime import datetime
from enum import Enum
from typing import Any, Callable

from dateutil import parser
from sqlalchemy.orm.attributes import InstrumentedAttribute

from src.enums import ComparisonOperator


class FilterValueType(Enum):
    SINGLE = "single"
    LIST = "list"
    RANGE = "range"


# Mapping of field type to supported filter operators
FILTER_OPERATORS_BY_FIELD_TYPE = {
    str: [
        ComparisonOperator.EQUALS.value,
        ComparisonOperator.NOT_EQUALS.value,
        ComparisonOperator.CONTAINS.value,
        ComparisonOperator.INSENSITIVE_CONTAINS.value,
        ComparisonOperator.NOT_CONTAINS.value,
        ComparisonOperator.INSENSITIVE_NOT_CONTAINS.value,
        ComparisonOperator.IN.value,
        ComparisonOperator.NOT_IN.value,
    ],
    int: [
        ComparisonOperator.EQUALS.value,
        ComparisonOperator.NOT_EQUALS.value,
        ComparisonOperator.LESS_THAN.value,
        ComparisonOperator.LESS_THAN_OR_EQUAL_TO.value,
        ComparisonOperator.GREATER_THAN.value,
        ComparisonOperator.GREATER_THAN_OR_EQUAL_TO.value,
        ComparisonOperator.IN.value,
        ComparisonOperator.NOT_IN.value,
        ComparisonOperator.BETWEEN.value,
    ],
    float: [
        ComparisonOperator.EQUALS.value,
        ComparisonOperator.NOT_EQUALS.value,
        ComparisonOperator.LESS_THAN.value,
        ComparisonOperator.LESS_THAN_OR_EQUAL_TO.value,
        ComparisonOperator.GREATER_THAN.value,
        ComparisonOperator.GREATER_THAN_OR_EQUAL_TO.value,
        ComparisonOperator.IN.value,
        ComparisonOperator.NOT_IN.value,
        ComparisonOperator.BETWEEN.value,
    ],
    datetime: [
        ComparisonOperator.EQUALS.value,
        ComparisonOperator.NOT_EQUALS.value,
        ComparisonOperator.LESS_THAN.value,
        ComparisonOperator.LESS_THAN_OR_EQUAL_TO.value,
        ComparisonOperator.GREATER_THAN.value,
        ComparisonOperator.GREATER_THAN_OR_EQUAL_TO.value,
        ComparisonOperator.IN.value,
        ComparisonOperator.NOT_IN.value,
        ComparisonOperator.BETWEEN.value,
    ],
    bool: [ComparisonOperator.EQUALS.value],
}


# Mapping of filter value types to allowed operators
COMPARISON_OPERATORS_BY_FILTER_VALUE_TYPE = {
    FilterValueType.SINGLE: [
        ComparisonOperator.EQUALS.value,
        ComparisonOperator.NOT_EQUALS.value,
        ComparisonOperator.LESS_THAN.value,
        ComparisonOperator.LESS_THAN_OR_EQUAL_TO.value,
        ComparisonOperator.GREATER_THAN.value,
        ComparisonOperator.GREATER_THAN_OR_EQUAL_TO.value,
        ComparisonOperator.CONTAINS.value,
        ComparisonOperator.INSENSITIVE_CONTAINS.value,
        ComparisonOperator.NOT_CONTAINS.value,
        ComparisonOperator.INSENSITIVE_NOT_CONTAINS.value,
    ],
    FilterValueType.LIST: [
        ComparisonOperator.IN.value,
        ComparisonOperator.NOT_IN.value,
    ],
    FilterValueType.RANGE: [
        ComparisonOperator.BETWEEN.value,
    ],
}

# SQLAlchemy operator lambda mapping
SQLA_OPERATORS: dict[str, Callable[..., Any]] = {
    ComparisonOperator.EQUALS.value: lambda field, val: field == val,
    ComparisonOperator.NOT_EQUALS.value: lambda field, val: field != val,
    ComparisonOperator.LESS_THAN.value: lambda field, val: field < val,
    ComparisonOperator.LESS_THAN_OR_EQUAL_TO.value: lambda field, val: field <= val,
    ComparisonOperator.GREATER_THAN.value: lambda field, val: field > val,
    ComparisonOperator.GREATER_THAN_OR_EQUAL_TO.value: lambda field, val: field >= val,
    ComparisonOperator.CONTAINS.value: lambda field, val: field.like(f"%{val}%"),
    ComparisonOperator.INSENSITIVE_CONTAINS.value: lambda field, val: field.ilike(
        f"%{val}%"
    ),
    ComparisonOperator.NOT_CONTAINS.value: lambda field, val: ~field.like(f"%{val}%"),
    ComparisonOperator.INSENSITIVE_NOT_CONTAINS.value: lambda field, val: ~field.ilike(
        f"%{val}%"
    ),
    ComparisonOperator.IN.value: lambda field, val: field.in_(val),
    ComparisonOperator.NOT_IN.value: lambda field, val: ~field.in_(val),
    ComparisonOperator.BETWEEN.value: lambda field, start, end: field.between(
        start, end
    ),
}


def get_filter_expression(
    operator: str, values: list, field: InstrumentedAttribute
) -> list[Any] | Any:
    if operator in COMPARISON_OPERATORS_BY_FILTER_VALUE_TYPE[FilterValueType.SINGLE]:
        return [SQLA_OPERATORS[operator](field, value) for value in values]

    if operator in COMPARISON_OPERATORS_BY_FILTER_VALUE_TYPE[FilterValueType.LIST]:
        return SQLA_OPERATORS[operator](field, values)

    if operator in COMPARISON_OPERATORS_BY_FILTER_VALUE_TYPE[FilterValueType.RANGE]:
        if len(values) != 2:
            raise ValueError(
                "Between operator expects exactly two values: [start, end]"
            )
        return SQLA_OPERATORS[operator](field, values[0], values[1])

    return None


def cast_values_to_type(values: list, field_type: type, field_name: str) -> list:
    try:
        rs = []
        for value in values:
            if field_type != datetime:
                rs.append(field_type(value))
            else:
                rs.append(parser.parse(value))
        return rs
    except (ValueError, TypeError) as exc:
        raise ValueError(
            f"Values for the '{field_name}' field must be provided "
            f"as a list of '{field_type.__name__}' types"
        ) from exc
