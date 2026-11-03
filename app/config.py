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
    # Multas: atraso leve (hasta multa_dias_leves) a monto_diario; atraso grave, los dias
    # siguientes a monto_diario_grave; mas un cargo fijo si se devuelve danado o destruido
    multa_monto_diario: float = 500.0
    multa_monto_diario_grave: float = 1000.0
    multa_dias_leves: int = 7
    multa_cargo_danado: float = 5000.0
    multa_cargo_destruido: float = 20000.0
    # Dias de atraso a partir de los cuales el socio queda inhabilitado automaticamente
    dias_atraso_inhabilitacion: int = 30

    # Proceso de vencimientos (reservas no retiradas e inhabilitacion por atraso)
    proceso_automatico: bool = True
    intervalo_proceso_minutos: int = 60

    @property
    def lista_cors_origenes(self) -> list[str]:
        return [origen.strip() for origen in self.cors_origenes.split(",") if origen.strip()]


settings = Settings()
