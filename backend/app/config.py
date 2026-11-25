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
    # Pedido por texto (RK-03): espera máxima pela IA antes de avisar o cliente
    ia_texto_timeout_segundos: float = 30

    # Versão em execução (o deploy define APP_VERSAO com a tag da imagem)
    app_versao: str = "dev"

    # Fila de retentativa (RK-03 / DA-CONF-I3-01): a espera dobra a cada falha até o teto; vencido o prazo, desiste
    fila_espera_inicial_segundos: float = 15
    fila_espera_maxima_segundos: float = 300
    fila_prazo_minutos: int = 60  # cobre 30 min de IA fora do ar mais o reprocessamento
    fila_intervalo_segundos: float = 10
    # Reserva da mensagem enquanto alguém a processa (evita dois processamentos simultâneos)
    fila_reserva_segundos: float = 120

    # Token do webhook (SCRUM: segurança). Vazio = webhook aberto; defina em qualquer ambiente exposto.
    webhook_token: str = ""

    # Admins (lista separada por vírgula)
    admin_numbers: str = ""

    # Painel: sessão do administrador
    jwt_secret: str
    admin_login: str = ""
    admin_password: str = ""
    session_minutes: int = 30
    lockout_attempts: int = 5
    lockout_minutes: int = 15

    # Pedido não confirmado expira depois deste prazo (US-10)
    pedido_expira_minutos: int = 30

    @property
    def admin_list(self) -> list[str]:
        return [n.strip() for n in self.admin_numbers.split(",") if n.strip()]


settings = Settings()
