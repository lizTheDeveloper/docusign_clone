# Interface Specifications - Complete Index

**Version:** 1.0.0  
**Last Updated:** January 13, 2026  
**Purpose:** Central index of all interface specifications for parallel development

---

## Overview

This directory contains complete interface definitions that enable **parallel frontend and backend development**. All contracts are defined upfront so teams can work independently while ensuring compatibility.

### Key Benefits

✅ **Frontend can mock backend** - Complete API contracts with request/response schemas  
✅ **Services can develop independently** - Internal API contracts defined  
✅ **Database schema is finalized** - No schema conflicts during integration  
✅ **Events are standardized** - Asynchronous communication is well-defined  
✅ **Type safety across stack** - Shared data models for consistency  

---

## Interface Specifications

### 1. [REST API Specification](rest-api.md)
**Complete HTTP API for frontend-backend communication**

**Contents:**
- Authentication endpoints (register, login, refresh, verify)
- User profile management
- Document upload/download/management
- Envelope creation, management, sending
- Recipient management
- Signature field editor endpoints
- Signing workflow endpoints (no auth required)
- Audit trail and certificate endpoints
- Notification preferences
- WebSocket events for real-time updates
- Error handling and pagination
- Rate limiting and CORS policy

**Use this for:**
- Frontend development (React/Vue/Angular)
- API client generation (OpenAPI/Swagger)
- Testing and mocking
- API documentation

---

### 2. [Service Interface Specification](service-interfaces.md)
**Internal service-to-service API contracts**

**Contents:**
- Auth Service internal APIs (token validation, access code management)
- Document Service internal APIs (ownership validation, presigned URLs)
- Envelope Service internal APIs (access validation, status updates)
- Field Service internal APIs (field validation, completion)
- Signing Service internal APIs (session management)
- Notification Service internal APIs (email/SMS delivery)
- Audit Service internal APIs (event logging, hash chain verification)
- Storage Service internal APIs (file upload/download, presigned URLs)
- Service authentication and discovery
- Circuit breaker and retry policies
- Health checks

**Use this for:**
- Microservices architecture
- Service-to-service communication
- Backend integration
- Distributed system design

---

### 3. [Database Schema Specification](database-schema.md)
**Complete PostgreSQL database schema**

**Contents:**
- All tables with columns, types, and constraints
- Primary keys, foreign keys, and indexes
- Views for common queries
- Triggers and functions
- Partitioning strategy
- Data retention policies
- Backup and connection pooling configuration

**Tables:**
- `users`, `email_verifications`, `password_resets`, `refresh_tokens`
- `documents`, `document_pages`
- `envelopes`, `envelope_documents`, `recipients`
- `signature_fields`, `adopted_signatures`, `signing_sessions`
- `audit_events`, `certificates`
- `notifications`, `notification_preferences`
- `api_keys`, `webhooks`, `templates`

**Use this for:**
- Database setup and migrations
- ORM model generation
- Query optimization
- Data modeling

---

### 4. [Event Bus Specification](event-bus.md)
**Asynchronous event-driven communication**

**Contents:**
- Event structure and format
- Envelope events (sent, viewed, signed, completed, declined, voided, expired)
- Document events (uploaded, processing, ready, failed, deleted)
- Notification events (queued, sent, delivered, failed)
- Audit events (logged, tampering detected, certificate generated)
- System events (user registered, verified, password reset)
- Queue configuration (Redis Streams / RabbitMQ)
- Publishing and consuming patterns
- Event ordering and replay
- Dead letter queues

**Use this for:**
- Event-driven architecture
- Asynchronous processing
- Service decoupling
- Message queue implementation

---

### 5. [Data Models Specification](data-models.md)
**Shared type definitions and DTOs**

**Contents:**
- TypeScript interfaces for all data structures
- Python Pydantic model equivalents
- User, authentication, and profile models
- Document and page models
- Envelope, recipient, and field models
- Signing workflow models
- Audit trail and certificate models
- Notification models
- Pagination and error models
- WebSocket message types
- Validation patterns and constants
- Type guards and utility types

**Use this for:**
- Type generation (TypeScript, Python, Java)
- Frontend state management
- API client type safety
- Validation and serialization

---

## Quick Start Guide

### For Frontend Developers

1. **Read:** [REST API Specification](rest-api.md)
2. **Reference:** [Data Models Specification](data-models.md)
3. **Mock:** Use request/response schemas to create mock API responses
4. **Build:** Develop UI components with confidence in API contracts

**Example:**
```typescript
// Import shared types
import { User, Envelope, EnvelopeStatus } from '@/types/models';

// API call with known response shape
const response = await fetch('/api/v1/envelopes/123');
const envelope: Envelope = await response.json();
```

---

### For Backend Developers

1. **Read:** [Database Schema](database-schema.md) - Set up database
2. **Read:** [REST API Specification](rest-api.md) - Implement endpoints
3. **Read:** [Service Interfaces](service-interfaces.md) - Internal APIs
4. **Read:** [Event Bus](event-bus.md) - Publish/consume events
5. **Reference:** [Data Models](data-models.md) - Type definitions

**Example:**
```python
from models import User, Envelope, EnvelopeStatus
from pydantic import BaseModel

@router.post("/envelopes/{envelope_id}/send")
async def send_envelope(envelope_id: str) -> dict:
    # Implementation matches REST API spec
    envelope = await envelope_service.send(envelope_id)
    
    # Publish event as per event bus spec
    await event_bus.publish("envelope.sent", {
        "envelopeId": envelope_id,
        "senderId": envelope.sender_id,
        ...
    })
    
    return {"status": "sent", "envelopeId": envelope_id}
```

---

### For Full-Stack Teams

**Parallel Development Flow:**

```
Week 1-2: Database Setup + API Mocking
├─ Backend: Create tables from database schema
└─ Frontend: Mock REST API with MSW or similar

Week 3-4: Core Features
├─ Backend: Implement auth + document endpoints
└─ Frontend: Build auth flows + document upload UI

Week 5-6: Envelope Management
├─ Backend: Envelope CRUD + recipients
└─ Frontend: Envelope creator UI

Week 7-8: Field Editor + Signing
├─ Backend: Field placement + signing workflow APIs
└─ Frontend: Drag-drop editor + signing UI

Week 9-10: Notifications + Audit
├─ Backend: Event consumers + email/SMS
└─ Frontend: Real-time updates (WebSocket)

Week 11-12: Integration + Testing
└─ Both: Replace mocks with real APIs, end-to-end tests
```

---

## Service Architecture

### Microservices Diagram

```
┌─────────────┐
│   Frontend  │
│ (React/Vue) │
└──────┬──────┘
       │ REST API
       ▼
┌─────────────────────────────────────────┐
│         API Gateway / Load Balancer     │
└────────────┬────────────────────────────┘
             │
    ┌────────┴────────┬─────────┬──────────┐
    ▼                 ▼         ▼          ▼
┌─────────┐  ┌──────────────┐  ┌────────────┐  ┌──────────┐
│  Auth   │  │   Document   │  │  Envelope  │  │  Signing │
│ Service │  │   Service    │  │  Service   │  │  Service │
└────┬────┘  └──────┬───────┘  └─────┬──────┘  └────┬─────┘
     │              │                 │              │
     └──────────────┴─────────────────┴──────────────┘
                          │
                          ▼
              ┌─────────────────────┐
              │   Event Bus (Redis  │
              │   or RabbitMQ)      │
              └──────────┬──────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
  ┌────────────┐  ┌───────────┐  ┌──────────────┐
  │Notification│  │   Audit   │  │  Certificate │
  │  Service   │  │  Service  │  │   Service    │
  └────────────┘  └───────────┘  └──────────────┘
         │
         ▼
  ┌────────────┐
  │SMTP/Twilio │
  └────────────┘

         All Services
              │
              ▼
    ┌──────────────────┐
    │   PostgreSQL     │
    │   Database       │
    └──────────────────┘
    
    ┌──────────────────┐
    │   S3 / MinIO     │
    │   Object Storage │
    └──────────────────┘
```

---

## Data Flow Examples

### Example 1: Sending an Envelope

```
1. Frontend → POST /envelopes/:id/send
2. Envelope Service validates envelope
3. Envelope Service → Event: envelope.sent
4. Notification Service consumes event
5. Notification Service → POST /internal/notifications/send-batch
6. Audit Service logs event
7. Frontend receives 200 OK
8. WebSocket notifies sender of delivery
```

### Example 2: Signing a Document

```
1. Recipient clicks email link
2. Frontend → GET /signing/:accessCode
3. Signing Service → POST /internal/auth/validate-access-code
4. Signing Service → POST /internal/signing/create-session
5. Frontend renders signing UI
6. Recipient fills fields
7. Frontend → POST /signing/:accessCode/fields/:fieldId/complete
8. Recipient submits
9. Frontend → POST /signing/:accessCode/submit
10. Signing Service validates all required fields
11. Signing Service → POST /internal/envelopes/update-recipient-status
12. Signing Service → Event: envelope.recipient.signed
13. Envelope Service checks completion
14. If complete → Event: envelope.completed
15. Notification Service sends completion emails
16. Certificate Service generates PDF
```

---

## Testing with Interfaces

### Unit Tests
Use data models to ensure type safety:
```typescript
import { Envelope, EnvelopeStatus } from '@/models';

test('envelope transitions to completed', () => {
  const envelope: Envelope = {
    envelopeId: '123',
    status: EnvelopeStatus.SENT,
    // ... matches interface exactly
  };
});
```

### Integration Tests
Test against API specification:
```python
def test_send_envelope():
    response = client.post('/api/v1/envelopes/123/send')
    assert response.status_code == 200
    # Response matches REST API spec exactly
    assert response.json() == {
        "envelopeId": "123",
        "status": "sent",
        "sentAt": "2026-01-13T...",
        "recipientsSent": 3
    }
```

### Contract Tests
Validate services implement interfaces correctly:
- Use Pact for consumer-driven contracts
- Validate events against event schemas
- Test database schema migrations

---

## Code Generation

### OpenAPI/Swagger
Generate from REST API spec:
```bash
# Generate TypeScript client
openapi-generator-cli generate -i rest-api.yaml -g typescript-axios

# Generate Python FastAPI server stubs
openapi-generator-cli generate -i rest-api.yaml -g python-fastapi
```

### TypeScript Types
```bash
# Convert data models to TypeScript
cp data-models.md src/types/models.ts
```

### Database Migrations
```bash
# Generate migration from schema
alembic revision --autogenerate -m "initial_schema"
```

---

## Validation Tools

### API Spec Validation
```bash
# Validate REST API responses match spec
npm install -g @stoplight/spectral-cli
spectral lint rest-api.yaml
```

### Event Schema Validation
```bash
# Validate events match schema
ajv validate -s event-schema.json -d event-data.json
```

### Type Checking
```bash
# TypeScript
tsc --noEmit

# Python
mypy app/
```

---

## Change Management

When interfaces need to change:

1. **Propose change** in OpenSpec
2. **Version the interface** (e.g., `/v2/envelopes`)
3. **Update all specs** (REST API, database, events, models)
4. **Coordinate with teams** before implementation
5. **Support both versions** during migration
6. **Deprecate old version** after 6 months

---

## Troubleshooting

### Frontend can't connect to backend
- Check CORS configuration in REST API spec
- Verify authentication token format (JWT)
- Check error response format matches spec

### Service-to-service call fails
- Verify service authentication (X-Service-Token)
- Check circuit breaker status
- Verify service discovery configuration

### Event not being processed
- Check event format matches event bus spec
- Verify consumer group is running
- Check dead letter queue

### Database constraint violation
- Review database schema
- Check foreign key relationships
- Validate data types match

---

## Additional Resources

- [SPECS_SUMMARY.md](../SPECS_SUMMARY.md) - High-level overview of all changes
- [openspec/changes/](../openspec/changes/) - Individual change proposals
- [openspec/AGENTS.md](../openspec/AGENTS.md) - OpenSpec workflow guide

---

## Contributing

When adding new features:

1. Update relevant interface specifications
2. Add references in change proposals
3. Maintain consistency across all specs
4. Document breaking changes
5. Version APIs appropriately

---

**Questions?** All interface contracts are complete and ready for parallel development. Frontend and backend teams can now work independently with full confidence in compatibility.
