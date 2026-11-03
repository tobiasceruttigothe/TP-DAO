"""detalle de multa

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-03 21:44:42.973585

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0005'
down_revision: Union[str, None] = '0004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('prestamos', sa.Column('detalle_multa', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('prestamos', 'detalle_multa')
