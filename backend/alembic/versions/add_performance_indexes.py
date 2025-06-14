"""add_performance_indexes

Revision ID: perf_indexes_001
Revises: 7f426826590e
Create Date: 2024-01-15 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'perf_indexes_001'
down_revision: Union[str, None] = '7f426826590e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add performance-critical indexes for MediMind application."""
    
    # === MEDICATIONS TABLE INDEXES ===
    # Composite index for user + status queries (most common)
    op.create_index(
        'idx_medications_user_status_updated', 
        'medications', 
        ['user_id', 'status', 'updated_at']
    )
    
    # Index for medication search queries
    op.create_index(
        'idx_medications_search_fields', 
        'medications', 
        ['user_id', 'name', 'prescribing_doctor']
    )
    
    # Index for date range queries
    op.create_index(
        'idx_medications_date_range', 
        'medications', 
        ['user_id', 'start_date', 'end_date']
    )
    
    # === DOCUMENTS TABLE INDEXES ===
    # Composite index for user + type + upload time (most common query pattern)
    op.create_index(
        'idx_documents_user_type_upload', 
        'documents', 
        ['user_id', 'document_type', 'upload_timestamp']
    )
    
    # Index for document search by filename
    op.create_index(
        'idx_documents_filename_search', 
        'documents', 
        ['user_id', 'original_filename']
    )
    
    # Index for document date queries
    op.create_index(
        'idx_documents_user_date', 
        'documents', 
        ['user_id', 'document_date']
    )
    
    # Full-text search index for PostgreSQL
    op.execute("""
        CREATE INDEX idx_documents_fulltext_search 
        ON documents 
        USING gin(to_tsvector('english', 
            coalesce(original_filename, '') || ' ' || 
            coalesce(source_name, '') || ' ' || 
            coalesce(source_location_city, '') || ' ' ||
            coalesce(related_to_health_goal_or_episode, '')
        ))
    """)
    
    # === HEALTH READINGS TABLE INDEXES ===
    # Composite index for user + type + date (most common query)
    op.create_index(
        'idx_health_readings_user_type_date', 
        'health_readings', 
        ['user_id', 'reading_type', 'reading_date']
    )
    
    # Index for recent readings dashboard queries
    op.create_index(
        'idx_health_readings_recent', 
        'health_readings', 
        ['user_id', 'reading_date']
    )
    
    # === EXTRACTED DATA TABLE INDEXES ===
    # Index for review status queries
    op.create_index(
        'idx_extracted_data_review_status', 
        'extracted_data', 
        ['review_status', 'extraction_timestamp']
    )
    
    # Full-text search index for extracted content
    op.execute("""
        CREATE INDEX idx_extracted_data_fulltext 
        ON extracted_data 
        USING gin(to_tsvector('english', coalesce(raw_text, '')))
    """)
    
    # === NOTIFICATIONS TABLE INDEXES ===
    # Restore critical notification indexes that were dropped
    op.create_index(
        'idx_notifications_user_created', 
        'notifications', 
        ['user_id', 'created_at']
    )
    
    op.create_index(
        'idx_notifications_user_unread', 
        'notifications', 
        ['user_id', 'is_read', 'created_at']
    )
    
    op.create_index(
        'idx_notifications_severity', 
        'notifications', 
        ['user_id', 'severity', 'created_at']
    )
    
    # Indexes for related entity lookups
    op.create_index(
        'idx_notifications_related_medication', 
        'notifications', 
        ['related_medication_id']
    )
    
    op.create_index(
        'idx_notifications_related_document', 
        'notifications', 
        ['related_document_id']
    )
    
    op.create_index(
        'idx_notifications_related_health_reading', 
        'notifications', 
        ['related_health_reading_id']
    )
    
    # === USERS TABLE INDEXES ===
    # Restore unique indexes that were dropped
    op.create_index(
        'idx_users_email_unique', 
        'users', 
        ['email'], 
        unique=True
    )
    
    op.create_index(
        'idx_users_supabase_id_unique', 
        'users', 
        ['supabase_id'], 
        unique=True
    )
    
    # Index for user activity tracking
    op.create_index(
        'idx_users_last_login', 
        'users', 
        ['last_login']
    )


def downgrade() -> None:
    """Remove performance indexes."""
    
    # Drop all indexes created in upgrade
    op.drop_index('idx_medications_user_status_updated', table_name='medications')
    op.drop_index('idx_medications_search_fields', table_name='medications')
    op.drop_index('idx_medications_date_range', table_name='medications')
    
    op.drop_index('idx_documents_user_type_upload', table_name='documents')
    op.drop_index('idx_documents_filename_search', table_name='documents')
    op.drop_index('idx_documents_user_date', table_name='documents')
    op.drop_index('idx_documents_fulltext_search', table_name='documents')
    
    op.drop_index('idx_health_readings_user_type_date', table_name='health_readings')
    op.drop_index('idx_health_readings_recent', table_name='health_readings')
    
    op.drop_index('idx_extracted_data_review_status', table_name='extracted_data')
    op.drop_index('idx_extracted_data_fulltext', table_name='extracted_data')
    
    op.drop_index('idx_notifications_user_created', table_name='notifications')
    op.drop_index('idx_notifications_user_unread', table_name='notifications')
    op.drop_index('idx_notifications_severity', table_name='notifications')
    op.drop_index('idx_notifications_related_medication', table_name='notifications')
    op.drop_index('idx_notifications_related_document', table_name='notifications')
    op.drop_index('idx_notifications_related_health_reading', table_name='notifications')
    
    op.drop_index('idx_users_email_unique', table_name='users')
    op.drop_index('idx_users_supabase_id_unique', table_name='users')
    op.drop_index('idx_users_last_login', table_name='users') 