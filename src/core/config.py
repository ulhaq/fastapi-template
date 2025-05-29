from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", env_file_encoding="utf-8")

    app_name: str
    app_secret: str
    debug_mode: bool

    auth_algorithm: str = "HS256"
    access_token_expiry: int = 1800


settings = Settings()  # type: ignore
