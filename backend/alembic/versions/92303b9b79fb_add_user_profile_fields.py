"""add_user_profile_fields

Revision ID: 92303b9b79fb
Revises: 7f426826590e
Create Date: 2025-06-12 23:26:16.825607

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '92303b9b79fb'
down_revision: Union[str, None] = '7f426826590e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add user profile columns to users table
    op.add_column('users', sa.Column('name', sa.String(), nullable=True))
    op.add_column('users', sa.Column('date_of_birth', sa.Date(), nullable=True))
    op.add_column('users', sa.Column('weight', sa.Numeric(precision=5, scale=2), nullable=True))
    op.add_column('users', sa.Column('height', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('gender', sa.String(10), nullable=True))
    op.add_column('users', sa.Column('profile_photo_url', sa.String(), nullable=True))
    
    # Add check constraints for data validation
    op.create_check_constraint(
        'check_weight_positive',
        'users',
        'weight > 0 AND weight <= 1000'
    )
    op.create_check_constraint(
        'check_height_positive', 
        'users',
        'height > 0 AND height <= 300'
    )
    op.create_check_constraint(
        'check_gender_valid',
        'users', 
        "gender IN ('male', 'female', 'other')"
    )


def downgrade() -> None:
    # Drop check constraints first
    op.drop_constraint('check_gender_valid', 'users', type_='check')
    op.drop_constraint('check_height_positive', 'users', type_='check')
    op.drop_constraint('check_weight_positive', 'users', type_='check')
    
    # Drop columns
    op.drop_column('users', 'profile_photo_url')
    op.drop_column('users', 'gender')
    op.drop_column('users', 'height')
    op.drop_column('users', 'weight')
    op.drop_column('users', 'date_of_birth')
    op.drop_column('users', 'name')
