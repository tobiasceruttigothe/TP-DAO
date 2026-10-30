from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg2://biblioteca:biblioteca@localhost:5432/biblioteca"

    # Origenes desde los que el frontend puede llamar a la API, separados por coma
    cors_origenes: str = "http://localhost:3000,http://localhost:5173,http://localhost:4200"

    # Reglas de negocio configurables
    dias_prestamo: int = 14
    max_prestamos_activos: int = 3
    dias_validez_reserva: int = 3
    multa_estrategia: str = "fija"  # "fija" | "escalonada"
    multa_monto_diario: float = 500.0

    @property
    def lista_cors_origenes(self) -> list[str]:
        return [origen.strip() for origen in self.cors_origenes.split(",") if origen.strip()]


settings = Settings()
