# Change: Add Signing Workflow

## Interface Definitions

**REST API Endpoints:** See [REST API Specification](../../specs/rest-api.md#signing-workflow-endpoints)
- GET /signing/:accessCode
- GET /signing/:accessCode/fields
- POST /signing/:accessCode/fields/:fieldId/complete
- POST /signing/:accessCode/adopt-signature
- POST /signing/:accessCode/submit
- POST /signing/:accessCode/decline
- GET /signing/:accessCode/progress

**Database Schema:** See [Database Schema](../../specs/database-schema.md)
- Table: `signing_sessions`
- Table: `adopted_signatures`

**Data Models:** See [Data Models](../../specs/data-models.md#signing-workflow-models)
- Type: `SigningSession`
- Type: `CompleteFieldRequest`
- Type: `AdoptSignatureRequest`
- Type: `SigningProgress`
- Enum: `SignatureType`

**Internal APIs:** See [Service Interfaces](../../specs/service-interfaces.md#signing-service-internal-apis)
- POST /internal/signing/create-session
- POST /internal/signing/validate-session

**Events Published:** See [Event Bus](../../specs/event-bus.md#envelope-events)
- `envelope.viewed`
- `envelope.recipient.signed`
- `envelope.declined`

--- System

## Why
Recipients need to access envelopes, review documents, and complete signature fields. The signing workflow is the core user experience for document signers - it must be intuitive, secure, and compliant with legal standards for electronic signatures. This handles the entire signing session from email link click through signature completion.

## What Changes
- Secure signing session management with access codes
- Document viewer for reviewing documents before signing
- Field-by-field signing experience with guided workflow
- Signature capture (typed, drawn, uploaded image)
- Form field completion (text, date, checkbox, etc.)
- Field validation and required field enforcement
- Progress tracking during signing session
- Adoption signature (sign once, apply to all instances)
- Mobile-friendly signing experience
- Final review before submission
- Signing completion confirmation

## Impact
- Affected specs: `signing-workflow` (new)
- Affected code:
  - Signing session API endpoints
  - Signature capture UI components
  - Field completion logic
  - Access control and authentication for recipients
  - Signature storage and encryption
- Dependencies: Envelope management, signature fields, document management, notifications
- Security: Access code verification, session timeouts, signature encryption
