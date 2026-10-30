"""incidencias de envio

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-30 17:06:18.652586

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0002'
down_revision: Union[str, None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('incidencias',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('remito_id', sa.Integer(), nullable=False),
    sa.Column('tipo', sa.Enum('DANIO', 'DESTRUCCION', 'EXTRAVIO', name='tipoincidencia', native_enum=False, length=20), nullable=False),
    sa.Column('descripcion', sa.String(length=300), nullable=True),
    sa.Column('fecha', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['remito_id'], ['remitos.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('incidencias')
