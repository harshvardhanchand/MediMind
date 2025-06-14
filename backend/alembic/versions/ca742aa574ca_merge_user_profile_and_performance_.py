"""merge_user_profile_and_performance_indexes

Revision ID: ca742aa574ca
Revises: 92303b9b79fb, perf_indexes_001
Create Date: 2025-06-14 19:14:23.307111

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ca742aa574ca'
down_revision: Union[str, None] = ('92303b9b79fb', 'perf_indexes_001')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
