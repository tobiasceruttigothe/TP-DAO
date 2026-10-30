from collections import defaultdict
from datetime import date, datetime, time

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.enums import EstadoEjemplar, EstadoFisico, EstadoPrestamo, TipoPrestamo
from app.domain.estados_remito import Cancelado, Despachado, Extraviado, Recibido
from app.models import Ejemplar, Libro, Prestamo, Remito, Sede
from app.schemas.reporte import (
    DisponibilidadSedeItem,
    EnTransitoItem,
    LibroSolicitadoItem,
    MovimientoSedesItem,
    PrestamoActivoItem,
    PrestamoVencidoItem,
    ReporteActivosYTransito,
    ReporteEnvios,
    ReporteVencidosYMultas,
    SocioMultasItem,
)
from app.services.prestamo_service import PrestamoService


def _rango(consulta, columna, desde: date | None, hasta: date | None):
    if desde is not None:
        consulta = consulta.where(columna >= datetime.combine(desde, time.min))
    if hasta is not None:
        consulta = consulta.where(columna <= datetime.combine(hasta, time.max))
    return consulta


class ReporteService:
    def __init__(self, db: Session):
        self.db = db

    def activos_y_en_transito(self, hoy: date | None = None) -> ReporteActivosYTransito:
        hoy = hoy or date.today()
        ahora = datetime.now()
        prestamos = self.db.scalars(
            select(Prestamo)
            .where(Prestamo.estado == EstadoPrestamo.ACTIVO)
            .order_by(Prestamo.fecha_vencimiento)
        ).all()
        remitos = self.db.scalars(
            select(Remito).where(Remito.estado == Despachado.nombre).order_by(Remito.fecha_despacho)
        ).all()

        activos = [
            PrestamoActivoItem(
                prestamo_id=p.id,
                socio=p.socio.nombre_completo,
                libro=p.ejemplar.libro.titulo,
                codigo_ejemplar=p.ejemplar.codigo_inventario,
                tipo=p.tipo.value,
                sede_retiro=p.sede_destino.nombre,
                fecha_inicio=p.fecha_inicio,
                fecha_vencimiento=p.fecha_vencimiento,
                vencido=p.esta_vencido(hoy),
            )
            for p in prestamos
        ]
        en_transito = [
            EnTransitoItem(
                remito=r.numero,
                tipo=r.tipo.value,
                libro=r.ejemplar.libro.titulo,
                codigo_ejemplar=r.ejemplar.codigo_inventario,
                sede_origen=r.sede_origen.nombre,
                sede_destino=r.sede_destino.nombre,
                fecha_despacho=r.fecha_despacho,
                horas_en_viaje=round((ahora - r.fecha_despacho).total_seconds() / 3600, 1),
            )
            for r in remitos
        ]
        return ReporteActivosYTransito(
            fecha=hoy,
            total_prestamos_activos=len(activos),
            total_en_transito=len(en_transito),
            prestamos_activos=activos,
            en_transito=en_transito,
        )

    def vencidos_y_multas(self, hoy: date | None = None) -> ReporteVencidosYMultas:
        hoy = hoy or date.today()
        calculo = PrestamoService(self.db)
        vencidos = self.db.scalars(
            select(Prestamo).where(
                Prestamo.estado == EstadoPrestamo.ACTIVO, Prestamo.fecha_vencimiento < hoy
            )
        ).all()
        con_multa = self.db.scalars(
            select(Prestamo).where(Prestamo.estado == EstadoPrestamo.DEVUELTO, Prestamo.multa > 0)
        ).all()

        socios: dict[int, SocioMultasItem] = {}

        def item_de(prestamo: Prestamo) -> SocioMultasItem:
            socio = prestamo.socio
            if socio.id not in socios:
                socios[socio.id] = SocioMultasItem(
                    socio_id=socio.id,
                    socio=socio.nombre_completo,
                    dni=socio.dni,
                    prestamos_vencidos=[],
                    multas_cobradas=0.0,
                    multas_pendientes=0.0,
                    total_acumulado=0.0,
                )
            return socios[socio.id]

        for p in vencidos:
            multa = calculo.multa_estimada(p, hoy)
            item = item_de(p)
            item.prestamos_vencidos.append(
                PrestamoVencidoItem(
                    prestamo_id=p.id,
                    libro=p.ejemplar.libro.titulo,
                    fecha_vencimiento=p.fecha_vencimiento,
                    dias_atraso=p.dias_atraso(hoy),
                    multa_estimada=multa,
                )
            )
            item.multas_pendientes += multa
        for p in con_multa:
            item_de(p).multas_cobradas += p.multa

        for item in socios.values():
            item.multas_pendientes = round(item.multas_pendientes, 2)
            item.multas_cobradas = round(item.multas_cobradas, 2)
            item.total_acumulado = round(item.multas_pendientes + item.multas_cobradas, 2)

        ordenados = sorted(socios.values(), key=lambda s: s.total_acumulado, reverse=True)
        return ReporteVencidosYMultas(
            fecha=hoy,
            total_prestamos_vencidos=len(vencidos),
            total_multas_pendientes=round(sum(s.multas_pendientes for s in ordenados), 2),
            total_multas_cobradas=round(sum(s.multas_cobradas for s in ordenados), 2),
            socios=ordenados,
        )

    def libros_mas_solicitados_intersede(
        self, desde: date | None = None, hasta: date | None = None, limite: int = 10
    ) -> list[LibroSolicitadoItem]:
        cantidad = func.count(Prestamo.id).label("cantidad")
        consulta = (
            select(Libro.id, Libro.titulo, Libro.autor, cantidad)
            .join(Ejemplar, Ejemplar.libro_id == Libro.id)
            .join(Prestamo, Prestamo.ejemplar_id == Ejemplar.id)
            .where(Prestamo.tipo == TipoPrestamo.INTERBIBLIOTECARIO)
            .group_by(Libro.id, Libro.titulo, Libro.autor)
            .order_by(cantidad.desc(), Libro.titulo)
            .limit(limite)
        )
        if desde is not None:
            consulta = consulta.where(Prestamo.fecha_solicitud >= desde)
        if hasta is not None:
            consulta = consulta.where(Prestamo.fecha_solicitud <= hasta)
        return [
            LibroSolicitadoItem(libro_id=f.id, titulo=f.titulo, autor=f.autor, cantidad_prestamos=f.cantidad)
            for f in self.db.execute(consulta)
        ]

    def disponibilidad_por_sede(self) -> list[DisponibilidadSedeItem]:
        filas = self.db.execute(
            select(Ejemplar.sede_id, Ejemplar.estado, func.count(Ejemplar.id))
            .where(Ejemplar.estado != EstadoEjemplar.BAJA)
            .group_by(Ejemplar.sede_id, Ejemplar.estado)
        ).all()
        titulos = dict(
            self.db.execute(
                select(Ejemplar.sede_id, func.count(func.distinct(Ejemplar.libro_id)))
                .where(Ejemplar.estado != EstadoEjemplar.BAJA)
                .group_by(Ejemplar.sede_id)
            ).all()
        )
        por_sede: dict[int, dict[str, int]] = defaultdict(dict)
        for sede_id, estado, cantidad in filas:
            por_sede[sede_id][estado.value] = cantidad

        resultado = []
        for sede in self.db.scalars(select(Sede).order_by(Sede.nombre)):
            estados = por_sede.get(sede.id, {})
            total = sum(estados.values())
            disponibles = estados.get(EstadoEjemplar.DISPONIBLE.value, 0)
            resultado.append(
                DisponibilidadSedeItem(
                    sede_id=sede.id,
                    sede=sede.nombre,
                    activa=sede.activa,
                    titulos_distintos=titulos.get(sede.id, 0),
                    total_ejemplares=total,
                    disponibles=disponibles,
                    porcentaje_disponible=round(disponibles * 100 / total, 1) if total else 0.0,
                    por_estado=estados,
                )
            )
        return resultado

    def tasa_envios(self, desde: date | None = None, hasta: date | None = None) -> ReporteEnvios:
        consulta = _rango(select(Remito), Remito.fecha_creacion, desde, hasta)
        remitos = self.db.scalars(consulta).all()

        recibidos = [r for r in remitos if r.estado == Recibido.nombre]
        con_danio = sum(1 for r in recibidos if r.estado_fisico_recepcion == EstadoFisico.DANADO)
        destruidos = sum(1 for r in recibidos if r.estado_fisico_recepcion == EstadoFisico.DESTRUIDO)
        extraviados = sum(1 for r in remitos if r.estado == Extraviado.nombre)
        cancelados = sum(1 for r in remitos if r.estado == Cancelado.nombre)
        en_curso = len(remitos) - len(recibidos) - extraviados - cancelados

        # Los cancelados no llegaron a viajar, por eso no cuentan para la tasa.
        viajaron = len(recibidos) + extraviados
        recibidos_ok = len(recibidos) - con_danio - destruidos
        incidencias = con_danio + destruidos + extraviados
        return ReporteEnvios(
            total_finalizados=viajaron + cancelados,
            recibidos_ok=recibidos_ok,
            recibidos_con_danio=con_danio,
            recibidos_destruidos=destruidos,
            extraviados=extraviados,
            cancelados=cancelados,
            en_curso=en_curso,
            tasa_exito=round(recibidos_ok * 100 / viajaron, 1) if viajaron else 0.0,
            tasa_incidencias=round(incidencias * 100 / viajaron, 1) if viajaron else 0.0,
        )

    def movimiento_entre_sedes(
        self, desde: date | None = None, hasta: date | None = None
    ) -> list[MovimientoSedesItem]:
        consulta = _rango(
            select(Remito).where(Remito.estado != Cancelado.nombre), Remito.fecha_creacion, desde, hasta
        )
        grupos: dict[tuple[str, str], list[Remito]] = defaultdict(list)
        for remito in self.db.scalars(consulta):
            grupos[(remito.sede_origen.nombre, remito.sede_destino.nombre)].append(remito)

        resultado = []
        for (origen, destino), remitos in grupos.items():
            horas = [r.horas_en_transito for r in remitos if r.horas_en_transito is not None]
            incidencias = sum(1 for r in remitos if r.tuvo_incidencia)
            resultado.append(
                MovimientoSedesItem(
                    sede_origen=origen,
                    sede_destino=destino,
                    envios=len(remitos),
                    recibidos=sum(1 for r in remitos if r.estado == Recibido.nombre),
                    incidencias=incidencias,
                    promedio_horas_transito=round(sum(horas) / len(horas), 1) if horas else None,
                )
            )
        return sorted(resultado, key=lambda m: m.envios, reverse=True)
