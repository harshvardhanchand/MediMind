"""add_medical_conditions_to_user_profile

Revision ID: medical_conditions_001
Revises: ca742aa574ca
Create Date: 2025-06-14 19:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'medical_conditions_001'
down_revision: Union[str, None] = 'ca742aa574ca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add medical_conditions JSON field to users table."""
    
    # Add medical_conditions column to users table
    op.add_column('users', sa.Column('medical_conditions', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Remove medical_conditions field from users table."""
    
    # Remove medical_conditions column from users table
    op.drop_column('users', 'medical_conditions') 