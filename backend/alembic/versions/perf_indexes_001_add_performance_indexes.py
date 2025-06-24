"""Add performance indexes for common query patterns

Revision ID: perf_indexes_001
Revises: 7f426826590e
Create Date: 2024-12-15 10:00:00.000000

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
    """Add performance-critical indexes for common query patterns."""
    
 
    op.create_index(
        'idx_medications_user_status_updated', 
        'medications', 
        ['user_id', 'status', 'updated_at'],
        postgresql_concurrently=True,
        postgresql_using='btree'
    )
    
    
    op.create_index(
        'idx_medications_user_active',
        'medications',
        ['user_id', 'updated_at'],
        postgresql_where=sa.text("status = 'active'"),
        postgresql_concurrently=True,
        postgresql_using='btree'
    )
    
   
    op.execute("""
        CREATE INDEX CONCURRENTLY idx_medications_search 
        ON medications USING gin(
            (user_id::text || ' ' || 
             coalesce(name, '') || ' ' || 
             coalesce(reason, '') || ' ' || 
             coalesce(prescribing_doctor, '') || ' ' ||
             coalesce(notes, '')) gin_trgm_ops
        )
    """)
    
   
    op.create_index(
        'idx_documents_user_type_upload', 
        'documents', 
        ['user_id', 'document_type', 'upload_timestamp'],
        postgresql_concurrently=True,
        postgresql_using='btree'
    )
    
    
    op.create_index(
        'idx_documents_user_upload',
        'documents',
        ['user_id', 'upload_timestamp'],
        postgresql_concurrently=True,
        postgresql_using='btree'
    )
    
    
    op.create_index(
        'idx_documents_hash_user',
        'documents',
        ['file_hash', 'user_id'],
        postgresql_concurrently=True,
        postgresql_using='btree'
    )
    
    
    op.execute("""
        CREATE INDEX CONCURRENTLY idx_documents_fulltext_search 
        ON documents USING gin(
            to_tsvector('english', 
                coalesce(original_filename, '') || ' ' || 
                coalesce(source_name, '') || ' ' ||
                coalesce(tags::text, '')
            )
        )
    """)
    
    
    op.create_index(
        'idx_health_readings_user_type_date', 
        'health_readings', 
        ['user_id', 'reading_type', 'reading_date'],
        postgresql_concurrently=True,
        postgresql_using='btree'
    )
    
   
    op.create_index(
        'idx_health_readings_user_date',
        'health_readings',
        ['user_id', 'reading_date'],
        postgresql_concurrently=True,
        postgresql_using='btree'
    )
    
    
    op.create_index(
        'idx_symptoms_user_date',
        'symptoms',
        ['user_id', 'onset_date'],
        postgresql_concurrently=True,
        postgresql_using='btree'
    )
    
    op.create_index(
        'idx_symptoms_user_severity',
        'symptoms',
        ['user_id', 'severity', 'onset_date'],
        postgresql_concurrently=True,
        postgresql_using='btree'
    )
    
    
    op.create_index(
        'idx_notifications_user_unread',
        'notifications',
        ['user_id', 'is_read', 'created_at'],
        postgresql_concurrently=True,
        postgresql_using='btree'
    )
    
    op.create_index(
        'idx_notifications_user_severity',
        'notifications',
        ['user_id', 'severity', 'created_at'],
        postgresql_concurrently=True,
        postgresql_using='btree'
    )
    
    op.create_index(
        'idx_notifications_user_type',
        'notifications',
        ['user_id', 'notification_type', 'created_at'],
        postgresql_concurrently=True,
        postgresql_using='btree'
    )
    
    
    op.create_index(
        'idx_extracted_data_document',
        'extracted_data',
        ['document_id'],
        postgresql_concurrently=True,
        postgresql_using='btree'
    )
    
   
    op.create_index(
        'idx_users_supabase_id',
        'users',
        ['supabase_id'],
        postgresql_concurrently=True,
        postgresql_using='btree'
    )


def downgrade() -> None:
    """Remove performance indexes."""
    
    
    indexes_to_drop = [
        'idx_medications_user_status_updated',
        'idx_medications_user_active', 
        'idx_medications_search',
        'idx_documents_user_type_upload',
        'idx_documents_user_upload',
        'idx_documents_hash_user',
        'idx_documents_fulltext_search',
        'idx_health_readings_user_type_date',
        'idx_health_readings_user_date',
        'idx_symptoms_user_date',
        'idx_symptoms_user_severity',
        'idx_notifications_user_unread',
        'idx_notifications_user_severity',
        'idx_notifications_user_type',
        'idx_extracted_data_document',
        'idx_users_supabase_id'
    ]
    
    for index_name in indexes_to_drop:
        try:
            op.drop_index(index_name, postgresql_concurrently=True)
        except Exception:
            
            pass 