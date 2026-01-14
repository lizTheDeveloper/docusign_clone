"""Add documents tables.

Revision ID: 002
Revises: 001
Create Date: 2026-01-13 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create documents and document_pages tables."""
    
    # Create documents table
    op.create_table(
        'documents',
        sa.Column('document_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('original_filename', sa.String(255), nullable=False),
        sa.Column('storage_key', sa.String(500), nullable=False),
        sa.Column('file_type', sa.String(100), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=False),
        sa.Column('page_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('checksum', sa.String(64), nullable=False),
        sa.Column('encryption_key_id', sa.String(100), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='processing'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('thumbnail_storage_key', sa.String(500), nullable=True),
        sa.Column('in_use_by_envelopes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.CheckConstraint("status IN ('processing', 'ready', 'failed')", name='check_document_status'),
    )
    
    # Create indexes for documents table
    op.create_index('idx_documents_user_id', 'documents', ['user_id'])
    op.create_index('idx_documents_status', 'documents', ['status'])
    op.create_index('idx_documents_uploaded_at', 'documents', ['uploaded_at'])
    op.create_index('idx_documents_checksum', 'documents', ['checksum'])
    
    # Create document_pages table
    op.create_table(
        'document_pages',
        sa.Column('page_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=False),
        sa.Column('width', sa.Float(), nullable=False),
        sa.Column('height', sa.Float(), nullable=False),
        sa.Column('thumbnail_storage_key', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['document_id'], ['documents.document_id'], ondelete='CASCADE'),
        sa.UniqueConstraint('document_id', 'page_number', name='uq_document_page_number'),
    )
    
    # Create indexes for document_pages table
    op.create_index('idx_document_pages_document_id', 'document_pages', ['document_id'])


def downgrade() -> None:
    """Drop documents and document_pages tables."""
    
    # Drop document_pages table
    op.drop_index('idx_document_pages_document_id', table_name='document_pages')
    op.drop_table('document_pages')
    
    # Drop documents table
    op.drop_index('idx_documents_checksum', table_name='documents')
    op.drop_index('idx_documents_uploaded_at', table_name='documents')
    op.drop_index('idx_documents_status', table_name='documents')
    op.drop_index('idx_documents_user_id', table_name='documents')
    op.drop_table('documents')
