"""prefijo de sede para numerar los codigos de inventario

Revision ID: 0007
Revises: 0006
Create Date: 2026-11-17 19:00:00

Los codigos de inventario ahora los asigna el sistema (PREFIJO-NNNN). A las sedes que ya
existen se les completa el prefijo con el que usan sus ejemplares (CEN-0001 -> CEN); si no
tienen ejemplares o no siguen ese formato, se arma con el nombre (Sede Oeste -> OES).
"""
import re
import unicodedata
from collections import Counter
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0007'
down_revision: Union[str, None] = '0006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _letras(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Z ]", "", sin_tildes.upper())


def _candidatos_por_nombre(nombre: str) -> list[str]:
    palabras = _letras(nombre).split() or ["SEDE"]
    ultima = palabras[-1]
    iniciales = "".join(p[0] for p in palabras)[:5]
    return [ultima[:3], ultima[:4], ultima[:5], iniciales, (palabras[0][:2] + ultima[:3])[:5]]


def _prefijo_libre(candidatos: list[str], usados: set[str], sede_id: int) -> str:
    for candidato in candidatos:
        if 2 <= len(candidato) <= 5 and candidato not in usados:
            return candidato
    # Ultimo recurso: S + el id escrito con letras (1 -> SB, 2 -> SC...)
    numero, letras = sede_id, ""
    while True:
        numero, resto = divmod(numero, 26)
        letras = chr(65 + resto) + letras
        if numero == 0:
            break
    return ("S" + letras)[:5]


def upgrade() -> None:
    op.add_column('sedes', sa.Column('prefijo', sa.String(length=5), nullable=True))

    conexion = op.get_bind()
    sedes = conexion.execute(sa.text("SELECT id, nombre FROM sedes ORDER BY id")).all()
    usados: set[str] = set()
    for sede_id, nombre in sedes:
        codigos = conexion.execute(
            sa.text("SELECT codigo_inventario FROM ejemplares WHERE sede_id = :id"), {"id": sede_id}
        ).scalars()
        prefijos = Counter(m.group(1) for c in codigos if (m := re.fullmatch(r"([A-Z]{2,5})-\d+", c)))
        candidatos = [p for p, _ in prefijos.most_common()] + _candidatos_por_nombre(nombre)
        prefijo = _prefijo_libre(candidatos, usados, sede_id)
        usados.add(prefijo)
        conexion.execute(sa.text("UPDATE sedes SET prefijo = :p WHERE id = :id"), {"p": prefijo, "id": sede_id})

    op.alter_column('sedes', 'prefijo', nullable=False)
    op.create_unique_constraint('sedes_prefijo_key', 'sedes', ['prefijo'])


def downgrade() -> None:
    op.drop_constraint('sedes_prefijo_key', 'sedes', type_='unique')
    op.drop_column('sedes', 'prefijo')
