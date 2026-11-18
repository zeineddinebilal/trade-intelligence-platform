from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    gemini_api_key: str = ""
    gemini_model: str = "gemini-4-carbon"
    database_url: str = "sqlite:///./trade_intel.db"
    human_review_threshold: int = 70
    auto_seed_demo: bool = True
    environment: str = "development"
    # If set, every route except /healthz requires HTTP Basic auth with this password.
    dashboard_password: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def normalized_database_url(self) -> str:
        # Render PostgreSQL strings occasionally start with postgres://; SQLAlchemy 2.0 requires postgresql://
        if self.database_url.startswith("postgres://"):
            return self.database_url.replace("postgres://", "postgresql://", 1)
        return self.database_url


settings = Settings()
