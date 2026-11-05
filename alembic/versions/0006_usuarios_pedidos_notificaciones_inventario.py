"""usuarios, pedidos, notificaciones e inventario

Revision ID: 0006
Revises: 0005
Create Date: 2026-11-04 20:11:49.169879

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0006'
down_revision: Union[str, None] = '0005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('inventarios',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('sede_id', sa.Integer(), nullable=False),
    sa.Column('estado', sa.Enum('EN_CURSO', 'CERRADO', name='estadoinventario', native_enum=False, length=20), nullable=False),
    sa.Column('fecha_inicio', sa.DateTime(), nullable=False),
    sa.Column('fecha_cierre', sa.DateTime(), nullable=True),
    sa.Column('observacion', sa.String(length=300), nullable=True),
    sa.Column('resumen', sa.JSON(), nullable=True),
    sa.ForeignKeyConstraint(['sede_id'], ['sedes.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('usuarios',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('email', sa.String(length=120), nullable=False),
    sa.Column('nombre', sa.String(length=100), nullable=False),
    sa.Column('hash_contrasena', sa.String(length=100), nullable=False),
    sa.Column('rol', sa.Enum('ADMIN', 'SOCIO', name='rol', native_enum=False, length=10), nullable=False),
    sa.Column('estado', sa.Enum('PENDIENTE_CONFIRMACION', 'PENDIENTE_APROBACION', 'ACTIVO', 'RECHAZADO', name='estadousuario', native_enum=False, length=30), nullable=False),
    sa.Column('socio_id', sa.Integer(), nullable=True),
    sa.Column('recibe_correos', sa.Boolean(), nullable=False),
    sa.Column('token_confirmacion', sa.String(length=64), nullable=True),
    sa.Column('fecha_alta', sa.DateTime(), nullable=False),
    sa.Column('motivo_rechazo', sa.String(length=200), nullable=True),
    sa.ForeignKeyConstraint(['socio_id'], ['socios.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('socio_id'),
    sa.UniqueConstraint('token_confirmacion')
    )
    op.create_table('items_inventario',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('inventario_id', sa.Integer(), nullable=False),
    sa.Column('codigo', sa.String(length=30), nullable=False),
    sa.Column('ejemplar_id', sa.Integer(), nullable=True),
    sa.Column('fecha', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['ejemplar_id'], ['ejemplares.id'], ),
    sa.ForeignKeyConstraint(['inventario_id'], ['inventarios.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('inventario_id', 'codigo', name='uq_item_inventario_codigo')
    )
    op.create_table('notificaciones',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('usuario_id', sa.Integer(), nullable=False),
    sa.Column('tipo', sa.Enum('REGISTRO_PENDIENTE', 'CUENTA_APROBADA', 'CUENTA_RECHAZADA', 'PEDIDO_NUEVO', 'PEDIDO_APROBADO', 'PEDIDO_RECHAZADO', 'RESERVA_DISPONIBLE', 'LISTO_PARA_RETIRAR', 'PRESTAMO_POR_VENCER', 'PRESTAMO_VENCIDO', 'SOCIO_INHABILITADO', name='tiponotificacion', native_enum=False, length=30), nullable=False),
    sa.Column('titulo', sa.String(length=150), nullable=False),
    sa.Column('mensaje', sa.String(length=500), nullable=False),
    sa.Column('enlace', sa.String(length=200), nullable=True),
    sa.Column('leida', sa.Boolean(), nullable=False),
    sa.Column('fecha', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('pedidos',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('socio_id', sa.Integer(), nullable=False),
    sa.Column('libro_id', sa.Integer(), nullable=False),
    sa.Column('sede_id', sa.Integer(), nullable=False),
    sa.Column('estado', sa.Enum('PENDIENTE', 'APROBADO', 'RECHAZADO', 'CANCELADO', name='estadopedido', native_enum=False, length=20), nullable=False),
    sa.Column('comentario', sa.String(length=300), nullable=True),
    sa.Column('fecha', sa.DateTime(), nullable=False),
    sa.Column('fecha_resolucion', sa.DateTime(), nullable=True),
    sa.Column('resolucion', sa.String(length=300), nullable=True),
    sa.Column('reserva_id', sa.Integer(), nullable=True),
    sa.Column('prestamo_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['libro_id'], ['libros.id'], ),
    sa.ForeignKeyConstraint(['prestamo_id'], ['prestamos.id'], ),
    sa.ForeignKeyConstraint(['reserva_id'], ['reservas.id'], ),
    sa.ForeignKeyConstraint(['sede_id'], ['sedes.id'], ),
    sa.ForeignKeyConstraint(['socio_id'], ['socios.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column('prestamos', sa.Column('aviso_por_vencer', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('prestamos', sa.Column('aviso_vencido', sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade() -> None:
    op.drop_column('prestamos', 'aviso_vencido')
    op.drop_column('prestamos', 'aviso_por_vencer')
    op.drop_table('pedidos')
    op.drop_table('notificaciones')
    op.drop_table('items_inventario')
    op.drop_table('usuarios')
    op.drop_table('inventarios')
