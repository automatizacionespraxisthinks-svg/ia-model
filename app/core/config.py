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
    # Razonamiento interno (qwen3.5, deepseek-r1, etc.).
    # False = respuesta directa, mucho más rápido y compatible con n8n/LangChain.
    # True = el modelo razona antes (mejor calidad en problemas complejos, mucho más lento).
    ollama_enable_thinking: bool = False

    # Modelos
    available_models: str = "qwen3.5,granite4.1"
    default_model: str = "qwen3.5"

    # Router automático
    router_light_threshold: int = 500    # chars
    router_medium_threshold: int = 2000  # chars
    router_light_model: str = "granite4.1"
    router_medium_model: str = "qwen3.5"
    router_heavy_model: str = "qwen3.5"

    # Rate limiting
    rate_limit_per_minute: int = 60

    # Admin
    admin_secret: str = "change-this-admin-secret"
    admin_username: str = "admin"
    admin_password: str = "change-this-admin-password"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def available_models_list(self) -> list[str]:
        return [m.strip() for m in self.available_models.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()
