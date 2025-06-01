from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", env_file_encoding="utf-8")

    app_name: str = ""
    app_secret: str = ""
    debug_mode: bool = False

    auth_algorithm: str = "HS256"
    access_token_expiry: int = 1800

    allowed_origins: str = "*"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def allow_origins(self) -> list[str]:
        return [
            origin.strip().rstrip("/") for origin in self.allowed_origins.split(",")
        ]

    allow_credentials: bool = True

    allowed_methods: str = "*"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def allow_methods(self) -> list[str]:
        return [method.strip() for method in self.allowed_methods.split(",")]

    allowed_headers: str = "*"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def allow_headers(self) -> list[str]:
        return [header.strip() for header in self.allowed_headers.split(",")]


settings = Settings()  # type: ignore
