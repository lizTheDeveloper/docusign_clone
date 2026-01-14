"""add_envelope_tables

Revision ID: de3d8f01d54f
Revises: 002
Create Date: 2026-01-14 00:19:12.832062+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'de3d8f01d54f'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create envelopes, envelope_documents, and recipients tables."""
    
    # Create envelopes table
    op.create_table(
        'envelopes',
        sa.Column('envelope_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('sender_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('subject', sa.String(200), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('signing_order', sa.String(20), nullable=False, server_default='parallel'),
        sa.Column('expiration_days', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('void_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('voided_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expired_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['sender_id'], ['users.user_id']),
        sa.CheckConstraint(
            "status IN ('draft', 'sent', 'delivered', 'signed', 'completed', 'declined', 'voided', 'expired')",
            name='check_envelope_status'
        ),
        sa.CheckConstraint(
            "signing_order IN ('parallel', 'sequential')",
            name='check_signing_order'
        ),
    )
    
    # Create indexes for envelopes table
    op.create_index('idx_envelopes_sender_id', 'envelopes', ['sender_id'])
    op.create_index('idx_envelopes_status', 'envelopes', ['status'])
    op.create_index('idx_envelopes_created_at', 'envelopes', ['created_at'])
    op.create_index('idx_envelopes_sent_at', 'envelopes', ['sent_at'])
    op.create_index('idx_envelopes_expires_at', 'envelopes', ['expires_at'])
    
    # Create envelope_documents table
    op.create_table(
        'envelope_documents',
        sa.Column('envelope_document_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('envelope_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['envelope_id'], ['envelopes.envelope_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.document_id']),
        sa.UniqueConstraint('envelope_id', 'document_id', name='uq_envelope_document'),
    )
    
    # Create indexes for envelope_documents table
    op.create_index('idx_envelope_documents_envelope_id', 'envelope_documents', ['envelope_id'])
    op.create_index('idx_envelope_documents_document_id', 'envelope_documents', ['document_id'])
    
    # Create recipients table
    op.create_table(
        'recipients',
        sa.Column('recipient_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('envelope_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('signing_order', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('access_code', sa.String(6), nullable=False),
        sa.Column('access_code_hash', sa.String(64), nullable=False),
        sa.Column('decline_reason', sa.Text(), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('viewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('signed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('declined_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['envelope_id'], ['envelopes.envelope_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id']),
        sa.CheckConstraint(
            "role IN ('signer', 'cc', 'approver')",
            name='check_recipient_role'
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'sent', 'viewed', 'signed', 'declined')",
            name='check_recipient_status'
        ),
    )
    
    # Create indexes for recipients table
    op.create_index('idx_recipients_envelope_id', 'recipients', ['envelope_id'])
    op.create_index('idx_recipients_email', 'recipients', ['email'])
    op.create_index('idx_recipients_access_code_hash', 'recipients', ['access_code_hash'])
    op.create_index('idx_recipients_status', 'recipients', ['status'])


def downgrade() -> None:
    """Drop envelopes, envelope_documents, and recipients tables."""
    
    # Drop recipients table
    op.drop_index('idx_recipients_status', table_name='recipients')
    op.drop_index('idx_recipients_access_code_hash', table_name='recipients')
    op.drop_index('idx_recipients_email', table_name='recipients')
    op.drop_index('idx_recipients_envelope_id', table_name='recipients')
    op.drop_table('recipients')
    
    # Drop envelope_documents table
    op.drop_index('idx_envelope_documents_document_id', table_name='envelope_documents')
    op.drop_index('idx_envelope_documents_envelope_id', table_name='envelope_documents')
    op.drop_table('envelope_documents')
    
    # Drop envelopes table
    op.drop_index('idx_envelopes_expires_at', table_name='envelopes')
    op.drop_index('idx_envelopes_sent_at', table_name='envelopes')
    op.drop_index('idx_envelopes_created_at', table_name='envelopes')
    op.drop_index('idx_envelopes_status', table_name='envelopes')
    op.drop_index('idx_envelopes_sender_id', table_name='envelopes')
    op.drop_table('envelopes')

