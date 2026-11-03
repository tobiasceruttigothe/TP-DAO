"""numero de remito por secuencia

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-03 12:00:00

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SEQUENCE remitos_numero_seq")
    # Continua despues del ultimo remito existente
    op.execute("SELECT setval('remitos_numero_seq', COALESCE((SELECT MAX(id) FROM remitos), 0) + 1, false)")


def downgrade() -> None:
    op.execute("DROP SEQUENCE remitos_numero_seq")
