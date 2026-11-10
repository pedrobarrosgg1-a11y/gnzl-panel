"""sub ids no lote

Revision ID: ecc7e5e706b4
Revises: f843edeec799
Create Date: 2026-11-09 22:08:20.286055

Os Sub IDs ficam no lote porque um novo `run` precisa reexecutar os itens
falhos com exatamente a mesma configuração usada na criação.

Nota sobre SQLite: adicionar CHECK exige recriar a tabela. O SQLAlchemy reflete
as constraints CHECK existentes, então elas são preservadas no rebuild — aqui
declaramos apenas as cinco novas.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "ecc7e5e706b4"
down_revision: Union[str, Sequence[str], None] = "f843edeec799"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_SUB_ID_CHECK = (
    "{column} IS NULL OR ("
    "{column} NOT GLOB '*[^a-z0-9-]*' "
    "AND length({column}) BETWEEN 1 AND 64)"
)


def _sub_id_checks() -> list[tuple[str, str]]:
    return [
        (f"sub_id_{index}_format", _SUB_ID_CHECK.format(column=f"sub_id_{index}"))
        for index in range(1, 6)
    ]


def upgrade() -> None:
    with op.batch_alter_table("link_batches", schema=None) as batch_op:
        for index in range(1, 6):
            batch_op.add_column(sa.Column(f"sub_id_{index}", sa.String(length=64)))

        for name, condition in _sub_id_checks():
            batch_op.create_check_constraint(name, condition)


def downgrade() -> None:
    with op.batch_alter_table("link_batches", schema=None) as batch_op:
        for name, _condition in _sub_id_checks():
            batch_op.drop_constraint(name, type_="check")
        for index in range(5, 0, -1):
            batch_op.drop_column(f"sub_id_{index}")
