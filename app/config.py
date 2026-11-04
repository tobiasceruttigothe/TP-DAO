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

    # Seguridad. El secreto firma los tokens: en un despliegue real se cambia por uno propio
    jwt_secreto: str = "cambiar-este-secreto-en-el-env-para-produccion"
    jwt_minutos: int = 480
    # Costo del hash de contrasenas: 12 es lo recomendado; los tests usan el minimo para ir rapido
    bcrypt_rondas: int = 12
    # Administrador que se crea al arrancar si no existe ninguno
    admin_email: str = "admin@example.com"
    admin_contrasena: str = "admin123"
    admin_nombre: str = "Administrador"
    crear_admin_al_iniciar: bool = True

    # Correo. Modo "smtp" envia de verdad (Mailpit en desarrollo, Gmail en la demo);
    # "memoria" los guarda para los tests; "desactivado" no envia nada.
    correo_modo: str = "smtp"
    smtp_host: str = "localhost"
    smtp_puerto: int = 1025
    smtp_usuario: str = ""
    smtp_contrasena: str = ""
    smtp_tls: bool = False
    correo_remitente: str = "Red de Bibliotecas <no-responder@example.com>"
    # Direccion del frontend, para los links de los correos
    url_frontend: str = "http://localhost:3000"
    # Dias de anticipacion para avisar que un prestamo esta por vencer
    dias_aviso_vencimiento: int = 2

    @property
    def lista_cors_origenes(self) -> list[str]:
        return [origen.strip() for origen in self.cors_origenes.split(",") if origen.strip()]


settings = Settings()
