from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr, field_validator


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://127.0.0.1:5432/hifztrack"
    cors_origins: str = "http://localhost:3000"
    security_secret_key: SecretStr
    session_ttl_hours: int = Field(default=12, ge=1, le=168)
    session_cookie_secure: bool = True

    @field_validator("security_secret_key")
    @classmethod
    def validate_security_secret_key(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value().encode("utf-8")) < 32:
            raise ValueError("SECURITY_SECRET_KEY must contain at least 32 bytes")
        return value

    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
