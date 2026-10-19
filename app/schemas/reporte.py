from datetime import date, datetime

from pydantic import BaseModel


class PrestamoActivoItem(BaseModel):
    prestamo_id: int
    socio: str
    libro: str
    codigo_ejemplar: str
    tipo: str
    sede_retiro: str
    fecha_inicio: date
    fecha_vencimiento: date
    vencido: bool


class EnTransitoItem(BaseModel):
    remito: str
    tipo: str
    libro: str
    codigo_ejemplar: str
    sede_origen: str
    sede_destino: str
    fecha_despacho: datetime
    horas_en_viaje: float


class ReporteActivosYTransito(BaseModel):
    fecha: date
    total_prestamos_activos: int
    total_en_transito: int
    prestamos_activos: list[PrestamoActivoItem]
    en_transito: list[EnTransitoItem]


class PrestamoVencidoItem(BaseModel):
    prestamo_id: int
    libro: str
    fecha_vencimiento: date
    dias_atraso: int
    multa_estimada: float


class SocioMultasItem(BaseModel):
    socio_id: int
    socio: str
    dni: str
    prestamos_vencidos: list[PrestamoVencidoItem]
    multas_cobradas: float
    multas_pendientes: float
    total_acumulado: float


class ReporteVencidosYMultas(BaseModel):
    fecha: date
    total_prestamos_vencidos: int
    total_multas_pendientes: float
    total_multas_cobradas: float
    socios: list[SocioMultasItem]


class LibroSolicitadoItem(BaseModel):
    libro_id: int
    titulo: str
    autor: str
    cantidad_prestamos: int


class DisponibilidadSedeItem(BaseModel):
    sede_id: int
    sede: str
    activa: bool
    titulos_distintos: int
    total_ejemplares: int
    disponibles: int
    porcentaje_disponible: float
    por_estado: dict[str, int]


class ReporteEnvios(BaseModel):
    total_finalizados: int
    recibidos_ok: int
    recibidos_con_danio: int
    extraviados: int
    cancelados: int
    en_curso: int
    tasa_exito: float
    tasa_incidencias: float


class MovimientoSedesItem(BaseModel):
    sede_origen: str
    sede_destino: str
    envios: int
    recibidos: int
    incidencias: int
    promedio_horas_transito: float | None
