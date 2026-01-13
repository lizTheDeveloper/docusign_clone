# Database Schema Specification

**Version:** 1.0.0  
**Last Updated:** January 13, 2026  
**Purpose:** Complete database schema for PostgreSQL

## Overview

This document defines the complete relational database schema for the DocuSign Clone application using PostgreSQL 14+.

**Database:** PostgreSQL 14+  
**Extensions Required:**
- `uuid-ossp` - UUID generation
- `pgcrypto` - Cryptographic functions
- `pg_trgm` - Full-text search

---

## Schema: `public`

### Table: `users`
User accounts and authentication.

```sql
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    company VARCHAR(200),
    phone VARCHAR(20),
    role VARCHAR(20) NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin')),
    email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    account_locked BOOLEAN NOT NULL DEFAULT FALSE,
    locked_until TIMESTAMP WITH TIME ZONE,
    failed_login_attempts INTEGER NOT NULL DEFAULT 0,
    last_failed_login TIMESTAMP WITH TIME ZONE,
    last_login_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_created_at ON users(created_at);
```

---

### Table: `email_verifications`
Email verification tokens.

```sql
CREATE TABLE email_verifications (
    verification_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    token VARCHAR(64) NOT NULL UNIQUE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    verified_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_email_verifications_user_id ON email_verifications(user_id);
CREATE INDEX idx_email_verifications_token ON email_verifications(token);
```

---

### Table: `password_resets`
Password reset tokens.

```sql
CREATE TABLE password_resets (
    reset_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    token VARCHAR(64) NOT NULL UNIQUE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_password_resets_token ON password_resets(token);
CREATE INDEX idx_password_resets_expires_at ON password_resets(expires_at);
```

---

### Table: `refresh_tokens`
JWT refresh tokens.

```sql
CREATE TABLE refresh_tokens (
    token_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    token_hash VARCHAR(64) NOT NULL UNIQUE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    revoked_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_used_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_token_hash ON refresh_tokens(token_hash);
CREATE INDEX idx_refresh_tokens_expires_at ON refresh_tokens(expires_at);
```

---

### Table: `documents`
Uploaded documents.

```sql
CREATE TABLE documents (
    document_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    storage_key VARCHAR(500) NOT NULL,
    file_type VARCHAR(100) NOT NULL,
    file_size BIGINT NOT NULL,
    page_count INTEGER NOT NULL DEFAULT 0,
    checksum VARCHAR(64) NOT NULL,
    encryption_key_id VARCHAR(100),
    status VARCHAR(20) NOT NULL DEFAULT 'processing' CHECK (status IN ('processing', 'ready', 'failed')),
    error_message TEXT,
    thumbnail_storage_key VARCHAR(500),
    in_use_by_envelopes INTEGER NOT NULL DEFAULT 0,
    uploaded_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_uploaded_at ON documents(uploaded_at);
CREATE INDEX idx_documents_checksum ON documents(checksum);
```

---

### Table: `document_pages`
Individual document pages metadata.

```sql
CREATE TABLE document_pages (
    page_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    width FLOAT NOT NULL,
    height FLOAT NOT NULL,
    thumbnail_storage_key VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(document_id, page_number)
);

CREATE INDEX idx_document_pages_document_id ON document_pages(document_id);
```

---

### Table: `envelopes`
Signing envelopes.

```sql
CREATE TABLE envelopes (
    envelope_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sender_id UUID NOT NULL REFERENCES users(user_id),
    subject VARCHAR(200) NOT NULL,
    message TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'sent', 'delivered', 'signed', 'completed', 'declined', 'voided', 'expired')),
    signing_order VARCHAR(20) NOT NULL DEFAULT 'parallel' CHECK (signing_order IN ('parallel', 'sequential')),
    expiration_days INTEGER NOT NULL DEFAULT 30,
    expires_at TIMESTAMP WITH TIME ZONE,
    void_reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    sent_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    voided_at TIMESTAMP WITH TIME ZONE,
    expired_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_envelopes_sender_id ON envelopes(sender_id);
CREATE INDEX idx_envelopes_status ON envelopes(status);
CREATE INDEX idx_envelopes_created_at ON envelopes(created_at);
CREATE INDEX idx_envelopes_sent_at ON envelopes(sent_at);
CREATE INDEX idx_envelopes_expires_at ON envelopes(expires_at);
```

---

### Table: `envelope_documents`
Documents in envelopes.

```sql
CREATE TABLE envelope_documents (
    envelope_document_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    envelope_id UUID NOT NULL REFERENCES envelopes(envelope_id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES documents(document_id),
    display_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(envelope_id, document_id)
);

CREATE INDEX idx_envelope_documents_envelope_id ON envelope_documents(envelope_id);
CREATE INDEX idx_envelope_documents_document_id ON envelope_documents(document_id);
```

---

### Table: `recipients`
Envelope recipients.

```sql
CREATE TABLE recipients (
    recipient_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    envelope_id UUID NOT NULL REFERENCES envelopes(envelope_id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(user_id),
    name VARCHAR(200) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    role VARCHAR(20) NOT NULL CHECK (role IN ('signer', 'cc', 'approver')),
    signing_order INTEGER NOT NULL DEFAULT 1,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'viewed', 'signed', 'declined')),
    access_code VARCHAR(6) NOT NULL,
    access_code_hash VARCHAR(64) NOT NULL,
    decline_reason TEXT,
    sent_at TIMESTAMP WITH TIME ZONE,
    viewed_at TIMESTAMP WITH TIME ZONE,
    signed_at TIMESTAMP WITH TIME ZONE,
    declined_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_recipients_envelope_id ON recipients(envelope_id);
CREATE INDEX idx_recipients_email ON recipients(email);
CREATE INDEX idx_recipients_access_code_hash ON recipients(access_code_hash);
CREATE INDEX idx_recipients_status ON recipients(status);
```

---

### Table: `signature_fields`
Signature and form fields on documents.

```sql
CREATE TABLE signature_fields (
    field_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    envelope_id UUID NOT NULL REFERENCES envelopes(envelope_id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES documents(document_id),
    recipient_id UUID NOT NULL REFERENCES recipients(recipient_id),
    field_type VARCHAR(20) NOT NULL CHECK (field_type IN ('signature', 'initial', 'text', 'textarea', 'date', 'checkbox', 'radio', 'dropdown', 'email', 'company', 'title')),
    page_number INTEGER NOT NULL,
    x FLOAT NOT NULL,
    y FLOAT NOT NULL,
    width FLOAT NOT NULL,
    height FLOAT NOT NULL,
    required BOOLEAN NOT NULL DEFAULT TRUE,
    label VARCHAR(100),
    default_value TEXT,
    validation_pattern VARCHAR(500),
    tab_order INTEGER,
    options JSONB,
    completed BOOLEAN NOT NULL DEFAULT FALSE,
    value TEXT,
    signature_data_storage_key VARCHAR(500),
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_signature_fields_envelope_id ON signature_fields(envelope_id);
CREATE INDEX idx_signature_fields_recipient_id ON signature_fields(recipient_id);
CREATE INDEX idx_signature_fields_document_id ON signature_fields(document_id);
CREATE INDEX idx_signature_fields_completed ON signature_fields(completed);
```

---

### Table: `adopted_signatures`
Signatures saved for reuse.

```sql
CREATE TABLE adopted_signatures (
    adopted_signature_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    recipient_id UUID NOT NULL REFERENCES recipients(recipient_id) ON DELETE CASCADE,
    signature_type VARCHAR(20) NOT NULL CHECK (signature_type IN ('typed', 'drawn', 'uploaded')),
    signature_data_storage_key VARCHAR(500) NOT NULL,
    font VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_adopted_signatures_recipient_id ON adopted_signatures(recipient_id);
```

---

### Table: `signing_sessions`
Active signing sessions.

```sql
CREATE TABLE signing_sessions (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    envelope_id UUID NOT NULL REFERENCES envelopes(envelope_id),
    recipient_id UUID NOT NULL REFERENCES recipients(recipient_id),
    access_code_hash VARCHAR(64) NOT NULL,
    ip_address VARCHAR(45) NOT NULL,
    user_agent TEXT,
    device_fingerprint VARCHAR(64),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_activity_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_signing_sessions_envelope_id ON signing_sessions(envelope_id);
CREATE INDEX idx_signing_sessions_recipient_id ON signing_sessions(recipient_id);
CREATE INDEX idx_signing_sessions_expires_at ON signing_sessions(expires_at);
```

---

### Table: `audit_events`
Immutable audit trail.

```sql
CREATE TABLE audit_events (
    event_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    envelope_id UUID NOT NULL REFERENCES envelopes(envelope_id) ON DELETE RESTRICT,
    event_type VARCHAR(50) NOT NULL,
    actor_user_id UUID REFERENCES users(user_id),
    actor_recipient_id UUID REFERENCES recipients(recipient_id),
    actor_name VARCHAR(200),
    actor_email VARCHAR(255),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    geolocation JSONB,
    device_info JSONB,
    event_details JSONB,
    event_hash VARCHAR(64) NOT NULL,
    previous_event_hash VARCHAR(64),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_events_envelope_id ON audit_events(envelope_id);
CREATE INDEX idx_audit_events_timestamp ON audit_events(timestamp);
CREATE INDEX idx_audit_events_event_type ON audit_events(event_type);
CREATE INDEX idx_audit_events_actor_user_id ON audit_events(actor_user_id);
```

---

### Table: `certificates`
Certificates of completion.

```sql
CREATE TABLE certificates (
    certificate_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    envelope_id UUID NOT NULL REFERENCES envelopes(envelope_id) ON DELETE CASCADE UNIQUE,
    storage_key VARCHAR(500) NOT NULL,
    envelope_hash VARCHAR(64) NOT NULL,
    audit_trail_hash VARCHAR(64) NOT NULL,
    verification_code VARCHAR(20) NOT NULL UNIQUE,
    generated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_certificates_envelope_id ON certificates(envelope_id);
CREATE INDEX idx_certificates_verification_code ON certificates(verification_code);
```

---

### Table: `notifications`
Notification history.

```sql
CREATE TABLE notifications (
    notification_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    envelope_id UUID REFERENCES envelopes(envelope_id),
    recipient_id UUID REFERENCES recipients(recipient_id),
    user_id UUID REFERENCES users(user_id),
    notification_type VARCHAR(50) NOT NULL,
    channel VARCHAR(10) NOT NULL CHECK (channel IN ('email', 'sms')),
    recipient_address VARCHAR(255) NOT NULL,
    subject VARCHAR(200),
    message TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'queued' CHECK (status IN ('queued', 'sent', 'delivered', 'failed')),
    provider_message_id VARCHAR(100),
    failure_reason TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    failed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_notifications_envelope_id ON notifications(envelope_id);
CREATE INDEX idx_notifications_recipient_id ON notifications(recipient_id);
CREATE INDEX idx_notifications_status ON notifications(status);
CREATE INDEX idx_notifications_created_at ON notifications(created_at);
```

---

### Table: `notification_preferences`
User notification settings.

```sql
CREATE TABLE notification_preferences (
    preference_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE UNIQUE,
    email_envelope_sent BOOLEAN NOT NULL DEFAULT TRUE,
    email_envelope_received BOOLEAN NOT NULL DEFAULT TRUE,
    email_envelope_completed BOOLEAN NOT NULL DEFAULT TRUE,
    email_envelope_declined BOOLEAN NOT NULL DEFAULT TRUE,
    email_envelope_voided BOOLEAN NOT NULL DEFAULT TRUE,
    email_envelope_expired BOOLEAN NOT NULL DEFAULT TRUE,
    email_reminder_received BOOLEAN NOT NULL DEFAULT TRUE,
    sms_envelope_received BOOLEAN NOT NULL DEFAULT FALSE,
    sms_reminder_received BOOLEAN NOT NULL DEFAULT FALSE,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_notification_preferences_user_id ON notification_preferences(user_id);
```

---

### Table: `api_keys`
API keys for programmatic access.

```sql
CREATE TABLE api_keys (
    api_key_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    key_prefix VARCHAR(10) NOT NULL,
    key_hash VARCHAR(64) NOT NULL UNIQUE,
    scopes TEXT[] NOT NULL,
    last_used_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    revoked_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash);
```

---

### Table: `webhooks`
Webhook subscriptions.

```sql
CREATE TABLE webhooks (
    webhook_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    url VARCHAR(500) NOT NULL,
    events TEXT[] NOT NULL,
    secret VARCHAR(64) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    failure_count INTEGER NOT NULL DEFAULT 0,
    last_success_at TIMESTAMP WITH TIME ZONE,
    last_failure_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_webhooks_user_id ON webhooks(user_id);
CREATE INDEX idx_webhooks_active ON webhooks(active);
```

---

### Table: `webhook_deliveries`
Webhook delivery attempts.

```sql
CREATE TABLE webhook_deliveries (
    delivery_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    webhook_id UUID NOT NULL REFERENCES webhooks(webhook_id) ON DELETE CASCADE,
    envelope_id UUID REFERENCES envelopes(envelope_id),
    event_type VARCHAR(50) NOT NULL,
    payload JSONB NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'success', 'failed')),
    http_status_code INTEGER,
    response_body TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    delivered_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_webhook_deliveries_webhook_id ON webhook_deliveries(webhook_id);
CREATE INDEX idx_webhook_deliveries_status ON webhook_deliveries(status);
CREATE INDEX idx_webhook_deliveries_created_at ON webhook_deliveries(created_at);
```

---

### Table: `templates`
Reusable envelope templates.

```sql
CREATE TABLE templates (
    template_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    subject VARCHAR(200),
    message TEXT,
    signing_order VARCHAR(20) NOT NULL DEFAULT 'parallel',
    expiration_days INTEGER NOT NULL DEFAULT 30,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_templates_user_id ON templates(user_id);
```

---

### Table: `system_settings`
System-wide configuration.

```sql
CREATE TABLE system_settings (
    setting_key VARCHAR(100) PRIMARY KEY,
    setting_value JSONB NOT NULL,
    description TEXT,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_by UUID REFERENCES users(user_id)
);
```

---

### Table: `audit_log`
System audit log (admin actions).

```sql
CREATE TABLE audit_log (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(user_id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id UUID,
    changes JSONB,
    ip_address VARCHAR(45),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at);
CREATE INDEX idx_audit_log_action ON audit_log(action);
```

---

## Views

### View: `envelope_summary`
Quick envelope summary for listing.

```sql
CREATE VIEW envelope_summary AS
SELECT 
    e.envelope_id,
    e.subject,
    e.status,
    e.sender_id,
    u.first_name || ' ' || u.last_name AS sender_name,
    u.email AS sender_email,
    e.created_at,
    e.sent_at,
    e.completed_at,
    e.expires_at,
    COUNT(DISTINCT ed.document_id) AS document_count,
    COUNT(DISTINCT r.recipient_id) AS recipient_count,
    COUNT(DISTINCT CASE WHEN r.status = 'signed' THEN r.recipient_id END) AS signed_count
FROM envelopes e
JOIN users u ON e.sender_id = u.user_id
LEFT JOIN envelope_documents ed ON e.envelope_id = ed.envelope_id
LEFT JOIN recipients r ON e.envelope_id = r.envelope_id
GROUP BY e.envelope_id, u.first_name, u.last_name, u.email;
```

### View: `recipient_progress`
Recipient signing progress.

```sql
CREATE VIEW recipient_progress AS
SELECT 
    r.recipient_id,
    r.envelope_id,
    r.name,
    r.email,
    r.status,
    COUNT(sf.field_id) AS total_fields,
    COUNT(CASE WHEN sf.completed THEN 1 END) AS completed_fields,
    COUNT(CASE WHEN sf.required THEN 1 END) AS required_fields,
    COUNT(CASE WHEN sf.required AND sf.completed THEN 1 END) AS required_completed
FROM recipients r
LEFT JOIN signature_fields sf ON r.recipient_id = sf.recipient_id
GROUP BY r.recipient_id, r.envelope_id, r.name, r.email, r.status;
```

---

## Functions

### Function: `update_updated_at_column()`
Automatically update updated_at timestamp.

```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

**Apply to tables:**
```sql
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_envelopes_updated_at BEFORE UPDATE ON envelopes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_recipients_updated_at BEFORE UPDATE ON recipients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_signature_fields_updated_at BEFORE UPDATE ON signature_fields
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

---

### Function: `check_envelope_completion()`
Automatically update envelope status to completed.

```sql
CREATE OR REPLACE FUNCTION check_envelope_completion()
RETURNS TRIGGER AS $$
DECLARE
    total_recipients INTEGER;
    signed_recipients INTEGER;
BEGIN
    SELECT COUNT(*), COUNT(CASE WHEN status = 'signed' THEN 1 END)
    INTO total_recipients, signed_recipients
    FROM recipients
    WHERE envelope_id = NEW.envelope_id AND role = 'signer';

    IF total_recipients > 0 AND total_recipients = signed_recipients THEN
        UPDATE envelopes
        SET status = 'completed', completed_at = NOW()
        WHERE envelope_id = NEW.envelope_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_check_envelope_completion
AFTER UPDATE OF status ON recipients
FOR EACH ROW
WHEN (NEW.status = 'signed')
EXECUTE FUNCTION check_envelope_completion();
```

---

### Function: `mark_expired_envelopes()`
Periodic job to expire envelopes.

```sql
CREATE OR REPLACE FUNCTION mark_expired_envelopes()
RETURNS INTEGER AS $$
DECLARE
    expired_count INTEGER;
BEGIN
    UPDATE envelopes
    SET status = 'expired', expired_at = NOW()
    WHERE status IN ('sent', 'delivered', 'signed')
    AND expires_at < NOW();

    GET DIAGNOSTICS expired_count = ROW_COUNT;
    RETURN expired_count;
END;
$$ LANGUAGE plpgsql;
```

---

## Indexes for Performance

Additional composite indexes:

```sql
-- Envelope queries by sender and status
CREATE INDEX idx_envelopes_sender_status ON envelopes(sender_id, status);

-- Recipient queries by envelope and status
CREATE INDEX idx_recipients_envelope_status ON recipients(envelope_id, status);

-- Field queries by envelope and recipient
CREATE INDEX idx_signature_fields_envelope_recipient ON signature_fields(envelope_id, recipient_id);

-- Audit queries by envelope and timestamp
CREATE INDEX idx_audit_events_envelope_timestamp ON audit_events(envelope_id, timestamp DESC);

-- Document search
CREATE INDEX idx_documents_name_trgm ON documents USING gin(name gin_trgm_ops);

-- Envelope search
CREATE INDEX idx_envelopes_subject_trgm ON envelopes USING gin(subject gin_trgm_ops);
```

---

## Partitioning Strategy

For high-volume tables, consider partitioning:

### `audit_events` - Partition by month

```sql
CREATE TABLE audit_events_2026_01 PARTITION OF audit_events
FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

CREATE TABLE audit_events_2026_02 PARTITION OF audit_events
FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');

-- Continue monthly partitions...
```

### `notifications` - Partition by month

```sql
CREATE TABLE notifications_2026_01 PARTITION OF notifications
FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

-- Continue monthly partitions...
```

---

## Data Retention Policies

```sql
-- Delete old password reset tokens (> 7 days)
DELETE FROM password_resets WHERE expires_at < NOW() - INTERVAL '7 days';

-- Delete old email verifications (> 30 days)
DELETE FROM email_verifications WHERE expires_at < NOW() - INTERVAL '30 days';

-- Archive completed envelopes (> 7 years for legal compliance)
-- Move to archive table or external storage

-- Delete old notifications (> 90 days)
DELETE FROM notifications WHERE created_at < NOW() - INTERVAL '90 days';
```

---

## Backup Strategy

**Full Backup:** Daily at 2 AM UTC  
**Incremental Backup:** Every 6 hours  
**WAL Archiving:** Continuous (point-in-time recovery)  
**Retention:** 30 days for point-in-time, 1 year for monthly backups  

---

## Connection Pooling

**Tool:** PgBouncer  
**Pool Size:** 100 connections per service  
**Pool Mode:** Transaction (default)  
**Max Client Connections:** 1000  

---

**End of Database Schema Specification**
