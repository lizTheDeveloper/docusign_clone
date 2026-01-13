# Internal Service Interface Specification

**Version:** 1.0.0  
**Last Updated:** January 13, 2026  
**Purpose:** Internal service-to-service API contracts for microservices architecture

## Overview

This document defines internal APIs between services for the DocuSign Clone application. These interfaces enable loose coupling and allow services to be developed and deployed independently.

**Architecture Pattern:** Event-driven microservices with synchronous REST APIs for critical path operations

---

## Service Architecture

### Core Services

1. **Auth Service** - Authentication, authorization, user management
2. **Document Service** - Document storage, retrieval, processing
3. **Envelope Service** - Envelope lifecycle, recipient management
4. **Field Service** - Signature field placement and management
5. **Signing Service** - Signature capture and workflow execution
6. **Notification Service** - Email/SMS delivery
7. **Audit Service** - Audit logging and compliance
8. **Storage Service** - Object storage abstraction (S3/MinIO)

---

## Auth Service Internal APIs

### POST /internal/auth/validate-token
Validate JWT token (called by all services).

**Request Headers:**
```
X-Service-Token: <internal-service-secret>
```

**Request Body:**
```json
{
  "token": "string (JWT access token)"
}
```

**Response 200 OK:**
```json
{
  "valid": true,
  "userId": "uuid",
  "email": "string",
  "role": "user | admin",
  "permissions": ["read:envelopes", "write:envelopes"]
}
```

**Response 401 Unauthorized:**
```json
{
  "valid": false,
  "reason": "expired | invalid_signature | revoked"
}
```

---

### POST /internal/auth/create-access-code
Generate unique access code for signing (called by Envelope Service).

**Request Headers:**
```
X-Service-Token: <internal-service-secret>
```

**Request Body:**
```json
{
  "envelopeId": "uuid",
  "recipientId": "uuid",
  "recipientEmail": "string"
}
```

**Response 201 Created:**
```json
{
  "accessCode": "string (6 digits, cryptographically random)",
  "expiresAt": "ISO8601 (30 days from now)"
}
```

---

### POST /internal/auth/validate-access-code
Validate signing access code (called by Signing Service).

**Request Headers:**
```
X-Service-Token: <internal-service-secret>
```

**Request Body:**
```json
{
  "accessCode": "string",
  "envelopeId": "uuid",
  "recipientId": "uuid"
}
```

**Response 200 OK:**
```json
{
  "valid": true,
  "recipientId": "uuid",
  "envelopeId": "uuid"
}
```

---

### POST /internal/auth/revoke-access-codes
Revoke all access codes for envelope (called when voided/completed).

**Request Headers:**
```
X-Service-Token: <internal-service-secret>
```

**Request Body:**
```json
{
  "envelopeId": "uuid"
}
```

**Response 200 OK:**
```json
{
  "codesRevoked": 5
}
```

---

## Document Service Internal APIs

### POST /internal/documents/validate-ownership
Verify user owns documents (called by Envelope Service).

**Request Headers:**
```
X-Service-Token: <internal-service-secret>
```

**Request Body:**
```json
{
  "userId": "uuid",
  "documentIds": ["uuid"]
}
```

**Response 200 OK:**
```json
{
  "valid": true,
  "documents": [
    {
      "documentId": "uuid",
      "owned": true
    }
  ]
}
```

**Response 403 Forbidden:**
```json
{
  "valid": false,
  "unauthorizedDocuments": ["uuid"]
}
```

---

### POST /internal/documents/mark-in-use
Mark documents as in-use by envelope (prevent deletion).

**Request Headers:**
```
X-Service-Token: <internal-service-secret>
```

**Request Body:**
```json
{
  "documentIds": ["uuid"],
  "envelopeId": "uuid"
}
```

**Response 200 OK:**
```json
{
  "success": true,
  "documentsMarked": 3
}
```

---

### DELETE /internal/documents/release-usage
Release document usage lock when envelope completed/voided.

**Request Headers:**
```
X-Service-Token: <internal-service-secret>
```

**Request Body:**
```json
{
  "envelopeId": "uuid"
}
```

**Response 200 OK:**
```json
{
  "documentsReleased": 3
}
```

---

### POST /internal/documents/generate-preview-urls
Generate presigned URLs for signing session (called by Signing Service).

**Request Headers:**
```
X-Service-Token: <internal-service-secret>
```

**Request Body:**
```json
{
  "documentIds": ["uuid"],
  "expiresIn": 3600 (seconds)
}
```

**Response 200 OK:**
```json
{
  "urls": [
    {
      "documentId": "uuid",
      "url": "string (presigned URL)",
      "expiresAt": "ISO8601"
    }
  ]
}
```

---

### POST /internal/documents/get-metadata-batch
Get metadata for multiple documents.

**Request Headers:**
```
X-Service-Token: <internal-service-secret>
```

**Request Body:**
```json
{
  "documentIds": ["uuid"]
}
```

**Response 200 OK:**
```json
{
  "documents": [
    {
      "documentId": "uuid",
      "name": "string",
      "pageCount": 10,
      "fileSize": 123456,
      "checksum": "string"
    }
  ]
}
```

---

## Envelope Service Internal APIs

### POST /internal/envelopes/validate-access
Verify user can access envelope (called by other services).

**Request Headers:**
```
X-Service-Token: <internal-service-secret>
```

**Request Body:**
```json
{
  "envelopeId": "uuid",
  "userId": "uuid | null",
  "recipientId": "uuid | null"
}
```

**Response 200 OK:**
```json
{
  "canAccess": true,
  "role": "sender | recipient | admin",
  "envelope": {
    "envelopeId": "uuid",
    "status": "sent",
    "senderId": "uuid"
  }
}
```

---

### POST /internal/envelopes/update-recipient-status
Update recipient status (called by Signing Service).

**Request Headers:**
```
X-Service-Token: <internal-service-secret>
```

**Request Body:**
```json
{
  "envelopeId": "uuid",
  "recipientId": "uuid",
  "status": "viewed | signed | declined",
  "timestamp": "ISO8601",
  "metadata": {
    "ipAddress": "string",
    "userAgent": "string"
  }
}
```

**Response 200 OK:**
```json
{
  "success": true,
  "envelopeStatus": "signed | completed",
  "nextRecipient": {
    "recipientId": "uuid | null",
    "email": "string | null"
  }
}
```

---

### POST /internal/envelopes/check-completion
Check if all required recipients completed (called by Signing Service).

**Request Headers:**
```
X-Service-Token: <internal-service-secret>
```

**Request Body:**
```json
{
  "envelopeId": "uuid"
}
```

**Response 200 OK:**
```json
{
  "completed": true,
  "allRecipientsSigned": true,
  "completedAt": "ISO8601"
}
```

---

### GET /internal/envelopes/:envelopeId/recipients
Get all recipients for envelope (called by Notification Service).

**Request Headers:**
```
X-Service-Token: <internal-service-secret>
```

**Response 200 OK:**
```json
{
  "recipients": [
    {
      "recipientId": "uuid",
      "name": "string",
      "email": "string",
      "phone": "string | null",
      "role": "signer",
      "signingOrder": 1,
      "status": "pending",
      "accessCode": "string"
    }
  ]
}
```

---

## Field Service Internal APIs

### POST /internal/fields/validate-completion
Validate all required fields completed (called by Signing Service).

**Request Headers:**
```
X-Service-Token: <internal-service-secret>
```

**Request Body:**
```json
{
  "envelopeId": "uuid",
  "recipientId": "uuid"
}
```

**Response 200 OK:**
```json
{
  "valid": true,
  "totalFields": 10,
  "completedFields": 10,
  "requiredFields": 8,
  "requiredCompleted": 8,
  "incompleteRequired": []
}
```

**Response 400 Bad Request:**
```json
{
  "valid": false,
  "incompleteRequired": [
    {
      "fieldId": "uuid",
      "label": "Signature",
      "pageNumber": 1
    }
  ]
}
```

---

### GET /internal/fields/envelope/:envelopeId
Get all fields for envelope (called by signing workflow).

**Request Headers:**
```
X-Service-Token: <internal-service-secret>
```

**Query Parameters:**
- `recipientId` (optional)

**Response 200 OK:**
```json
{
  "fields": [
    {
      "fieldId": "uuid",
      "documentId": "uuid",
      "recipientId": "uuid",
      "type": "signature",
      "pageNumber": 1,
      "x": 100,
      "y": 200,
      "width": 150,
      "height": 50,
      "required": true,
      "tabOrder": 1
    }
  ]
}
```

---

### POST /internal/fields/bulk-complete
Mark multiple fields as completed (called by Signing Service).

**Request Headers:**
```
X-Service-Token: <internal-service-secret>
```

**Request Body:**
```json
{
  "completions": [
    {
      "fieldId": "uuid",
      "value": "string | base64",
      "completedAt": "ISO8601",
      "ipAddress": "string"
    }
  ]
}
```

**Response 200 OK:**
```json
{
  "fieldsCompleted": 5,
  "success": true
}
```

---

## Signing Service Internal APIs

### POST /internal/signing/create-session
Create signing session (called by Envelope Service when accessed).

**Request Headers:**
```
X-Service-Token: <internal-service-secret>
```

**Request Body:**
```json
{
  "envelopeId": "uuid",
  "recipientId": "uuid",
  "accessCode": "string",
  "ipAddress": "string",
  "userAgent": "string"
}
```

**Response 201 Created:**
```json
{
  "sessionId": "uuid",
  "expiresAt": "ISO8601 (30 min idle timeout)",
  "canSign": true,
  "waitingMessage": "string | null"
}
```

---

### POST /internal/signing/validate-session
Validate active signing session.

**Request Headers:**
```
X-Service-Token: <internal-service-secret>
```

**Request Body:**
```json
{
  "sessionId": "uuid"
}
```

**Response 200 OK:**
```json
{
  "valid": true,
  "recipientId": "uuid",
  "envelopeId": "uuid",
  "expiresAt": "ISO8601"
}
```

---

## Notification Service Internal APIs

### POST /internal/notifications/send-email
Send email notification (called by all services).

**Request Headers:**
```
X-Service-Token: <internal-service-secret>
```

**Request Body:**
```json
{
  "to": "string (email)",
  "subject": "string",
  "templateId": "envelope-sent | envelope-completed | reminder",
  "templateData": {
    "recipientName": "string",
    "senderName": "string",
    "envelopeSubject": "string",
    "signingUrl": "string"
  },
  "priority": "high | normal | low"
}
```

**Response 202 Accepted:**
```json
{
  "notificationId": "uuid",
  "status": "queued",
  "estimatedDelivery": "ISO8601"
}
```

---

### POST /internal/notifications/send-sms
Send SMS notification.

**Request Headers:**
```
X-Service-Token: <internal-service-secret>
```

**Request Body:**
```json
{
  "to": "string (E.164 phone)",
  "message": "string (max 160 chars)",
  "envelopeId": "uuid (for tracking)"
}
```

**Response 202 Accepted:**
```json
{
  "notificationId": "uuid",
  "status": "queued"
}
```

---

### POST /internal/notifications/send-batch
Send multiple notifications (envelope sent to all recipients).

**Request Headers:**
```
X-Service-Token: <internal-service-secret>
```

**Request Body:**
```json
{
  "notifications": [
    {
      "type": "email | sms",
      "to": "string",
      "templateId": "string",
      "templateData": {}
    }
  ]
}
```

**Response 202 Accepted:**
```json
{
  "queued": 10,
  "notificationIds": ["uuid"]
}
```

---

### GET /internal/notifications/:notificationId/status
Check notification delivery status.

**Request Headers:**
```
X-Service-Token: <internal-service-secret>
```

**Response 200 OK:**
```json
{
  "notificationId": "uuid",
  "status": "queued | sent | delivered | failed",
  "sentAt": "ISO8601 | null",
  "deliveredAt": "ISO8601 | null",
  "failureReason": "string | null",
  "retryCount": 0
}
```

---

## Audit Service Internal APIs

### POST /internal/audit/log-event
Log audit event (called by all services).

**Request Headers:**
```
X-Service-Token: <internal-service-secret>
```

**Request Body:**
```json
{
  "envelopeId": "uuid",
  "eventType": "envelope_sent | document_viewed | signature_completed | envelope_completed | envelope_declined | envelope_voided",
  "actorId": "uuid | null",
  "actorEmail": "string",
  "actorName": "string",
  "timestamp": "ISO8601",
  "ipAddress": "string",
  "userAgent": "string",
  "geolocation": {
    "country": "string",
    "region": "string",
    "city": "string",
    "latitude": 0.0,
    "longitude": 0.0
  },
  "deviceInfo": {
    "deviceType": "desktop | mobile | tablet",
    "os": "string",
    "browser": "string"
  },
  "eventDetails": {
    "recipientId": "uuid",
    "documentId": "uuid",
    "fieldId": "uuid",
    "pageNumber": 1,
    "customData": {}
  }
}
```

**Response 201 Created:**
```json
{
  "eventId": "uuid",
  "eventHash": "string (SHA-256)",
  "previousHash": "string | null",
  "createdAt": "ISO8601"
}
```

---

### POST /internal/audit/verify-hash-chain
Verify audit trail integrity.

**Request Headers:**
```
X-Service-Token: <internal-service-secret>
```

**Request Body:**
```json
{
  "envelopeId": "uuid"
}
```

**Response 200 OK:**
```json
{
  "valid": true,
  "eventCount": 25,
  "firstEventHash": "string",
  "lastEventHash": "string"
}
```

**Response 400 Bad Request:**
```json
{
  "valid": false,
  "tamperedEvents": ["uuid"],
  "reason": "Hash chain broken at event X"
}
```

---

### GET /internal/audit/events/:envelopeId
Get all audit events for envelope.

**Request Headers:**
```
X-Service-Token: <internal-service-secret>
```

**Response 200 OK:**
```json
{
  "envelopeId": "uuid",
  "events": [
    {
      "eventId": "uuid",
      "eventType": "string",
      "timestamp": "ISO8601",
      "actor": {
        "name": "string",
        "email": "string"
      },
      "ipAddress": "string",
      "eventHash": "string"
    }
  ]
}
```

---

### POST /internal/audit/generate-certificate
Generate certificate of completion PDF.

**Request Headers:**
```
X-Service-Token: <internal-service-secret>
```

**Request Body:**
```json
{
  "envelopeId": "uuid"
}
```

**Response 200 OK:**
```json
{
  "certificateUrl": "string (presigned URL)",
  "generatedAt": "ISO8601",
  "expiresAt": "ISO8601"
}
```

---

## Storage Service Internal APIs

### POST /internal/storage/upload
Upload file to object storage.

**Request Headers:**
```
X-Service-Token: <internal-service-secret>
Content-Type: multipart/form-data
```

**Request Body:**
```
file: binary
metadata: {
  "userId": "uuid",
  "documentId": "uuid",
  "contentType": "string"
}
```

**Response 201 Created:**
```json
{
  "storageKey": "string",
  "checksum": "string (SHA-256)",
  "size": 123456,
  "encryptionKeyId": "string"
}
```

---

### POST /internal/storage/generate-presigned-url
Generate presigned URL for download.

**Request Headers:**
```
X-Service-Token: <internal-service-secret>
```

**Request Body:**
```json
{
  "storageKey": "string",
  "expiresIn": 3600 (seconds),
  "contentDisposition": "inline | attachment",
  "filename": "string (optional)"
}
```

**Response 200 OK:**
```json
{
  "url": "string (presigned URL)",
  "expiresAt": "ISO8601"
}
```

---

### DELETE /internal/storage/delete
Delete file from storage.

**Request Headers:**
```
X-Service-Token: <internal-service-secret>
```

**Request Body:**
```json
{
  "storageKey": "string"
}
```

**Response 204 No Content**

---

### POST /internal/storage/copy
Copy file in storage (for versioning).

**Request Headers:**
```
X-Service-Token: <internal-service-secret>
```

**Request Body:**
```json
{
  "sourceKey": "string",
  "destinationKey": "string"
}
```

**Response 200 OK:**
```json
{
  "destinationKey": "string",
  "size": 123456,
  "checksum": "string"
}
```

---

## Service Authentication

All internal API calls MUST include service authentication:

**Header:**
```
X-Service-Token: <service-specific-secret>
```

**OR** use mutual TLS (mTLS) with service certificates.

### Service Tokens

Each service has a unique secret token stored in environment variables:

```
AUTH_SERVICE_TOKEN=<secret>
DOCUMENT_SERVICE_TOKEN=<secret>
ENVELOPE_SERVICE_TOKEN=<secret>
...
```

Tokens are rotated every 90 days.

---

## Service Discovery

Services discover each other via:

1. **Environment Variables** (simple deployments):
   ```
   AUTH_SERVICE_URL=http://auth-service:8001
   DOCUMENT_SERVICE_URL=http://document-service:8002
   ```

2. **Service Mesh** (Kubernetes):
   - Istio/Linkerd for service discovery
   - DNS: `auth-service.default.svc.cluster.local`

3. **Service Registry** (advanced):
   - Consul/Eureka for dynamic discovery

---

## Circuit Breaker Pattern

All service-to-service calls MUST implement circuit breaker:

**States:**
- **Closed**: Normal operation
- **Open**: Service unavailable (fail fast)
- **Half-Open**: Testing recovery

**Configuration:**
- Failure threshold: 5 consecutive failures
- Timeout: 30 seconds
- Half-open wait: 60 seconds

---

## Retry Policy

**Retryable errors:** 503, 504, network timeouts  
**Retry strategy:** Exponential backoff  
**Max retries:** 3  
**Initial delay:** 100ms  
**Max delay:** 5s  

**Non-retryable errors:** 400, 401, 403, 404, 409

---

## Timeouts

**Default timeout:** 30 seconds  
**Long operations (PDF generation, virus scan):** 120 seconds  
**Quick operations (token validation):** 5 seconds

---

## Health Checks

All services must expose:

### GET /health
Basic health check.

**Response 200 OK:**
```json
{
  "status": "healthy",
  "service": "auth-service",
  "version": "1.0.0",
  "timestamp": "ISO8601"
}
```

### GET /health/ready
Readiness check (includes dependencies).

**Response 200 OK:**
```json
{
  "status": "ready",
  "dependencies": {
    "database": "healthy",
    "redis": "healthy",
    "storage": "healthy"
  }
}
```

---

**End of Service Interface Specification**
