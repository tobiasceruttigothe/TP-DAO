from datetime import date, datetime, time

from sqlalchemy import select

from app.domain.enums import TipoIncidencia
from app.models import Incidencia, Remito
from app.repositories.base import BaseRepository, Paginacion, ResultadoPaginado


class IncidenciaRepository(BaseRepository[Incidencia]):
    modelo = Incidencia

    def listar_filtrado(
        self,
        paginacion: Paginacion,
        tipo: TipoIncidencia | None = None,
        sede_id: int | None = None,
        desde: date | None = None,
        hasta: date | None = None,
    ) -> ResultadoPaginado[Incidencia]:
        consulta = select(Incidencia).join(Remito).order_by(Incidencia.fecha.desc(), Incidencia.id.desc())
        if tipo is not None:
            consulta = consulta.where(Incidencia.tipo == tipo)
        if sede_id is not None:
            consulta = consulta.where((Remito.sede_origen_id == sede_id) | (Remito.sede_destino_id == sede_id))
        if desde is not None:
            consulta = consulta.where(Incidencia.fecha >= datetime.combine(desde, time.min))
        if hasta is not None:
            consulta = consulta.where(Incidencia.fecha <= datetime.combine(hasta, time.max))
        return self.paginar(consulta, paginacion)
