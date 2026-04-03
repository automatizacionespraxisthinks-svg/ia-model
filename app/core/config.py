from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    app_name: str = "praxis-ia-model"
    app_env: str = "production"
    debug: bool = False
    secret_key: str = "change-this-secret"

    # Database
    database_url: str = "sqlite:///./data/praxis.db"

    # Ollama
    ollama_base_url: str = "http://ollama:11434"
    ollama_timeout: int = 120
    ollama_max_retries: int = 3

    # Modelos
    available_models: str = "mistral,llama3,phi3"
    default_model: str = "mistral"

    # Router automático
    router_light_threshold: int = 500    # chars
    router_medium_threshold: int = 2000  # chars
    router_light_model: str = "phi3"
    router_medium_model: str = "mistral"
    router_heavy_model: str = "llama3"

    # Rate limiting
    rate_limit_per_minute: int = 60

    # Admin
    admin_secret: str = "change-this-admin-secret"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def available_models_list(self) -> list[str]:
        return [m.strip() for m in self.available_models.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()
