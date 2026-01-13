# Change: Add Envelope Management

## Interface Definitions

**REST API Endpoints:** See [REST API Specification](../../specs/rest-api.md#envelope-management-endpoints)
- POST /envelopes
- GET /envelopes/:envelopeId
- PATCH /envelopes/:envelopeId
- POST /envelopes/:envelopeId/recipients
- PUT /envelopes/:envelopeId/signing-order
- POST /envelopes/:envelopeId/send
- POST /envelopes/:envelopeId/void
- POST /envelopes/:envelopeId/reminders
- GET /envelopes

**Database Schema:** See [Database Schema](../../specs/database-schema.md)
- Table: `envelopes`
- Table: `envelope_documents`
- Table: `recipients`
- View: `envelope_summary`
- View: `recipient_progress`

**Data Models:** See [Data Models](../../specs/data-models.md#envelope-models)
- Type: `Envelope`
- Type: `EnvelopeSummary`
- Type: `Recipient`
- Type: `RecipientProgress`
- Enum: `EnvelopeStatus`
- Enum: `SigningOrder`
- Enum: `RecipientRole`
- Enum: `RecipientStatus`

**Internal APIs:** See [Service Interfaces](../../specs/service-interfaces.md#envelope-service-internal-apis)
- POST /internal/envelopes/validate-access
- POST /internal/envelopes/update-recipient-status
- POST /internal/envelopes/check-completion
- GET /internal/envelopes/:envelopeId/recipients

**Events Published:** See [Event Bus](../../specs/event-bus.md#envelope-events)
- `envelope.created`
- `envelope.sent`
- `envelope.viewed`
- `envelope.recipient.signed`
- `envelope.completed`
- `envelope.declined`
- `envelope.voided`
- `envelope.expired`
- `envelope.reminder.sent`

--- System

## Why
Envelopes are the core workflow containers that group documents, recipients, and signature fields together. Users need to create envelopes to send documents for signing, track who needs to sign, manage signing order (sequential or parallel), and monitor completion status. This is the central orchestration system for the entire signing workflow.

## What Changes
- Envelope creation with one or more documents
- Recipient/signee management (name, email, role, signing order)
- Envelope status tracking (draft, sent, delivered, signed, completed, voided, expired)
- Sender information and envelope metadata
- Sequential and parallel signing workflows
- Envelope expiration dates
- Envelope templates for reuse
- Email reminders and tracking
- Envelope voiding and cancellation
- Envelope listing and search

## Impact
- Affected specs: `envelope-management` (new)
- Affected code:
  - New envelope API endpoints
  - Envelope database schema (envelopes, recipients tables)
  - Workflow state machine
  - Email notification triggers
  - Document-envelope relationships
- Dependencies: Document management, notification system
- Integration points: Email service, SMS service, signature fields, audit trail
