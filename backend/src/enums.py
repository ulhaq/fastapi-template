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


class ErrorCode(Enum):
    SERVER_ERROR = ("server_error", "Something went wrong on our end.")
    VALIDATION_ERROR = (
        "validation_error",
        "The request failed due to validation errors",
    )
    UNAUTHORIZED = ("unauthorized", "You are not authenticated")
    LOGIN_FAILED = ("login_failed", "Invalid email or password")
    PERMISSION_DENIED = (
        "permission_denied",
        "You are not authorized to perform this action",
    )
    JSON_INVALID = ("json_invalid", "Problems parsing JSON")
    TOKEN_EXPIRED = ("token_expired", "The authentication token has expired")
    TOKEN_INVALID = ("token_invalid", "The authentication token is invalid")
    SIGNATURE_EXPIRED = ("signature_expired", "The signature has expired")
    SIGNATURE_INVALID = ("signature_invalid", "The signature is invalid")
    PARAMETER_INVALID = (
        "parameter_invalid",
        "One or more request parameters are invalid or not allowed",
    )
    RESOURCE_NOT_FOUND = (
        "resource_not_found",
        "The requested resource could not be found",
    )
    RESOURCE_ALREADY_EXISTS = (
        "resource_already_exists",
        "The requested resource already exists",
    )
    EMAIL_ALREADY_EXISTS = ("email_already_exists", "The provided email already exists")

    def __init__(self, code: str, description: str):
        self.code = code
        self.description = description
