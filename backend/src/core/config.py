from typing import Literal, Self

from pydantic import Field, SecretStr, computed_field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_comma_list(value: str) -> list[str]:
    return [v.strip().rstrip("/") for v in value.split(",")]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="./.env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = ""
    app_url: str = "http://localhost"
    app_env: Literal["local", "development", "staging", "production"] = "local"
    app_secret: SecretStr = SecretStr("")
    app_debug: bool = False

    db_connection: str = ""

    auth_enabled: bool = True
    auth_algorithm: str = "HS256"
    auth_access_token_expiry: int = 30 * 60
    auth_refresh_token_expiry: int = 15 * 24 * 60 * 60
    auth_password_reset_expiry: int = 10 * 60
    email_verification_expiry: int = 60 * 60 * 24
    complete_registration_expiry: int = 30 * 60
    invite_expiry: int = 7 * 24 * 60 * 60

    raw_allow_origins: str = Field(default="*", validation_alias="allow_origins")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def allow_origins(self) -> list[str]:
        return _parse_comma_list(self.raw_allow_origins)  # pylint: disable=no-member

    allow_credentials: bool = True

    raw_allow_methods: str = Field(default="*", validation_alias="allow_methods")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def allow_methods(self) -> list[str]:
        return _parse_comma_list(self.raw_allow_methods)  # pylint: disable=no-member

    raw_allow_headers: str = Field(default="*", validation_alias="allow_headers")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def allow_headers(self) -> list[str]:
        return _parse_comma_list(self.raw_allow_headers)  # pylint: disable=no-member

    email_host: str = ""
    email_user: str = ""
    email_password: str = ""
    email_tls: bool = True
    email_port: int = 587
    email_from_address: str = ""
    email_from_name: str = ""

    template_path: str = "./src/templates"
    frontend_url: str = "http://localhost:3000"
    frontend_password_reset_path: str = "reset-password?token="
    frontend_invite_path: str = "invite?token="

    rate_limit_enabled: bool = True

    stripe_secret_key: SecretStr = SecretStr("")
    stripe_webhook_secret: SecretStr = SecretStr("")
    billing_success_url: str = "http://localhost:3000/billing/success"
    billing_cancel_url: str = "http://localhost:3000/billing/cancel"
    billing_portal_return_url: str = "http://localhost:3000/billing"
    billing_automatic_tax: bool = False

    log_exc_info: bool = True
    sqlalchemy_echo: bool = False

    @model_validator(mode="after")
    def validate_allow_origins_and_credentials(self) -> Self:
        if self.allow_credentials is True and "*" in self.allow_origins:
            raise ValueError(
                "ALLOW_ORIGINS must not contain '*' when ALLOW_CREDENTIALS is True"
            )
        return self

    @model_validator(mode="after")
    def validate_production_auth(self) -> Self:
        if self.auth_enabled is False and self.app_env == "production":
            raise ValueError("AUTH_ENABLED must be True in production")
        return self

    @model_validator(mode="after")
    def validate_billing_urls(self) -> Self:
        if self.app_env == "production":
            for field_name in ("billing_success_url", "billing_cancel_url"):
                url = getattr(self, field_name)
                if "localhost" in url or "127.0.0.1" in url:
                    raise ValueError(
                        f"{field_name} must not point to localhost in production"
                    )
        return self


settings = Settings()  # type: ignore[call-arg]
