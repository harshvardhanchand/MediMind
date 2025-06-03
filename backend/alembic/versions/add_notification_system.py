"""Add notification system tables

Revision ID: add_notification_system
Revises: previous_revision
Create Date: 2024-01-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_notification_system'
down_revision = 'previous_revision'  # Update this to your latest revision
branch_labels = None
depends_on = None


def upgrade():
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Notifications table
    op.create_table('notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_dismissed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('expires_at', sa.TIMESTAMP(), nullable=True),
        
        # Links to existing tables that triggered the notification
        sa.Column('related_medication_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('related_document_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('related_health_reading_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('related_extracted_data_id', postgresql.UUID(as_uuid=True), nullable=True),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['related_medication_id'], ['medications.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['related_document_id'], ['documents.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['related_health_reading_id'], ['health_readings.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['related_extracted_data_id'], ['extracted_data.id'], ondelete='SET NULL'),
    )
    
    # Medical situations vector storage using pgvector
    op.create_table('medical_situations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('medical_context', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('analysis_result', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('similarity_threshold', sa.Float(), nullable=False, server_default='0.85'),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('last_used_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Add vector column using pgvector (768 dimensions for BioBERT)
    op.execute('ALTER TABLE medical_situations ADD COLUMN embedding vector(768)')
    
    # AI analysis logs for debugging
    op.create_table('ai_analysis_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('trigger_type', sa.String(50), nullable=False),
        sa.Column('medical_profile_hash', sa.String(64), nullable=False),
        sa.Column('similarity_matches', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('llm_called', sa.Boolean(), nullable=False),
        sa.Column('llm_cost', sa.Float(), nullable=True),
        sa.Column('processing_time_ms', sa.Integer(), nullable=False),
        sa.Column('analysis_result', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('NOW()')),
        
        # Links to triggering entities
        sa.Column('related_medication_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('related_document_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('related_health_reading_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('related_extracted_data_id', postgresql.UUID(as_uuid=True), nullable=True),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['related_medication_id'], ['medications.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['related_document_id'], ['documents.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['related_health_reading_id'], ['health_readings.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['related_extracted_data_id'], ['extracted_data.id'], ondelete='SET NULL'),
    )
    
    # Add vector column for analysis logs too (for debugging)
    op.execute('ALTER TABLE ai_analysis_logs ADD COLUMN embedding vector(768)')
    
    # Indexes for performance
    op.create_index('idx_notifications_user_created', 'notifications', ['user_id', 'created_at'])
    op.create_index('idx_notifications_unread', 'notifications', ['user_id', 'is_read'])
    op.create_index('idx_notifications_related_medication', 'notifications', ['related_medication_id'])
    op.create_index('idx_notifications_related_document', 'notifications', ['related_document_id'])
    op.create_index('idx_notifications_related_health_reading', 'notifications', ['related_health_reading_id'])
    op.create_index('idx_medical_situations_confidence', 'medical_situations', ['confidence_score'])
    op.create_index('idx_ai_analysis_user_trigger', 'ai_analysis_logs', ['user_id', 'trigger_type'])
    op.create_index('idx_ai_analysis_related_medication', 'ai_analysis_logs', ['related_medication_id'])
    op.create_index('idx_ai_analysis_related_document', 'ai_analysis_logs', ['related_document_id'])
    
    # Vector similarity index (HNSW for fast similarity search)
    op.execute('CREATE INDEX ON medical_situations USING hnsw (embedding vector_cosine_ops)')


def downgrade():
    op.drop_table('ai_analysis_logs')
    op.drop_table('medical_situations')
    op.drop_table('notifications')
    op.execute('DROP EXTENSION IF EXISTS vector') 