from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg2://biblioteca:biblioteca@localhost:5432/biblioteca"

    # Reglas de negocio configurables
    dias_prestamo: int = 14
    max_prestamos_activos: int = 3
    dias_validez_reserva: int = 3
    multa_estrategia: str = "fija"  # "fija" | "escalonada"
    multa_monto_diario: float = 500.0


settings = Settings()
