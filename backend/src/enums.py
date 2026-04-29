from enum import Enum, StrEnum

OWNER_ROLE_NAME = "Owner"
ADMIN_ROLE_NAME = "Admin"
MEMBER_ROLE_NAME = "Member"


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
    BILLING_ERROR = ("billing_error", "A billing provider error occurred")
    BILLING_WEBHOOK_INVALID = (
        "billing_webhook_invalid",
        "Webhook signature verification failed",
    )
    SUBSCRIPTION_ALREADY_ACTIVE = (
        "subscription_already_active",
        "Organization already has an active subscription",
    )
    SUBSCRIPTION_NOT_FOUND = (
        "subscription_not_found",
        "No active subscription found for this organization",
    )
    TRIAL_ALREADY_USED = (
        "trial_already_used",
        "A free trial has already been used for this organization",
    )
    PROTECTED_ROLE_MODIFICATION = (
        "protected_role_modification",
        "Protected roles cannot be modified or deleted",
    )
    LAST_OWNER_REMOVAL = (
        "last_owner_removal",
        "Cannot remove the last Owner from an organization",
    )
    PLAN_FEATURE_UNAVAILABLE = (
        "plan_feature_unavailable",
        "Your current plan does not include this feature",
    )

    def __init__(self, code: str, description: str):
        self.code = code
        self.description = description


class Permission(StrEnum):
    UPDATE_ORGANIZATION = "update:organization"
    DELETE_ORGANIZATION = "delete:organization"
    MANAGE_ORGANIZATION_USER = "manage:organization_user"
    READ_USER = "read:user"
    READ_ROLE = "read:role"
    CREATE_ROLE = "create:role"
    UPDATE_ROLE = "update:role"
    DELETE_ROLE = "delete:role"
    MANAGE_USER_ROLE = "manage:user_role"
    READ_PERMISSION = "read:permission"
    MANAGE_ROLE_PERMISSION = "manage:role_permission"
    MANAGE_SUBSCRIPTION = "manage:subscription"
    MANAGE_API_TOKEN = "manage:api_token"


DEFAULT_ROLES: list[tuple[str, str, list["Permission"]]] = [
    (
        ADMIN_ROLE_NAME,
        "Access to manage users, roles, organization settings, and billing.",
        [
            Permission.UPDATE_ORGANIZATION,
            Permission.MANAGE_ORGANIZATION_USER,
            Permission.READ_USER,
            Permission.READ_ROLE,
            Permission.CREATE_ROLE,
            Permission.UPDATE_ROLE,
            Permission.DELETE_ROLE,
            Permission.MANAGE_USER_ROLE,
            Permission.READ_PERMISSION,
            Permission.MANAGE_ROLE_PERMISSION,
            Permission.MANAGE_SUBSCRIPTION,
            Permission.MANAGE_API_TOKEN,
        ],
    ),
    (
        MEMBER_ROLE_NAME,
        "Read-only access to users, roles, and organization settings.",
        [
            Permission.READ_USER,
            Permission.READ_ROLE,
            Permission.READ_PERMISSION,
            Permission.MANAGE_API_TOKEN,
        ],
    ),
]


PERMISSION_DESCRIPTIONS: dict[Permission, str] = {
    Permission.UPDATE_ORGANIZATION: "Allows the user to update organization accounts.",
    Permission.DELETE_ORGANIZATION: "Allows the user to delete organization accounts.",
    Permission.MANAGE_ORGANIZATION_USER: (
        "Allows the user to manage organizations' users."
    ),
    Permission.READ_USER: "Allows the user to read users.",
    Permission.READ_ROLE: "Allows the user to read roles.",
    Permission.CREATE_ROLE: "Allows the user to create new roles.",
    Permission.UPDATE_ROLE: "Allows the user to update roles.",
    Permission.DELETE_ROLE: "Allows the user to delete roles.",
    Permission.MANAGE_USER_ROLE: "Allows the user to manage users' roles.",
    Permission.READ_PERMISSION: "Allows the user to read permissions.",
    Permission.MANAGE_ROLE_PERMISSION: "Allows the user to manage roles' permissions.",
    Permission.MANAGE_SUBSCRIPTION: "Allows managing the organization's subscription.",
    Permission.MANAGE_API_TOKEN: (
        "Allows the user to create and manage their own API tokens."
    ),
}


class PlanFeature(StrEnum):
    API_ACCESS = "api_access"
