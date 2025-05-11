"""create_initial_tables

Revision ID: 48de9abcfbd6
Revises: 
Create Date: 2025-05-11 12:00:33.276748

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '48de9abcfbd6'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Define Enum types that will be used
documenttype_enum = sa.Enum('prescription', 'lab_result', 'imaging_report', 'consultation_note', 'discharge_summary', 'other', name='documenttype')
processingstatus_enum = sa.Enum('pending', 'ocr_completed', 'extraction_completed', 'review_required', 'completed', 'failed', name='processingstatus')
reviewstatus_enum = sa.Enum('pending_review', 'reviewed_corrected', 'reviewed_approved', name='reviewstatus')
medicationfrequency_enum = sa.Enum('once_daily', 'twice_daily', 'three_times_daily', 'four_times_daily', 'every_other_day', 'once_weekly', 'twice_weekly', 'once_monthly', 'as_needed', 'other', name='medicationfrequency')
medicationstatus_enum = sa.Enum('active', 'discontinued', 'completed', 'on_hold', name='medicationstatus')


def upgrade() -> None:
    # Attempt to drop ENUM types first, in case they exist from previous failed migrations
    # Using op.execute for raw SQL might be more robust here if sa.Enum().drop() has issues in this context
    op.execute("DROP TYPE IF EXISTS documenttype CASCADE;")
    op.execute("DROP TYPE IF EXISTS processingstatus CASCADE;")
    op.execute("DROP TYPE IF EXISTS reviewstatus CASCADE;")
    op.execute("DROP TYPE IF EXISTS medicationfrequency CASCADE;")
    op.execute("DROP TYPE IF EXISTS medicationstatus CASCADE;")

    # Now, create the ENUM types (SQLAlchemy will typically handle this when creating tables,
    # but explicit creation can be done if needed, or let table creation handle it)
    # For this attempt, we'll let table creation try to create them after ensuring they are dropped.

    # Create users table
    op.create_table('users',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('supabase_id', sa.String(), nullable=True),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('user_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('app_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('user_id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('supabase_id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_supabase_id'), 'users', ['supabase_id'], unique=True)

    # Create documents table
    op.create_table('documents',
        sa.Column('document_id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('original_filename', sa.String(), nullable=False),
        sa.Column('storage_path', sa.String(), nullable=False),
        sa.Column('document_type', documenttype_enum, nullable=False),
        sa.Column('upload_timestamp', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('processing_status', processingstatus_enum, server_default='pending', nullable=False),
        sa.Column('file_hash', sa.String(), nullable=True),
        sa.Column('file_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('document_date', sa.Date(), nullable=True),
        sa.Column('source_name', sa.String(), nullable=True),
        sa.Column('source_location_city', sa.String(), nullable=True),
        sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('user_added_tags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('related_to_health_goal_or_episode', sa.String(), nullable=True),
        sa.Column('metadata_overrides', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('document_id'),
        sa.UniqueConstraint('storage_path')
    )
    op.create_index(op.f('ix_documents_user_id'), 'documents', ['user_id'], unique=False)
    op.create_index(op.f('ix_documents_file_hash'), 'documents', ['file_hash'], unique=False) # Assuming not unique per user for simplicity here
    op.create_index(op.f('ix_documents_document_type'), 'documents', ['document_type'], unique=False)
    op.create_index(op.f('ix_documents_processing_status'), 'documents', ['processing_status'], unique=False)


    # Create extracted_data table
    op.create_table('extracted_data',
        sa.Column('extracted_data_id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('raw_text', sa.Text(), nullable=True),
        sa.Column('extraction_timestamp', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('review_status', reviewstatus_enum, server_default='pending_review', nullable=False),
        sa.Column('reviewed_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('review_timestamp', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.document_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reviewed_by_user_id'], ['users.user_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('extracted_data_id'),
        sa.UniqueConstraint('document_id') # Ensuring one-to-one with Document
    )
    op.create_index(op.f('ix_extracted_data_review_status'), 'extracted_data', ['review_status'], unique=False)


    # Create medications table
    op.create_table('medications',
        sa.Column('medication_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(), nullable=False, index=True),
        sa.Column('dosage', sa.String(), nullable=True),
        sa.Column('frequency', medicationfrequency_enum, nullable=False),
        sa.Column('frequency_details', sa.String(), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('time_of_day', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('with_food', sa.Boolean(), nullable=True),
        sa.Column('reason', sa.String(), nullable=True),
        sa.Column('prescribing_doctor', sa.String(), nullable=True),
        sa.Column('pharmacy', sa.String(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('status', medicationstatus_enum, server_default='active', nullable=False),
        sa.Column('related_document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.document_id', ondelete='SET NULL'), nullable=True),
        sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False)
    )
    # Indexes for medications were specified with sa.Column(index=True), Alembic autogenerates op.f() named indexes
    # If you need more control or different names, add op.create_index() calls here.
    # Example: op.create_index(op.f('ix_medications_name'), 'medications', ['name'], unique=False)
    # op.create_index(op.f('ix_medications_user_id'), 'medications', ['user_id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    # Drop in reverse order of creation
    
    # Drop medications table and its enums (if they were created by this migration and are not shared)
    # op.drop_index(op.f('ix_medications_user_id'), table_name='medications') # If explicitly created
    # op.drop_index(op.f('ix_medications_name'), table_name='medications') # If explicitly created
    op.drop_table('medications')
    medicationfrequency_enum.drop(op.get_bind(), checkfirst=True)
    medicationstatus_enum.drop(op.get_bind(), checkfirst=True)

    # Drop extracted_data table and its enums
    op.drop_index(op.f('ix_extracted_data_review_status'), table_name='extracted_data')
    op.drop_table('extracted_data')
    reviewstatus_enum.drop(op.get_bind(), checkfirst=True)

    # Drop documents table and its enums
    op.drop_index(op.f('ix_documents_processing_status'), table_name='documents')
    op.drop_index(op.f('ix_documents_document_type'), table_name='documents')
    op.drop_index(op.f('ix_documents_file_hash'), table_name='documents')
    op.drop_index(op.f('ix_documents_user_id'), table_name='documents')
    op.drop_table('documents')
    documenttype_enum.drop(op.get_bind(), checkfirst=True)
    processingstatus_enum.drop(op.get_bind(), checkfirst=True)

    # Drop users table
    op.drop_index(op.f('ix_users_supabase_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    # ### end Alembic commands ###
