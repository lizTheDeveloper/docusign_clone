# Data Models & Type Definitions Specification

**Version:** 1.0.0  
**Last Updated:** January 13, 2026  
**Purpose:** Shared data models and type definitions for consistent data structures across services

## Overview

This document defines common data transfer objects (DTOs), enums, and types used across all services. Use these definitions to ensure consistency between frontend, backend, and services.

**Format:** TypeScript interfaces (can be translated to Python, Java, etc.)

---

## User Models

### Type: `User`
```typescript
interface User {
  userId: string;           // UUID
  email: string;
  firstName: string;
  lastName: string;
  company?: string;
  phone?: string;
  role: UserRole;
  emailVerified: boolean;
  createdAt: string;        // ISO 8601
  updatedAt: string;
  lastLoginAt?: string;
}
```

### Enum: `UserRole`
```typescript
enum UserRole {
  USER = 'user',
  ADMIN = 'admin'
}
```

### Type: `UserProfile`
```typescript
interface UserProfile {
  userId: string;
  email: string;
  firstName: string;
  lastName: string;
  fullName: string;          // Computed: firstName + lastName
  company?: string;
  phone?: string;
  avatar?: string;           // URL
  role: UserRole;
  emailVerified: boolean;
  createdAt: string;
  lastLoginAt?: string;
}
```

---

## Authentication Models

### Type: `LoginRequest`
```typescript
interface LoginRequest {
  email: string;
  password: string;
}
```

### Type: `LoginResponse`
```typescript
interface LoginResponse {
  accessToken: string;       // JWT, expires 1h
  refreshToken: string;      // JWT, expires 30d
  user: UserProfile;
}
```

### Type: `RegisterRequest`
```typescript
interface RegisterRequest {
  email: string;
  password: string;
  firstName: string;
  lastName: string;
  company?: string;
  phone?: string;
}
```

### Type: `JWTPayload`
```typescript
interface JWTPayload {
  sub: string;               // userId
  email: string;
  role: UserRole;
  permissions: string[];
  iat: number;               // Issued at (Unix timestamp)
  exp: number;               // Expires at (Unix timestamp)
}
```

---

## Document Models

### Type: `Document`
```typescript
interface Document {
  documentId: string;        // UUID
  userId: string;
  name: string;
  originalFilename: string;
  fileType: string;          // MIME type
  fileSize: number;          // Bytes
  pageCount: number;
  status: DocumentStatus;
  thumbnailUrl?: string;
  checksum: string;          // SHA-256
  uploadedAt: string;
  updatedAt: string;
}
```

### Enum: `DocumentStatus`
```typescript
enum DocumentStatus {
  PROCESSING = 'processing',
  READY = 'ready',
  FAILED = 'failed'
}
```

### Type: `DocumentPage`
```typescript
interface DocumentPage {
  pageNumber: number;        // 1-indexed
  width: number;             // Pixels
  height: number;            // Pixels
  thumbnailUrl?: string;
}
```

### Type: `DocumentUploadRequest`
```typescript
interface DocumentUploadRequest {
  file: File;                // Multipart file
  name?: string;             // Optional override
}
```

### Type: `DocumentMetadata`
```typescript
interface DocumentMetadata {
  documentId: string;
  name: string;
  fileType: string;
  fileSize: number;
  pageCount: number;
  pages: DocumentPage[];
  thumbnailUrl?: string;
  uploadedAt: string;
  uploadedBy: {
    userId: string;
    name: string;
  };
}
```

---

## Envelope Models

### Type: `Envelope`
```typescript
interface Envelope {
  envelopeId: string;
  subject: string;
  message?: string;
  status: EnvelopeStatus;
  signingOrder: SigningOrder;
  createdAt: string;
  sentAt?: string;
  completedAt?: string;
  expiresAt: string;
  sender: EnvelopeSender;
  documents: EnvelopeDocument[];
  recipients: Recipient[];
}
```

### Enum: `EnvelopeStatus`
```typescript
enum EnvelopeStatus {
  DRAFT = 'draft',
  SENT = 'sent',
  DELIVERED = 'delivered',
  SIGNED = 'signed',
  COMPLETED = 'completed',
  DECLINED = 'declined',
  VOIDED = 'voided',
  EXPIRED = 'expired'
}
```

### Enum: `SigningOrder`
```typescript
enum SigningOrder {
  PARALLEL = 'parallel',
  SEQUENTIAL = 'sequential'
}
```

### Type: `EnvelopeSender`
```typescript
interface EnvelopeSender {
  userId: string;
  name: string;
  email: string;
}
```

### Type: `EnvelopeDocument`
```typescript
interface EnvelopeDocument {
  documentId: string;
  name: string;
  pageCount: number;
  order: number;             // Display order in envelope
}
```

### Type: `CreateEnvelopeRequest`
```typescript
interface CreateEnvelopeRequest {
  subject: string;
  message?: string;
  documentIds: string[];     // At least 1
  expirationDays?: number;   // Default 30, max 365
}
```

### Type: `EnvelopeSummary`
```typescript
interface EnvelopeSummary {
  envelopeId: string;
  subject: string;
  status: EnvelopeStatus;
  createdAt: string;
  sentAt?: string;
  sender: {
    name: string;
  };
  documentCount: number;
  recipientCount: number;
  completedCount: number;
}
```

---

## Recipient Models

### Type: `Recipient`
```typescript
interface Recipient {
  recipientId: string;
  name: string;
  email: string;
  phone?: string;
  role: RecipientRole;
  signingOrder: number;
  status: RecipientStatus;
  accessCode?: string;       // Only included for sender
  sentAt?: string;
  viewedAt?: string;
  signedAt?: string;
  declinedAt?: string;
  declineReason?: string;
}
```

### Enum: `RecipientRole`
```typescript
enum RecipientRole {
  SIGNER = 'signer',
  CC = 'cc',
  APPROVER = 'approver'
}
```

### Enum: `RecipientStatus`
```typescript
enum RecipientStatus {
  PENDING = 'pending',
  SENT = 'sent',
  VIEWED = 'viewed',
  SIGNED = 'signed',
  DECLINED = 'declined'
}
```

### Type: `AddRecipientRequest`
```typescript
interface AddRecipientRequest {
  name: string;
  email: string;
  phone?: string;
  role: RecipientRole;
  signingOrder: number;      // Required for sequential
}
```

### Type: `RecipientProgress`
```typescript
interface RecipientProgress {
  recipientId: string;
  name: string;
  email: string;
  status: RecipientStatus;
  totalFields: number;
  completedFields: number;
  requiredFields: number;
  requiredCompleted: number;
  percentComplete: number;
}
```

---

## Signature Field Models

### Type: `SignatureField`
```typescript
interface SignatureField {
  fieldId: string;
  documentId: string;
  recipientId: string;
  recipientName?: string;    // Denormalized for convenience
  type: FieldType;
  pageNumber: number;        // 1-indexed
  x: number;                 // Pixels from left
  y: number;                 // Pixels from top
  width: number;             // Pixels
  height: number;            // Pixels
  required: boolean;
  label?: string;
  defaultValue?: string;
  validationPattern?: string;
  tabOrder?: number;
  options?: string[];        // For dropdown/radio
  completed: boolean;
  value?: string;
  completedAt?: string;
}
```

### Enum: `FieldType`
```typescript
enum FieldType {
  SIGNATURE = 'signature',
  INITIAL = 'initial',
  TEXT = 'text',
  TEXTAREA = 'textarea',
  DATE = 'date',
  CHECKBOX = 'checkbox',
  RADIO = 'radio',
  DROPDOWN = 'dropdown',
  EMAIL = 'email',
  COMPANY = 'company',
  TITLE = 'title'
}
```

### Type: `CreateFieldRequest`
```typescript
interface CreateFieldRequest {
  documentId: string;
  recipientId: string;
  type: FieldType;
  pageNumber: number;
  x: number;
  y: number;
  width: number;
  height: number;
  required?: boolean;        // Default true
  label?: string;
  defaultValue?: string;
  validationPattern?: string;
  tabOrder?: number;
  options?: string[];
}
```

### Type: `UpdateFieldRequest`
```typescript
interface UpdateFieldRequest {
  x?: number;
  y?: number;
  width?: number;
  height?: number;
  required?: boolean;
  label?: string;
  tabOrder?: number;
}
```

### Type: `FieldPosition`
```typescript
interface FieldPosition {
  pageNumber: number;
  x: number;
  y: number;
  width: number;
  height: number;
}
```

---

## Signing Workflow Models

### Type: `SigningSession`
```typescript
interface SigningSession {
  sessionId: string;
  envelopeId: string;
  recipientId: string;
  subject: string;
  message?: string;
  sender: EnvelopeSender;
  recipient: Recipient;
  documents: EnvelopeDocument[];
  canSign: boolean;
  waitingMessage?: string;   // For sequential signing
  status: RecipientStatus;
  expiresAt: string;
}
```

### Type: `CompleteFieldRequest`
```typescript
interface CompleteFieldRequest {
  // For signature/initial fields
  signatureType?: SignatureType;
  signatureData?: string;    // Base64 PNG or text
  font?: string;
  
  // For text/date fields
  value?: string;
  
  // For checkbox
  checked?: boolean;
}
```

### Enum: `SignatureType`
```typescript
enum SignatureType {
  TYPED = 'typed',
  DRAWN = 'drawn',
  UPLOADED = 'uploaded'
}
```

### Type: `AdoptSignatureRequest`
```typescript
interface AdoptSignatureRequest {
  signatureType: SignatureType;
  signatureData: string;
  font?: string;
}
```

### Type: `AdoptedSignature`
```typescript
interface AdoptedSignature {
  adoptedSignatureId: string;
  previewUrl: string;
}
```

### Type: `SubmitSigningRequest`
```typescript
interface SubmitSigningRequest {
  certify: boolean;          // User confirms identity and intent
}
```

### Type: `DeclineEnvelopeRequest`
```typescript
interface DeclineEnvelopeRequest {
  reason: string;
}
```

### Type: `SigningProgress`
```typescript
interface SigningProgress {
  totalFields: number;
  completedFields: number;
  requiredFields: number;
  requiredCompleted: number;
  percentComplete: number;
  canSubmit: boolean;
  nextField?: {
    fieldId: string;
    documentId: string;
    pageNumber: number;
    type: FieldType;
  };
}
```

---

## Audit Trail Models

### Type: `AuditEvent`
```typescript
interface AuditEvent {
  eventId: string;
  eventType: AuditEventType;
  timestamp: string;
  actor: AuditActor;
  ipAddress: string;
  userAgent: string;
  geolocation?: Geolocation;
  deviceInfo?: DeviceInfo;
  details: AuditEventDetails;
  eventHash: string;
  previousHash?: string;
}
```

### Enum: `AuditEventType`
```typescript
enum AuditEventType {
  ENVELOPE_CREATED = 'envelope_created',
  ENVELOPE_SENT = 'envelope_sent',
  ENVELOPE_VIEWED = 'envelope_viewed',
  DOCUMENT_VIEWED = 'document_viewed',
  SIGNATURE_COMPLETED = 'signature_completed',
  ENVELOPE_SIGNED = 'envelope_signed',
  ENVELOPE_COMPLETED = 'envelope_completed',
  ENVELOPE_DECLINED = 'envelope_declined',
  ENVELOPE_VOIDED = 'envelope_voided',
  ENVELOPE_EXPIRED = 'envelope_expired',
  ACCESS_GRANTED = 'access_granted',
  ACCESS_DENIED = 'access_denied'
}
```

### Type: `AuditActor`
```typescript
interface AuditActor {
  userId?: string;
  recipientId?: string;
  name: string;
  email: string;
}
```

### Type: `Geolocation`
```typescript
interface Geolocation {
  country: string;
  region?: string;
  city?: string;
  latitude?: number;
  longitude?: number;
}
```

### Type: `DeviceInfo`
```typescript
interface DeviceInfo {
  deviceType: 'desktop' | 'mobile' | 'tablet';
  os: string;
  browser: string;
  browserVersion?: string;
}
```

### Type: `AuditEventDetails`
```typescript
interface AuditEventDetails {
  recipientId?: string;
  documentId?: string;
  fieldId?: string;
  pageNumber?: number;
  [key: string]: any;        // Additional context
}
```

### Type: `AuditTrail`
```typescript
interface AuditTrail {
  envelopeId: string;
  events: AuditEvent[];
  hashChainValid: boolean;
}
```

### Type: `Certificate`
```typescript
interface Certificate {
  certificateId: string;
  envelopeId: string;
  envelopeHash: string;
  auditTrailHash: string;
  verificationCode: string;
  downloadUrl: string;
  generatedAt: string;
}
```

---

## Notification Models

### Type: `NotificationPreferences`
```typescript
interface NotificationPreferences {
  emailNotifications: EmailNotificationSettings;
  smsNotifications: SmsNotificationSettings;
}
```

### Type: `EmailNotificationSettings`
```typescript
interface EmailNotificationSettings {
  envelopeSent: boolean;
  envelopeReceived: boolean;
  envelopeCompleted: boolean;
  envelopeDeclined: boolean;
  envelopeVoided: boolean;
  envelopeExpired: boolean;
  reminderReceived: boolean;
}
```

### Type: `SmsNotificationSettings`
```typescript
interface SmsNotificationSettings {
  envelopeReceived: boolean;
  reminderReceived: boolean;
}
```

### Type: `Notification`
```typescript
interface Notification {
  notificationId: string;
  type: NotificationType;
  channel: NotificationChannel;
  status: NotificationStatus;
  recipientAddress: string;
  subject?: string;
  createdAt: string;
  sentAt?: string;
  deliveredAt?: string;
}
```

### Enum: `NotificationType`
```typescript
enum NotificationType {
  ENVELOPE_SENT = 'envelope_sent',
  ENVELOPE_RECEIVED = 'envelope_received',
  ENVELOPE_COMPLETED = 'envelope_completed',
  ENVELOPE_DECLINED = 'envelope_declined',
  ENVELOPE_VOIDED = 'envelope_voided',
  ENVELOPE_EXPIRED = 'envelope_expired',
  REMINDER = 'reminder',
  NEXT_SIGNER = 'next_signer'
}
```

### Enum: `NotificationChannel`
```typescript
enum NotificationChannel {
  EMAIL = 'email',
  SMS = 'sms'
}
```

### Enum: `NotificationStatus`
```typescript
enum NotificationStatus {
  QUEUED = 'queued',
  SENT = 'sent',
  DELIVERED = 'delivered',
  FAILED = 'failed'
}
```

---

## Pagination Models

### Type: `PaginatedRequest`
```typescript
interface PaginatedRequest {
  page?: number;             // Default 1
  limit?: number;            // Default 20, max 100
  sortBy?: string;
  sortOrder?: 'asc' | 'desc'; // Default desc
  search?: string;
}
```

### Type: `PaginatedResponse<T>`
```typescript
interface PaginatedResponse<T> {
  data: T[];
  pagination: Pagination;
}
```

### Type: `Pagination`
```typescript
interface Pagination {
  page: number;
  limit: number;
  totalPages: number;
  totalItems: number;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
}
```

---

## Error Models

### Type: `ErrorResponse`
```typescript
interface ErrorResponse {
  error: {
    code: ErrorCode;
    message: string;
    details?: Record<string, any>;
    timestamp: string;
    requestId: string;
  };
}
```

### Enum: `ErrorCode`
```typescript
enum ErrorCode {
  VALIDATION_ERROR = 'VALIDATION_ERROR',
  AUTHENTICATION_REQUIRED = 'AUTHENTICATION_REQUIRED',
  PERMISSION_DENIED = 'PERMISSION_DENIED',
  RESOURCE_NOT_FOUND = 'RESOURCE_NOT_FOUND',
  RESOURCE_CONFLICT = 'RESOURCE_CONFLICT',
  RATE_LIMIT_EXCEEDED = 'RATE_LIMIT_EXCEEDED',
  INTERNAL_ERROR = 'INTERNAL_ERROR'
}
```

### Type: `ValidationError`
```typescript
interface ValidationError {
  field: string;
  message: string;
  code: string;
}
```

---

## WebSocket Models

### Type: `WebSocketMessage`
```typescript
interface WebSocketMessage {
  type: WebSocketMessageType;
  data: any;
  timestamp: string;
}
```

### Enum: `WebSocketMessageType`
```typescript
enum WebSocketMessageType {
  // Client → Server
  SUBSCRIBE = 'subscribe',
  UNSUBSCRIBE = 'unsubscribe',
  PING = 'ping',
  
  // Server → Client
  ENVELOPE_STATUS_CHANGED = 'envelope.status.changed',
  RECIPIENT_SIGNED = 'envelope.recipient.signed',
  ENVELOPE_COMPLETED = 'envelope.completed',
  PONG = 'pong'
}
```

### Type: `SubscribeMessage`
```typescript
interface SubscribeMessage {
  type: 'subscribe';
  channels: string[];        // e.g., ['envelope:<id>', 'user:<id>']
}
```

---

## Common Utility Types

### Type: `Timestamp`
```typescript
type Timestamp = string;     // ISO 8601 format
```

### Type: `UUID`
```typescript
type UUID = string;          // UUID v4
```

### Type: `EmailAddress`
```typescript
type EmailAddress = string;  // Valid email format
```

### Type: `PhoneNumber`
```typescript
type PhoneNumber = string;   // E.164 format
```

### Type: `URL`
```typescript
type URL = string;           // Valid URL
```

### Type: `Base64`
```typescript
type Base64 = string;        // Base64-encoded data
```

---

## Validation Patterns

### Email Validation
```typescript
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
```

### Phone Validation (E.164)
```typescript
const PHONE_PATTERN = /^\+[1-9]\d{1,14}$/;
```

### Password Requirements
```typescript
interface PasswordRequirements {
  minLength: 12;
  requireUppercase: true;
  requireLowercase: true;
  requireNumber: true;
  requireSpecialChar: false;
}
```

### Access Code Format
```typescript
const ACCESS_CODE_PATTERN = /^[0-9]{6}$/;
```

---

## Constants

### File Size Limits
```typescript
const MAX_FILE_SIZE = 50 * 1024 * 1024;  // 50 MB
```

### Envelope Limits
```typescript
const MAX_DOCUMENTS_PER_ENVELOPE = 100;
const MAX_RECIPIENTS_PER_ENVELOPE = 100;
const MAX_FIELDS_PER_DOCUMENT = 500;
const DEFAULT_EXPIRATION_DAYS = 30;
const MAX_EXPIRATION_DAYS = 365;
```

### Session Timeouts
```typescript
const ACCESS_TOKEN_EXPIRY = 3600;          // 1 hour (seconds)
const REFRESH_TOKEN_EXPIRY = 2592000;      // 30 days (seconds)
const SIGNING_SESSION_TIMEOUT = 1800;      // 30 min (seconds)
const PRESIGNED_URL_EXPIRY = 3600;         // 1 hour (seconds)
```

### Field Dimensions
```typescript
const MIN_FIELD_WIDTH = 20;                // Pixels
const MIN_FIELD_HEIGHT = 20;               // Pixels
const DEFAULT_SIGNATURE_WIDTH = 150;
const DEFAULT_SIGNATURE_HEIGHT = 50;
const DEFAULT_TEXT_WIDTH = 200;
const DEFAULT_TEXT_HEIGHT = 30;
```

---

## Type Guards

### User Type Guard
```typescript
function isUser(obj: any): obj is User {
  return (
    typeof obj === 'object' &&
    typeof obj.userId === 'string' &&
    typeof obj.email === 'string' &&
    typeof obj.firstName === 'string' &&
    typeof obj.lastName === 'string'
  );
}
```

### Envelope Type Guard
```typescript
function isEnvelope(obj: any): obj is Envelope {
  return (
    typeof obj === 'object' &&
    typeof obj.envelopeId === 'string' &&
    typeof obj.subject === 'string' &&
    Object.values(EnvelopeStatus).includes(obj.status)
  );
}
```

---

## Python Equivalents

For Python services, use Pydantic models:

```python
from pydantic import BaseModel, EmailStr, Field
from enum import Enum
from typing import Optional, List
from datetime import datetime

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"

class User(BaseModel):
    user_id: str = Field(alias="userId")
    email: EmailStr
    first_name: str = Field(alias="firstName")
    last_name: str = Field(alias="lastName")
    company: Optional[str] = None
    phone: Optional[str] = None
    role: UserRole
    email_verified: bool = Field(alias="emailVerified")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    last_login_at: Optional[datetime] = Field(alias="lastLoginAt")
    
    class Config:
        populate_by_name = True
```

---

**End of Data Models Specification**
