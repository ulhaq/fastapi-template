from enum import Enum


class ComparisonOperator(Enum):
    EQUALS = "eq"
    NOT_EQUALS = "neq"
    LESS_THAN = "lt"
    LESS_THAN_OR_EQUAL_TO = "lte"
    GREATER_THAN = "gt"
    GREATER_THAN_OR_EQUAL_TO = "gte"
    CONTAINS = "co"
    INSENSITIVE_CONTAINS = "ico"
    NOT_CONTAINS = "nco"
    INSENSITIVE_NOT_CONTAINS = "inco"
    IN = "in"
    NOT_IN = "nin"
    BETWEEN = "between"
