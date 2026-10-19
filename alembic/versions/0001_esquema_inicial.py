"""esquema inicial

Revision ID: 0001
Revises: 
Create Date: 2026-10-19 20:06:35.228253

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('libros',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('isbn', sa.String(length=20), nullable=False),
    sa.Column('titulo', sa.String(length=200), nullable=False),
    sa.Column('autor', sa.String(length=150), nullable=False),
    sa.Column('editorial', sa.String(length=100), nullable=True),
    sa.Column('anio_publicacion', sa.Integer(), nullable=True),
    sa.Column('genero', sa.String(length=60), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('isbn')
    )
    op.create_table('sedes',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('nombre', sa.String(length=100), nullable=False),
    sa.Column('direccion', sa.String(length=200), nullable=False),
    sa.Column('telefono', sa.String(length=30), nullable=True),
    sa.Column('email', sa.String(length=120), nullable=True),
    sa.Column('horario', sa.String(length=200), nullable=True),
    sa.Column('activa', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('nombre')
    )
    op.create_table('socios',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('dni', sa.String(length=20), nullable=False),
    sa.Column('nombre', sa.String(length=100), nullable=False),
    sa.Column('apellido', sa.String(length=100), nullable=False),
    sa.Column('email', sa.String(length=120), nullable=False),
    sa.Column('telefono', sa.String(length=30), nullable=True),
    sa.Column('fecha_alta', sa.Date(), nullable=False),
    sa.Column('habilitado', sa.Boolean(), nullable=False),
    sa.Column('motivo_inhabilitacion', sa.String(length=200), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('dni'),
    sa.UniqueConstraint('email')
    )
    op.create_table('ejemplares',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('codigo_inventario', sa.String(length=30), nullable=False),
    sa.Column('libro_id', sa.Integer(), nullable=False),
    sa.Column('sede_id', sa.Integer(), nullable=False),
    sa.Column('estado', sa.Enum('DISPONIBLE', 'RESERVADO', 'PRESTADO', 'EN_TRANSITO', 'EN_REPARACION', 'EXTRAVIADO', 'BAJA', name='estadoejemplar', native_enum=False, length=20), nullable=False),
    sa.Column('estado_fisico', sa.Enum('BUENO', 'REGULAR', 'DANADO', name='estadofisico', native_enum=False, length=20), nullable=False),
    sa.ForeignKeyConstraint(['libro_id'], ['libros.id'], ),
    sa.ForeignKeyConstraint(['sede_id'], ['sedes.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('codigo_inventario')
    )
    op.create_table('prestamos',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('socio_id', sa.Integer(), nullable=False),
    sa.Column('ejemplar_id', sa.Integer(), nullable=False),
    sa.Column('sede_origen_id', sa.Integer(), nullable=False),
    sa.Column('sede_destino_id', sa.Integer(), nullable=False),
    sa.Column('tipo', sa.Enum('LOCAL', 'INTERBIBLIOTECARIO', name='tipoprestamo', native_enum=False, length=20), nullable=False),
    sa.Column('estado', sa.Enum('SOLICITADO', 'EN_TRANSITO', 'ACTIVO', 'DEVUELTO', 'CANCELADO', name='estadoprestamo', native_enum=False, length=20), nullable=False),
    sa.Column('fecha_solicitud', sa.Date(), nullable=False),
    sa.Column('fecha_inicio', sa.Date(), nullable=True),
    sa.Column('fecha_vencimiento', sa.Date(), nullable=True),
    sa.Column('fecha_devolucion', sa.Date(), nullable=True),
    sa.Column('estado_fisico_devolucion', sa.Enum('BUENO', 'REGULAR', 'DANADO', name='estadofisico', native_enum=False, length=20), nullable=True),
    sa.Column('multa', sa.Float(), nullable=False),
    sa.Column('observaciones', sa.String(length=300), nullable=True),
    sa.ForeignKeyConstraint(['ejemplar_id'], ['ejemplares.id'], ),
    sa.ForeignKeyConstraint(['sede_destino_id'], ['sedes.id'], ),
    sa.ForeignKeyConstraint(['sede_origen_id'], ['sedes.id'], ),
    sa.ForeignKeyConstraint(['socio_id'], ['socios.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('reservas',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('socio_id', sa.Integer(), nullable=False),
    sa.Column('libro_id', sa.Integer(), nullable=False),
    sa.Column('sede_id', sa.Integer(), nullable=False),
    sa.Column('ejemplar_id', sa.Integer(), nullable=True),
    sa.Column('estado', sa.Enum('PENDIENTE', 'DISPONIBLE', 'CUMPLIDA', 'CANCELADA', 'VENCIDA', name='estadoreserva', native_enum=False, length=20), nullable=False),
    sa.Column('fecha_reserva', sa.Date(), nullable=False),
    sa.Column('fecha_expiracion', sa.Date(), nullable=True),
    sa.ForeignKeyConstraint(['ejemplar_id'], ['ejemplares.id'], ),
    sa.ForeignKeyConstraint(['libro_id'], ['libros.id'], ),
    sa.ForeignKeyConstraint(['sede_id'], ['sedes.id'], ),
    sa.ForeignKeyConstraint(['socio_id'], ['socios.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('remitos',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('numero', sa.String(length=20), nullable=False),
    sa.Column('tipo', sa.Enum('IDA', 'RETORNO', name='tiporemito', native_enum=False, length=10), nullable=False),
    sa.Column('prestamo_id', sa.Integer(), nullable=False),
    sa.Column('ejemplar_id', sa.Integer(), nullable=False),
    sa.Column('sede_origen_id', sa.Integer(), nullable=False),
    sa.Column('sede_destino_id', sa.Integer(), nullable=False),
    sa.Column('estado', sa.String(length=20), nullable=False),
    sa.Column('fecha_creacion', sa.DateTime(), nullable=False),
    sa.Column('fecha_despacho', sa.DateTime(), nullable=True),
    sa.Column('fecha_recepcion', sa.DateTime(), nullable=True),
    sa.Column('estado_fisico_recepcion', sa.Enum('BUENO', 'REGULAR', 'DANADO', name='estadofisico', native_enum=False, length=20), nullable=True),
    sa.ForeignKeyConstraint(['ejemplar_id'], ['ejemplares.id'], ),
    sa.ForeignKeyConstraint(['prestamo_id'], ['prestamos.id'], ),
    sa.ForeignKeyConstraint(['sede_destino_id'], ['sedes.id'], ),
    sa.ForeignKeyConstraint(['sede_origen_id'], ['sedes.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('numero')
    )
    op.create_table('movimientos_remito',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('remito_id', sa.Integer(), nullable=False),
    sa.Column('estado_anterior', sa.String(length=20), nullable=True),
    sa.Column('estado_nuevo', sa.String(length=20), nullable=False),
    sa.Column('fecha', sa.DateTime(), nullable=False),
    sa.Column('observacion', sa.String(length=300), nullable=True),
    sa.ForeignKeyConstraint(['remito_id'], ['remitos.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('movimientos_remito')
    op.drop_table('remitos')
    op.drop_table('reservas')
    op.drop_table('prestamos')
    op.drop_table('ejemplares')
    op.drop_table('socios')
    op.drop_table('sedes')
    op.drop_table('libros')
