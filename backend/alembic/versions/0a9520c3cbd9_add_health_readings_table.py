"""add_health_readings_table

Revision ID: 0a9520c3cbd9
Revises: 48de9abcfbd6
Create Date: 2025-05-11 12:10:53.107112

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0a9520c3cbd9'
down_revision: Union[str, None] = '48de9abcfbd6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Define Enum type for HealthReadingType
healthreadingtype_enum = sa.Enum(
    'BLOOD_PRESSURE', 'GLUCOSE', 'HEART_RATE', 'WEIGHT', 'HEIGHT', 
    'BMI', 'SPO2', 'TEMPERATURE', 'RESPIRATORY_RATE', 'PAIN_LEVEL', 
    'STEPS', 'SLEEP', 'OTHER', 
    name='healthreadingtype'
)

def upgrade() -> None:
    # ### Create HealthReadings Table and its Enum ###

    # Attempt to drop ENUM type first, in case it exists from previous failed migrations
    op.execute("DROP TYPE IF EXISTS healthreadingtype CASCADE;")
    
    # Create the health_readings table
    op.create_table('health_readings',
        sa.Column('health_reading_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('reading_type', healthreadingtype_enum, nullable=False, index=True),
        sa.Column('numeric_value', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('unit', sa.String(), nullable=True),
        sa.Column('systolic_value', sa.Integer(), nullable=True),
        sa.Column('diastolic_value', sa.Integer(), nullable=True),
        sa.Column('text_value', sa.Text(), nullable=True),
        sa.Column('json_value', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('reading_date', sa.DateTime(), server_default=sa.text('now()'), nullable=False, index=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('source', sa.String(), nullable=True),
        sa.Column('related_document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.document_id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False)
    )
    # Explicitly create indexes if not handled by index=True in Column for some dialects or for specific naming
    # op.create_index(op.f('ix_health_readings_user_id'), 'health_readings', ['user_id'], unique=False) # Covered by index=True
    # op.create_index(op.f('ix_health_readings_reading_type'), 'health_readings', ['reading_type'], unique=False) # Covered by index=True
    # op.create_index(op.f('ix_health_readings_reading_date'), 'health_readings', ['reading_date'], unique=False) # Covered by index=True
    
    # ### End HealthReadings Table ###


def downgrade() -> None:
    # ### Downgrade for HealthReadings Table and its Enum ###
    
    # op.drop_index(op.f('ix_health_readings_reading_date'), table_name='health_readings') # If explicitly created
    # op.drop_index(op.f('ix_health_readings_reading_type'), table_name='health_readings') # If explicitly created
    # op.drop_index(op.f('ix_health_readings_user_id'), table_name='health_readings') # If explicitly created
    op.drop_table('health_readings')
    
    # Drop the ENUM type
    healthreadingtype_enum.drop(op.get_bind(), checkfirst=True)
    
    # ### End Downgrade HealthReadings Table ###
