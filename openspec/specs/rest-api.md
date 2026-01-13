# REST API Interface Specification

**Version:** 1.0.0  
**Last Updated:** January 13, 2026  
**Purpose:** Complete REST API contract for frontend-backend communication

## Overview

This document defines all HTTP endpoints, request/response schemas, and error handling for the DocuSign Clone REST API. Frontend developers can use this as the complete contract for building the UI, while backend developers implement these exact specifications.

**Base URL:** `https://api.docusign-clone.com/v1`  
**Authentication:** Bearer JWT token in `Authorization` header  
**Content-Type:** `application/json`  
**Rate Limiting:** 100 requests/minute per user, 1000/minute per IP

---

## Authentication Endpoints

### POST /auth/register
Register a new user account.

**Request Body:**
```json
{
  "email": "string (email format, required)",
  "password": "string (min 12 chars, required)",
  "firstName": "string (required)",
  "lastName": "string (required)",
  "company": "string (optional)",
  "phone": "string (E.164 format, optional)"
}
```

**Response 201 Created:**
```json
{
  "userId": "uuid",
  "email": "string",
  "firstName": "string",
  "lastName": "string",
  "emailVerified": false,
  "createdAt": "ISO8601 timestamp"
}
```

**Errors:**
- `400` - Validation error (weak password, invalid email)
- `409` - Email already registered
- `429` - Rate limit exceeded

---

### POST /auth/verify-email
Verify email address with token from email link.

**Request Body:**
```json
{
  "token": "string (required)"
}
```

**Response 200 OK:**
```json
{
  "success": true,
  "message": "Email verified successfully"
}
```

**Errors:**
- `400` - Invalid or expired token
- `404` - Token not found

---

### POST /auth/resend-verification
Resend verification email.

**Request Body:**
```json
{
  "email": "string (required)"
}
```

**Response 200 OK:**
```json
{
  "success": true,
  "message": "Verification email sent"
}
```

**Errors:**
- `400` - Email already verified
- `404` - Email not found
- `429` - Too many requests

---

### POST /auth/login
Authenticate user and receive JWT tokens.

**Request Body:**
```json
{
  "email": "string (required)",
  "password": "string (required)"
}
```

**Response 200 OK:**
```json
{
  "accessToken": "string (JWT, expires 1h)",
  "refreshToken": "string (JWT, expires 30d)",
  "user": {
    "userId": "uuid",
    "email": "string",
    "firstName": "string",
    "lastName": "string",
    "emailVerified": true,
    "company": "string | null",
    "role": "user | admin"
  }
}
```

**Errors:**
- `401` - Invalid credentials
- `403` - Email not verified / Account locked
- `429` - Rate limit exceeded

---

### POST /auth/refresh
Refresh access token using refresh token.

**Request Body:**
```json
{
  "refreshToken": "string (required)"
}
```

**Response 200 OK:**
```json
{
  "accessToken": "string (JWT, expires 1h)"
}
```

**Errors:**
- `401` - Invalid or expired refresh token

---

### POST /auth/logout
Invalidate refresh token.

**Headers:** `Authorization: Bearer <accessToken>`

**Request Body:**
```json
{
  "refreshToken": "string (required)"
}
```

**Response 204 No Content**

---

### POST /auth/forgot-password
Request password reset email.

**Request Body:**
```json
{
  "email": "string (required)"
}
```

**Response 200 OK:**
```json
{
  "success": true,
  "message": "If email exists, reset link sent"
}
```

---

### POST /auth/reset-password
Reset password with token.

**Request Body:**
```json
{
  "token": "string (required)",
  "newPassword": "string (min 12 chars, required)"
}
```

**Response 200 OK:**
```json
{
  "success": true,
  "message": "Password reset successfully"
}
```

**Errors:**
- `400` - Invalid/expired token or weak password
- `404` - Token not found

---

## User Profile Endpoints

### GET /users/me
Get current user profile.

**Headers:** `Authorization: Bearer <token>`

**Response 200 OK:**
```json
{
  "userId": "uuid",
  "email": "string",
  "firstName": "string",
  "lastName": "string",
  "company": "string | null",
  "phone": "string | null",
  "emailVerified": true,
  "role": "user | admin",
  "createdAt": "ISO8601",
  "lastLoginAt": "ISO8601"
}
```

---

### PATCH /users/me
Update current user profile.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "firstName": "string (optional)",
  "lastName": "string (optional)",
  "company": "string (optional)",
  "phone": "string (optional)"
}
```

**Response 200 OK:**
```json
{
  "userId": "uuid",
  "email": "string",
  "firstName": "string",
  "lastName": "string",
  "company": "string | null",
  "phone": "string | null",
  "updatedAt": "ISO8601"
}
```

---

### POST /users/me/change-password
Change user password.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "currentPassword": "string (required)",
  "newPassword": "string (min 12 chars, required)"
}
```

**Response 200 OK:**
```json
{
  "success": true,
  "message": "Password changed successfully"
}
```

**Errors:**
- `401` - Current password incorrect
- `400` - New password too weak

---

## Document Management Endpoints

### POST /documents
Upload a document.

**Headers:** 
- `Authorization: Bearer <token>`
- `Content-Type: multipart/form-data`

**Request Body (multipart):**
```
file: File (PDF, DOCX, XLSX - max 50MB)
name: string (optional, defaults to filename)
```

**Response 201 Created:**
```json
{
  "documentId": "uuid",
  "name": "string",
  "originalFilename": "string",
  "fileType": "application/pdf",
  "fileSize": 1234567,
  "pageCount": 10,
  "uploadedAt": "ISO8601",
  "status": "processing | ready | failed",
  "thumbnailUrl": "string | null",
  "checksum": "string (SHA-256)"
}
```

**Errors:**
- `400` - Invalid file format or size exceeded
- `413` - File too large
- `422` - Virus detected or corrupted file

---

### GET /documents/:documentId
Get document metadata.

**Headers:** `Authorization: Bearer <token>`

**Response 200 OK:**
```json
{
  "documentId": "uuid",
  "name": "string",
  "originalFilename": "string",
  "fileType": "string",
  "fileSize": 123456,
  "pageCount": 10,
  "uploadedAt": "ISO8601",
  "uploadedBy": {
    "userId": "uuid",
    "name": "string"
  },
  "status": "ready",
  "thumbnailUrl": "string",
  "checksum": "string",
  "pages": [
    {
      "pageNumber": 1,
      "width": 612,
      "height": 792,
      "thumbnailUrl": "string"
    }
  ]
}
```

**Errors:**
- `404` - Document not found
- `403` - Not authorized to access document

---

### GET /documents/:documentId/download
Download document file.

**Headers:** `Authorization: Bearer <token>`

**Response 200 OK:**
```
Content-Type: application/pdf
Content-Disposition: attachment; filename="document.pdf"
[Binary PDF data]
```

**OR Response 302 Redirect:**
```
Location: https://storage.url/presigned-url?expires=3600
```

**Errors:**
- `404` - Document not found
- `403` - Not authorized

---

### GET /documents/:documentId/preview
Get document preview URL.

**Headers:** `Authorization: Bearer <token>`

**Response 200 OK:**
```json
{
  "previewUrl": "string (presigned URL, valid 1h)",
  "expiresAt": "ISO8601"
}
```

---

### DELETE /documents/:documentId
Delete a document (only if not in any envelope).

**Headers:** `Authorization: Bearer <token>`

**Response 204 No Content**

**Errors:**
- `409` - Document is in use by envelope
- `403` - Not authorized

---

### GET /documents
List user's documents.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `page` (int, default 1)
- `limit` (int, default 20, max 100)
- `sortBy` (uploadedAt | name, default uploadedAt)
- `sortOrder` (asc | desc, default desc)
- `search` (string, optional)

**Response 200 OK:**
```json
{
  "documents": [
    {
      "documentId": "uuid",
      "name": "string",
      "fileSize": 123456,
      "pageCount": 10,
      "uploadedAt": "ISO8601",
      "thumbnailUrl": "string"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "totalPages": 5,
    "totalItems": 95
  }
}
```

---

## Envelope Management Endpoints

### POST /envelopes
Create a new envelope (draft).

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "subject": "string (required, max 200 chars)",
  "message": "string (optional, max 2000 chars)",
  "documentIds": ["uuid"] (required, min 1),
  "expirationDays": 30 (optional, default 30, max 365)
}
```

**Response 201 Created:**
```json
{
  "envelopeId": "uuid",
  "subject": "string",
  "message": "string",
  "status": "draft",
  "createdAt": "ISO8601",
  "sender": {
    "userId": "uuid",
    "name": "string",
    "email": "string"
  },
  "documents": [
    {
      "documentId": "uuid",
      "name": "string",
      "pageCount": 10,
      "order": 0
    }
  ],
  "expiresAt": "ISO8601"
}
```

---

### GET /envelopes/:envelopeId
Get envelope details.

**Headers:** `Authorization: Bearer <token>`

**Response 200 OK:**
```json
{
  "envelopeId": "uuid",
  "subject": "string",
  "message": "string",
  "status": "draft | sent | delivered | signed | completed | declined | voided | expired",
  "createdAt": "ISO8601",
  "sentAt": "ISO8601 | null",
  "completedAt": "ISO8601 | null",
  "expiresAt": "ISO8601",
  "sender": {
    "userId": "uuid",
    "name": "string",
    "email": "string"
  },
  "documents": [
    {
      "documentId": "uuid",
      "name": "string",
      "pageCount": 10,
      "order": 0
    }
  ],
  "recipients": [
    {
      "recipientId": "uuid",
      "name": "string",
      "email": "string",
      "role": "signer | cc | approver",
      "signingOrder": 1,
      "status": "pending | sent | viewed | signed | declined",
      "sentAt": "ISO8601 | null",
      "viewedAt": "ISO8601 | null",
      "signedAt": "ISO8601 | null"
    }
  ],
  "signingOrder": "parallel | sequential"
}
```

**Errors:**
- `404` - Envelope not found
- `403` - Not authorized

---

### PATCH /envelopes/:envelopeId
Update envelope (draft only).

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "subject": "string (optional)",
  "message": "string (optional)",
  "expirationDays": 30 (optional)
}
```

**Response 200 OK:**
```json
{
  "envelopeId": "uuid",
  "subject": "string",
  "message": "string",
  "expiresAt": "ISO8601",
  "updatedAt": "ISO8601"
}
```

**Errors:**
- `409` - Envelope not in draft status

---

### POST /envelopes/:envelopeId/recipients
Add recipient to envelope.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "name": "string (required)",
  "email": "string (email format, required)",
  "role": "signer | cc | approver (required)",
  "phone": "string (E.164 format, optional)",
  "signingOrder": 1 (required for sequential, integer > 0)
}
```

**Response 201 Created:**
```json
{
  "recipientId": "uuid",
  "name": "string",
  "email": "string",
  "role": "signer",
  "signingOrder": 1,
  "status": "pending",
  "accessCode": "string (6 digits)",
  "createdAt": "ISO8601"
}
```

**Errors:**
- `409` - Email already added / Envelope not in draft
- `400` - Invalid email or signing order

---

### PATCH /envelopes/:envelopeId/recipients/:recipientId
Update recipient (draft only).

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "name": "string (optional)",
  "email": "string (optional)",
  "signingOrder": 1 (optional)
}
```

**Response 200 OK:**
```json
{
  "recipientId": "uuid",
  "name": "string",
  "email": "string",
  "role": "signer",
  "signingOrder": 1,
  "updatedAt": "ISO8601"
}
```

---

### DELETE /envelopes/:envelopeId/recipients/:recipientId
Remove recipient (draft only).

**Headers:** `Authorization: Bearer <token>`

**Response 204 No Content**

---

### PUT /envelopes/:envelopeId/signing-order
Set signing order for envelope.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "type": "parallel | sequential (required)"
}
```

**Response 200 OK:**
```json
{
  "envelopeId": "uuid",
  "signingOrder": "parallel",
  "updatedAt": "ISO8601"
}
```

---

### POST /envelopes/:envelopeId/send
Send envelope to recipients.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{}
```

**Response 200 OK:**
```json
{
  "envelopeId": "uuid",
  "status": "sent",
  "sentAt": "ISO8601",
  "recipientsSent": 3
}
```

**Errors:**
- `400` - Validation error (no recipients, no fields, etc.)
- `409` - Envelope already sent

---

### POST /envelopes/:envelopeId/void
Void/cancel an envelope.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "reason": "string (required, max 500 chars)"
}
```

**Response 200 OK:**
```json
{
  "envelopeId": "uuid",
  "status": "voided",
  "voidedAt": "ISO8601",
  "voidReason": "string"
}
```

**Errors:**
- `409` - Envelope already completed or voided

---

### DELETE /envelopes/:envelopeId
Delete draft envelope.

**Headers:** `Authorization: Bearer <token>`

**Response 204 No Content**

**Errors:**
- `409` - Envelope not in draft status

---

### GET /envelopes
List user's envelopes.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `page` (int, default 1)
- `limit` (int, default 20, max 100)
- `status` (draft | sent | completed | all, default all)
- `role` (sender | recipient | all, default all)
- `sortBy` (createdAt | sentAt | completedAt, default createdAt)
- `sortOrder` (asc | desc, default desc)
- `search` (string, optional - searches subject)

**Response 200 OK:**
```json
{
  "envelopes": [
    {
      "envelopeId": "uuid",
      "subject": "string",
      "status": "sent",
      "createdAt": "ISO8601",
      "sentAt": "ISO8601",
      "sender": {
        "name": "string"
      },
      "documentCount": 2,
      "recipientCount": 3,
      "completedCount": 1
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "totalPages": 5,
    "totalItems": 95
  }
}
```

---

### POST /envelopes/:envelopeId/reminders
Send reminder to pending recipients.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "recipientIds": ["uuid"] (optional, sends to all if omitted)
}
```

**Response 200 OK:**
```json
{
  "remindersSent": 2,
  "recipients": ["uuid"]
}
```

---

### GET /envelopes/:envelopeId/download-completed
Download completed envelope with all signatures.

**Headers:** `Authorization: Bearer <token>`

**Response 200 OK:**
```
Content-Type: application/pdf
Content-Disposition: attachment; filename="envelope-completed.pdf"
[Binary PDF with signatures]
```

**Errors:**
- `409` - Envelope not completed

---

## Signature Field Editor Endpoints

### POST /envelopes/:envelopeId/fields
Add signature field to envelope document.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "documentId": "uuid (required)",
  "recipientId": "uuid (required)",
  "type": "signature | initial | text | date | checkbox | radio | dropdown (required)",
  "pageNumber": 1 (required, integer >= 1),
  "x": 100.5 (required, float - pixels from left),
  "y": 200.75 (required, float - pixels from top),
  "width": 150.0 (required, float),
  "height": 50.0 (required, float),
  "required": true (optional, default true),
  "label": "string (optional)",
  "defaultValue": "string (optional)",
  "validationPattern": "string (optional, regex)",
  "tabOrder": 1 (optional, integer),
  "options": ["Option 1", "Option 2"] (for dropdown/radio, optional)
}
```

**Response 201 Created:**
```json
{
  "fieldId": "uuid",
  "documentId": "uuid",
  "recipientId": "uuid",
  "type": "signature",
  "pageNumber": 1,
  "x": 100.5,
  "y": 200.75,
  "width": 150.0,
  "height": 50.0,
  "required": true,
  "label": "string | null",
  "tabOrder": 1,
  "createdAt": "ISO8601"
}
```

**Errors:**
- `400` - Invalid coordinates or field type
- `409` - Envelope not in draft status

---

### PATCH /envelopes/:envelopeId/fields/:fieldId
Update signature field.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "x": 100.5 (optional),
  "y": 200.75 (optional),
  "width": 150.0 (optional),
  "height": 50.0 (optional),
  "required": true (optional),
  "label": "string (optional)",
  "tabOrder": 1 (optional)
}
```

**Response 200 OK:**
```json
{
  "fieldId": "uuid",
  "x": 100.5,
  "y": 200.75,
  "width": 150.0,
  "height": 50.0,
  "updatedAt": "ISO8601"
}
```

---

### DELETE /envelopes/:envelopeId/fields/:fieldId
Delete signature field.

**Headers:** `Authorization: Bearer <token>`

**Response 204 No Content**

---

### GET /envelopes/:envelopeId/fields
List all fields in envelope.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `documentId` (uuid, optional - filter by document)
- `recipientId` (uuid, optional - filter by recipient)

**Response 200 OK:**
```json
{
  "fields": [
    {
      "fieldId": "uuid",
      "documentId": "uuid",
      "recipientId": "uuid",
      "recipientName": "string",
      "type": "signature",
      "pageNumber": 1,
      "x": 100.5,
      "y": 200.75,
      "width": 150.0,
      "height": 50.0,
      "required": true,
      "label": "Sign Here",
      "tabOrder": 1,
      "completed": false
    }
  ]
}
```

---

### POST /envelopes/:envelopeId/fields/bulk
Add multiple fields at once.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "fields": [
    {
      "documentId": "uuid",
      "recipientId": "uuid",
      "type": "signature",
      "pageNumber": 1,
      "x": 100,
      "y": 200,
      "width": 150,
      "height": 50
    }
  ]
}
```

**Response 201 Created:**
```json
{
  "fieldsCreated": 5,
  "fields": [
    {
      "fieldId": "uuid",
      "documentId": "uuid",
      "type": "signature"
    }
  ]
}
```

---

## Signing Workflow Endpoints

### GET /signing/:accessCode
Access signing session with unique access code.

**No authentication required** (access code provides authentication)

**Response 200 OK:**
```json
{
  "sessionId": "uuid",
  "envelopeId": "uuid",
  "recipientId": "uuid",
  "subject": "string",
  "message": "string",
  "sender": {
    "name": "string",
    "email": "string"
  },
  "recipient": {
    "name": "string",
    "email": "string",
    "role": "signer"
  },
  "documents": [
    {
      "documentId": "uuid",
      "name": "string",
      "pageCount": 10,
      "previewUrl": "string"
    }
  ],
  "canSign": true,
  "status": "pending | ready | waiting",
  "waitingMessage": "string | null",
  "expiresAt": "ISO8601"
}
```

**Errors:**
- `401` - Invalid or expired access code
- `404` - Signing session not found
- `410` - Envelope completed/voided/expired

---

### GET /signing/:accessCode/fields
Get fields for current recipient.

**No authentication required**

**Response 200 OK:**
```json
{
  "fields": [
    {
      "fieldId": "uuid",
      "documentId": "uuid",
      "type": "signature",
      "pageNumber": 1,
      "x": 100,
      "y": 200,
      "width": 150,
      "height": 50,
      "required": true,
      "label": "Sign Here",
      "tabOrder": 1,
      "completed": false,
      "value": null
    }
  ],
  "totalFields": 5,
  "completedFields": 0,
  "requiredFields": 3
}
```

---

### POST /signing/:accessCode/fields/:fieldId/complete
Complete a signature or form field.

**No authentication required**

**Request Body (for signature/initial fields):**
```json
{
  "signatureType": "typed | drawn | uploaded (required)",
  "signatureData": "string (base64 PNG for drawn/uploaded, text for typed)",
  "font": "string (optional, for typed signatures)"
}
```

**Request Body (for text/date fields):**
```json
{
  "value": "string (required)"
}
```

**Request Body (for checkbox):**
```json
{
  "checked": true
}
```

**Response 200 OK:**
```json
{
  "fieldId": "uuid",
  "completed": true,
  "completedAt": "ISO8601",
  "value": "string | null"
}
```

**Errors:**
- `400` - Invalid signature data or value
- `409` - Field already completed

---

### POST /signing/:accessCode/adopt-signature
Save signature for reuse across multiple fields.

**No authentication required**

**Request Body:**
```json
{
  "signatureType": "typed | drawn | uploaded",
  "signatureData": "string (base64 PNG or text)",
  "font": "string (optional)"
}
```

**Response 200 OK:**
```json
{
  "adoptedSignatureId": "uuid",
  "previewUrl": "string"
}
```

---

### POST /signing/:accessCode/submit
Submit completed signing.

**No authentication required**

**Request Body:**
```json
{
  "certify": true (required - user confirms identity and intent)
}
```

**Response 200 OK:**
```json
{
  "envelopeId": "uuid",
  "recipientId": "uuid",
  "completedAt": "ISO8601",
  "status": "signed",
  "certificateUrl": "string (presigned URL for certificate)"
}
```

**Errors:**
- `400` - Required fields not completed
- `409` - Already submitted

---

### POST /signing/:accessCode/decline
Decline to sign envelope.

**No authentication required**

**Request Body:**
```json
{
  "reason": "string (required, max 500 chars)"
}
```

**Response 200 OK:**
```json
{
  "envelopeId": "uuid",
  "recipientId": "uuid",
  "declinedAt": "ISO8601",
  "reason": "string"
}
```

---

### GET /signing/:accessCode/progress
Get signing progress.

**No authentication required**

**Response 200 OK:**
```json
{
  "totalFields": 10,
  "completedFields": 5,
  "requiredFields": 8,
  "requiredCompleted": 3,
  "percentComplete": 50,
  "canSubmit": false,
  "nextField": {
    "fieldId": "uuid",
    "documentId": "uuid",
    "pageNumber": 2,
    "type": "signature"
  }
}
```

---

## Audit Trail Endpoints

### GET /envelopes/:envelopeId/audit-trail
Get audit trail for envelope.

**Headers:** `Authorization: Bearer <token>`

**Response 200 OK:**
```json
{
  "envelopeId": "uuid",
  "events": [
    {
      "eventId": "uuid",
      "eventType": "envelope_sent | document_viewed | signature_completed | envelope_completed",
      "timestamp": "ISO8601",
      "actor": {
        "userId": "uuid | null",
        "name": "string",
        "email": "string"
      },
      "ipAddress": "string",
      "userAgent": "string",
      "geolocation": {
        "country": "string",
        "region": "string",
        "city": "string"
      },
      "details": {
        "fieldId": "uuid",
        "documentId": "uuid",
        "pageNumber": 1
      },
      "eventHash": "string (SHA-256)",
      "previousHash": "string | null"
    }
  ],
  "hashChainValid": true
}
```

---

### GET /envelopes/:envelopeId/audit-trail/export
Export audit trail as PDF/CSV/JSON.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `format` (pdf | csv | json, default pdf)

**Response 200 OK:**
```
Content-Type: application/pdf | text/csv | application/json
Content-Disposition: attachment; filename="audit-trail.pdf"
[File data]
```

---

### GET /envelopes/:envelopeId/certificate
Get certificate of completion.

**Headers:** `Authorization: Bearer <token>`

**Response 200 OK:**
```
Content-Type: application/pdf
Content-Disposition: attachment; filename="certificate.pdf"
[Certificate PDF with signatures, audit trail, cryptographic proof]
```

**Errors:**
- `409` - Envelope not completed

---

## Notification Preferences Endpoints

### GET /users/me/notification-preferences
Get user's notification preferences.

**Headers:** `Authorization: Bearer <token>`

**Response 200 OK:**
```json
{
  "emailNotifications": {
    "envelopeSent": true,
    "envelopeReceived": true,
    "envelopeCompleted": true,
    "envelopeDeclined": true,
    "envelopeVoided": true,
    "envelopeExpired": true,
    "reminderReceived": true
  },
  "smsNotifications": {
    "envelopeReceived": false,
    "reminderReceived": false
  }
}
```

---

### PATCH /users/me/notification-preferences
Update notification preferences.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "emailNotifications": {
    "envelopeSent": true,
    "envelopeReceived": true
  },
  "smsNotifications": {
    "envelopeReceived": false
  }
}
```

**Response 200 OK:**
```json
{
  "emailNotifications": { ... },
  "smsNotifications": { ... },
  "updatedAt": "ISO8601"
}
```

---

## Admin Endpoints

### GET /admin/users
List all users (admin only).

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `page`, `limit`, `search`

**Response 200 OK:**
```json
{
  "users": [
    {
      "userId": "uuid",
      "email": "string",
      "name": "string",
      "role": "user | admin",
      "emailVerified": true,
      "createdAt": "ISO8601",
      "lastLoginAt": "ISO8601"
    }
  ],
  "pagination": { ... }
}
```

---

### GET /admin/stats
Get platform statistics (admin only).

**Headers:** `Authorization: Bearer <token>`

**Response 200 OK:**
```json
{
  "totalUsers": 1234,
  "totalEnvelopes": 5678,
  "completedEnvelopes": 4500,
  "totalDocuments": 9012,
  "storageUsedGB": 123.45,
  "last30Days": {
    "newUsers": 45,
    "envelopesSent": 234,
    "envelopesCompleted": 189
  }
}
```

---

## WebSocket Events (Real-time Updates)

**Connection:** `wss://api.docusign-clone.com/ws?token=<jwt>`

### Client → Server Events

```json
{
  "type": "subscribe",
  "channels": ["envelope:<envelopeId>", "user:<userId>"]
}
```

### Server → Client Events

**Envelope Status Update:**
```json
{
  "type": "envelope.status.changed",
  "envelopeId": "uuid",
  "status": "signed",
  "timestamp": "ISO8601"
}
```

**Recipient Signed:**
```json
{
  "type": "envelope.recipient.signed",
  "envelopeId": "uuid",
  "recipientId": "uuid",
  "recipientName": "string",
  "timestamp": "ISO8601"
}
```

**Envelope Completed:**
```json
{
  "type": "envelope.completed",
  "envelopeId": "uuid",
  "timestamp": "ISO8601"
}
```

---

## Error Response Format

All error responses follow this structure:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field": "email",
      "reason": "Invalid format"
    },
    "timestamp": "ISO8601",
    "requestId": "uuid"
  }
}
```

### Common Error Codes

- `VALIDATION_ERROR` - Request validation failed
- `AUTHENTICATION_REQUIRED` - Missing or invalid auth token
- `PERMISSION_DENIED` - User lacks required permissions
- `RESOURCE_NOT_FOUND` - Requested resource doesn't exist
- `RESOURCE_CONFLICT` - Operation conflicts with current state
- `RATE_LIMIT_EXCEEDED` - Too many requests
- `INTERNAL_ERROR` - Server error

---

## Pagination

All list endpoints support pagination with this format:

**Query Parameters:**
- `page` (integer, default 1)
- `limit` (integer, default 20, max 100)

**Response:**
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "totalPages": 10,
    "totalItems": 195,
    "hasNextPage": true,
    "hasPreviousPage": false
  }
}
```

---

## Rate Limiting

**Headers included in all responses:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1704067200
```

When rate limit exceeded:
```
HTTP 429 Too Many Requests
Retry-After: 60
```

---

## CORS Policy

**Allowed Origins:** Configured domains only  
**Allowed Methods:** GET, POST, PUT, PATCH, DELETE, OPTIONS  
**Allowed Headers:** Authorization, Content-Type  
**Exposed Headers:** X-RateLimit-*, Location  
**Max Age:** 86400 seconds  
**Credentials:** true

---

**End of REST API Specification**
