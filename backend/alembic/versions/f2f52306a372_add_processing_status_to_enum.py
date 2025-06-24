"""add_processing_status_to_enum

Revision ID: f2f52306a372
Revises: medical_conditions_001
Create Date: 2025-06-24 23:48:24.334809

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f2f52306a372'
down_revision: Union[str, None] = 'medical_conditions_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add the 'processing' value to the processingstatus enum
    op.execute("ALTER TYPE processingstatus ADD VALUE 'processing'")


def downgrade() -> None:
    # Note: PostgreSQL doesn't support removing enum values directly
    # This would require recreating the enum type and updating all references
    # For now, we'll leave this as a no-op since enum value removal is complex
    pass
