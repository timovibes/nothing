"""add format to report_exports

Revision ID: f0f50aa1bc1a
Revises: 9098ed2aa9c4
Create Date: 2026-08-10 11:44:21.951470

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f0f50aa1bc1a'
down_revision: Union[str, None] = '9098ed2aa9c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    report_format_enum = sa.Enum('CSV', 'PDF', name='reportformat')
    report_format_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        'report_exports',
        sa.Column(
            'format',
            sa.Enum('CSV', 'PDF', name='reportformat', create_type=False),
            nullable=False,
            server_default='CSV',
        ),
    )
    op.alter_column('report_exports', 'format', server_default=None)


def downgrade() -> None:
    op.drop_column('report_exports', 'format')
    sa.Enum(name='reportformat').drop(op.get_bind(), checkfirst=True)