from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", env_file_encoding="utf-8")

    app_name: str = ""
    app_url: str = "http://localhost"
    app_env: str = "local"
    app_secret: str = ""
    app_debug: bool = False

    db_connection: str = ""

    auth_algorithm: str = "HS256"
    auth_token_expiry: int = 1800
    auth_password_reset_expiry: int = 600

    raw_allow_origins: str = Field(default="*", validation_alias="allow_origins")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def allow_origins(self) -> list[str]:
        return [
            origin.strip().rstrip("/")
            for origin in self.raw_allow_origins.split(",")  # pylint: disable=no-member
        ]

    allow_credentials: bool = True

    raw_allow_methods: str = Field(default="*", validation_alias="allow_methods")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def allow_methods(self) -> list[str]:
        return [method.strip() for method in self.raw_allow_methods.split(",")]  # pylint: disable=no-member

    raw_allow_headers: str = Field(default="*", validation_alias="allow_headers")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def allow_headers(self) -> list[str]:
        return [header.strip() for header in self.raw_allow_headers.split(",")]  # pylint: disable=no-member

    email_host: str
    email_user: str
    email_password: str
    email_tls: bool = True
    email_port: int = 587
    email_from_address: str
    email_from_name: str

    template_path: str = "./src/templates"
    frontend_url: str = "http://localhost:8000"

    log_exc_info: bool = True
    sqlalchemy_echo: bool = False


settings = Settings()  # type: ignore[call-arg]
