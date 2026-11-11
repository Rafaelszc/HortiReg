from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Lê as variáveis de ambiente (docker-compose injeta o .env)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Banco (no Docker, o docker-compose sobrescreve com host "postgres")
    database_url: str = "postgresql+asyncpg://sgv:sgv@localhost:5432/sgv"

    # Evolution API
    evolution_url: str = "http://localhost:8080"
    evolution_api_key: str = ""
    evolution_instance: str = "sgv"

    # Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    # Pedido por áudio (US-06): limite de duração, tamanho do arquivo e espera pela IA
    audio_max_segundos: int = 60
    audio_max_bytes: int = 5_000_000
    audio_timeout_segundos: float = 45

    # Admins (lista separada por vírgula)
    admin_numbers: str = ""

    # Painel: sessão do administrador
    jwt_secret: str
    admin_login: str = ""
    admin_password: str = ""
    session_minutes: int = 30
    lockout_attempts: int = 5
    lockout_minutes: int = 15

    @property
    def admin_list(self) -> list[str]:
        return [n.strip() for n in self.admin_numbers.split(",") if n.strip()]


settings = Settings()
