# Event Bus & Message Queue Specification

**Version:** 1.0.0  
**Last Updated:** January 13, 2026  
**Purpose:** Asynchronous event-driven communication between services

## Overview

This document defines the event-driven architecture for asynchronous communication between services. Events enable loose coupling, scalability, and reliability.

**Message Broker:** Redis Streams or RabbitMQ  
**Pattern:** Event Sourcing + Pub/Sub  
**Format:** JSON  
**Guarantees:** At-least-once delivery  

---

## Event Categories

### 1. Envelope Events
Events related to envelope lifecycle.

### 2. Document Events
Events related to document processing.

### 3. Notification Events
Events triggering notifications.

### 4. Audit Events
Events for audit trail logging.

### 5. System Events
Internal system events.

---

## Event Structure

All events follow this standard structure:

```json
{
  "eventId": "uuid (unique event ID)",
  "eventType": "string (envelope.sent, document.uploaded, etc.)",
  "version": "1.0",
  "timestamp": "ISO8601 (when event occurred)",
  "source": "string (service name that published event)",
  "traceId": "uuid (for distributed tracing)",
  "data": {
    ... event-specific payload ...
  },
  "metadata": {
    "userId": "uuid | null",
    "correlationId": "uuid | null",
    "causationId": "uuid | null (ID of event that caused this)"
  }
}
```

---

## Envelope Events

### Event: `envelope.created`
Published when new envelope created (draft).

**Publisher:** Envelope Service  
**Consumers:** Audit Service

**Data:**
```json
{
  "envelopeId": "uuid",
  "senderId": "uuid",
  "subject": "string",
  "documentCount": 0,
  "recipientCount": 0,
  "createdAt": "ISO8601"
}
```

---

### Event: `envelope.sent`
Published when envelope sent to recipients.

**Publisher:** Envelope Service  
**Consumers:** Notification Service, Audit Service

**Data:**
```json
{
  "envelopeId": "uuid",
  "senderId": "uuid",
  "senderName": "string",
  "senderEmail": "string",
  "subject": "string",
  "message": "string",
  "recipients": [
    {
      "recipientId": "uuid",
      "name": "string",
      "email": "string",
      "phone": "string | null",
      "role": "signer | cc | approver",
      "signingOrder": 1,
      "accessCode": "string"
    }
  ],
  "documents": [
    {
      "documentId": "uuid",
      "name": "string",
      "pageCount": 10
    }
  ],
  "signingOrder": "parallel | sequential",
  "expiresAt": "ISO8601",
  "sentAt": "ISO8601"
}
```

**Notification Actions:**
- Send email to all recipients (parallel) or first recipient (sequential)
- Send SMS if enabled
- Send confirmation email to sender

---

### Event: `envelope.viewed`
Published when recipient views envelope.

**Publisher:** Signing Service  
**Consumers:** Envelope Service, Audit Service, Notification Service (for sender notification)

**Data:**
```json
{
  "envelopeId": "uuid",
  "recipientId": "uuid",
  "recipientName": "string",
  "recipientEmail": "string",
  "viewedAt": "ISO8601",
  "ipAddress": "string",
  "userAgent": "string",
  "geolocation": {
    "country": "string",
    "region": "string",
    "city": "string"
  }
}
```

---

### Event: `envelope.recipient.signed`
Published when recipient completes signing.

**Publisher:** Signing Service  
**Consumers:** Envelope Service, Notification Service, Audit Service

**Data:**
```json
{
  "envelopeId": "uuid",
  "recipientId": "uuid",
  "recipientName": "string",
  "recipientEmail": "string",
  "signingOrder": 1,
  "fieldsCompleted": 5,
  "signedAt": "ISO8601",
  "ipAddress": "string",
  "userAgent": "string",
  "geolocation": {
    "country": "string",
    "region": "string",
    "city": "string"
  },
  "deviceInfo": {
    "deviceType": "desktop | mobile | tablet",
    "os": "string",
    "browser": "string"
  }
}
```

**Envelope Service Actions:**
- Update recipient status to 'signed'
- Check if envelope completed
- Unlock next recipient if sequential

**Notification Actions:**
- Notify sender of progress
- Notify next signer if sequential
- If last signer, trigger envelope.completed

---

### Event: `envelope.completed`
Published when all recipients have signed.

**Publisher:** Envelope Service  
**Consumers:** Notification Service, Audit Service, Document Service, Certificate Service

**Data:**
```json
{
  "envelopeId": "uuid",
  "senderId": "uuid",
  "senderName": "string",
  "senderEmail": "string",
  "subject": "string",
  "recipients": [
    {
      "recipientId": "uuid",
      "name": "string",
      "email": "string",
      "signedAt": "ISO8601"
    }
  ],
  "completedAt": "ISO8601",
  "totalDuration": "PT2H30M (ISO 8601 duration)"
}
```

**Actions:**
- Generate certificate of completion
- Send completion emails to all parties
- Mark documents as completed
- Archive if needed

---

### Event: `envelope.declined`
Published when recipient declines to sign.

**Publisher:** Signing Service  
**Consumers:** Envelope Service, Notification Service, Audit Service

**Data:**
```json
{
  "envelopeId": "uuid",
  "recipientId": "uuid",
  "recipientName": "string",
  "recipientEmail": "string",
  "reason": "string",
  "declinedAt": "ISO8601",
  "ipAddress": "string"
}
```

**Actions:**
- Update envelope status to 'declined'
- Notify sender and other recipients
- Revoke all access codes

---

### Event: `envelope.voided`
Published when sender voids envelope.

**Publisher:** Envelope Service  
**Consumers:** Notification Service, Audit Service, Auth Service (revoke codes)

**Data:**
```json
{
  "envelopeId": "uuid",
  "senderId": "uuid",
  "senderName": "string",
  "reason": "string",
  "voidedAt": "ISO8601",
  "recipients": [
    {
      "recipientId": "uuid",
      "name": "string",
      "email": "string"
    }
  ]
}
```

**Actions:**
- Notify all recipients
- Revoke access codes
- Log void event

---

### Event: `envelope.expired`
Published when envelope expires without completion.

**Publisher:** Envelope Service (scheduled job)  
**Consumers:** Notification Service, Audit Service

**Data:**
```json
{
  "envelopeId": "uuid",
  "senderId": "uuid",
  "senderEmail": "string",
  "subject": "string",
  "expiresAt": "ISO8601",
  "pendingRecipients": [
    {
      "recipientId": "uuid",
      "name": "string",
      "email": "string"
    }
  ]
}
```

---

### Event: `envelope.reminder.sent`
Published when manual reminder sent.

**Publisher:** Envelope Service  
**Consumers:** Notification Service, Audit Service

**Data:**
```json
{
  "envelopeId": "uuid",
  "senderId": "uuid",
  "recipientIds": ["uuid"],
  "recipients": [
    {
      "recipientId": "uuid",
      "name": "string",
      "email": "string",
      "accessCode": "string"
    }
  ],
  "sentAt": "ISO8601"
}
```

---

## Document Events

### Event: `document.uploaded`
Published when document upload starts.

**Publisher:** Document Service  
**Consumers:** Audit Service, Virus Scanner Service

**Data:**
```json
{
  "documentId": "uuid",
  "userId": "uuid",
  "name": "string",
  "originalFilename": "string",
  "fileSize": 123456,
  "fileType": "string",
  "storageKey": "string",
  "uploadedAt": "ISO8601"
}
```

---

### Event: `document.processing.started`
Document processing started (conversion, scanning).

**Publisher:** Document Service  
**Consumers:** WebSocket Service (real-time updates)

**Data:**
```json
{
  "documentId": "uuid",
  "userId": "uuid",
  "processingType": "virus_scan | pdf_conversion | thumbnail_generation",
  "startedAt": "ISO8601"
}
```

---

### Event: `document.ready`
Document successfully processed and ready to use.

**Publisher:** Document Service  
**Consumers:** Envelope Service, WebSocket Service

**Data:**
```json
{
  "documentId": "uuid",
  "userId": "uuid",
  "name": "string",
  "pageCount": 10,
  "thumbnailUrl": "string",
  "checksum": "string",
  "readyAt": "ISO8601"
}
```

---

### Event: `document.processing.failed`
Document processing failed.

**Publisher:** Document Service  
**Consumers:** Notification Service, WebSocket Service

**Data:**
```json
{
  "documentId": "uuid",
  "userId": "uuid",
  "userEmail": "string",
  "errorType": "virus_detected | corrupted | conversion_failed",
  "errorMessage": "string",
  "failedAt": "ISO8601"
}
```

---

### Event: `document.deleted`
Document deleted by user.

**Publisher:** Document Service  
**Consumers:** Storage Service, Audit Service

**Data:**
```json
{
  "documentId": "uuid",
  "userId": "uuid",
  "storageKey": "string",
  "deletedAt": "ISO8601"
}
```

---

## Notification Events

### Event: `notification.queued`
Notification queued for delivery.

**Publisher:** Notification Service  
**Consumers:** Delivery Workers

**Data:**
```json
{
  "notificationId": "uuid",
  "channel": "email | sms",
  "recipientAddress": "string",
  "templateId": "string",
  "templateData": {},
  "priority": "high | normal | low",
  "queuedAt": "ISO8601"
}
```

---

### Event: `notification.sent`
Notification sent to provider (SMTP/Twilio).

**Publisher:** Delivery Workers  
**Consumers:** Notification Service (update status)

**Data:**
```json
{
  "notificationId": "uuid",
  "providerMessageId": "string",
  "sentAt": "ISO8601"
}
```

---

### Event: `notification.delivered`
Notification confirmed delivered.

**Publisher:** Webhook receiver (from provider)  
**Consumers:** Notification Service

**Data:**
```json
{
  "notificationId": "uuid",
  "providerMessageId": "string",
  "deliveredAt": "ISO8601"
}
```

---

### Event: `notification.failed`
Notification delivery failed.

**Publisher:** Delivery Workers  
**Consumers:** Notification Service (retry logic)

**Data:**
```json
{
  "notificationId": "uuid",
  "failureReason": "string",
  "retryCount": 1,
  "willRetry": true,
  "nextRetryAt": "ISO8601 | null",
  "failedAt": "ISO8601"
}
```

---

## Audit Events

### Event: `audit.event.logged`
Audit event successfully logged.

**Publisher:** Audit Service  
**Consumers:** Compliance Service, Monitoring

**Data:**
```json
{
  "eventId": "uuid",
  "envelopeId": "uuid",
  "eventType": "string",
  "eventHash": "string",
  "previousHash": "string | null",
  "loggedAt": "ISO8601"
}
```

---

### Event: `audit.tampering.detected`
Hash chain integrity violation detected.

**Publisher:** Audit Service  
**Consumers:** Security Service, Admin Notification

**Data:**
```json
{
  "envelopeId": "uuid",
  "tamperedEventId": "uuid",
  "expectedHash": "string",
  "actualHash": "string",
  "detectedAt": "ISO8601",
  "severity": "critical"
}
```

---

### Event: `certificate.generated`
Certificate of completion generated.

**Publisher:** Certificate Service  
**Consumers:** Document Service, Notification Service

**Data:**
```json
{
  "certificateId": "uuid",
  "envelopeId": "uuid",
  "storageKey": "string",
  "verificationCode": "string",
  "envelopeHash": "string",
  "generatedAt": "ISO8601"
}
```

---

## System Events

### Event: `user.registered`
New user registered.

**Publisher:** Auth Service  
**Consumers:** Notification Service, Analytics Service

**Data:**
```json
{
  "userId": "uuid",
  "email": "string",
  "firstName": "string",
  "lastName": "string",
  "verificationToken": "string",
  "registeredAt": "ISO8601"
}
```

---

### Event: `user.verified`
User email verified.

**Publisher:** Auth Service  
**Consumers:** Notification Service

**Data:**
```json
{
  "userId": "uuid",
  "email": "string",
  "verifiedAt": "ISO8601"
}
```

---

### Event: `user.password.reset`
Password reset completed.

**Publisher:** Auth Service  
**Consumers:** Notification Service, Audit Service

**Data:**
```json
{
  "userId": "uuid",
  "email": "string",
  "ipAddress": "string",
  "resetAt": "ISO8601"
}
```

---

### Event: `user.account.locked`
Account locked due to failed login attempts.

**Publisher:** Auth Service  
**Consumers:** Notification Service

**Data:**
```json
{
  "userId": "uuid",
  "email": "string",
  "reason": "too_many_failed_attempts",
  "lockedUntil": "ISO8601",
  "lockedAt": "ISO8601"
}
```

---

## Event Queues

### Queue Configuration

**Envelope Queue:**
- Name: `envelope-events`
- Dead Letter Queue: `envelope-events-dlq`
- Max Retries: 3
- Visibility Timeout: 60s

**Document Queue:**
- Name: `document-events`
- Dead Letter Queue: `document-events-dlq`
- Max Retries: 5
- Visibility Timeout: 300s (longer for processing)

**Notification Queue:**
- Name: `notification-events`
- Dead Letter Queue: `notification-events-dlq`
- Max Retries: 3
- Visibility Timeout: 30s

**Audit Queue:**
- Name: `audit-events`
- Dead Letter Queue: `audit-events-dlq`
- Max Retries: 5
- Visibility Timeout: 60s

---

## Event Publishing

### Publishing with Redis Streams

```python
import redis
import json
from datetime import datetime
import uuid

redis_client = redis.Redis(host='localhost', port=6379)

def publish_event(stream_name, event_type, data, metadata=None):
    event = {
        "eventId": str(uuid.uuid4()),
        "eventType": event_type,
        "version": "1.0",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "source": "envelope-service",
        "traceId": get_current_trace_id(),
        "data": data,
        "metadata": metadata or {}
    }
    
    redis_client.xadd(
        stream_name,
        {"event": json.dumps(event)},
        maxlen=100000  # Keep last 100k events
    )
    
    return event["eventId"]

# Usage
publish_event(
    "envelope-events",
    "envelope.sent",
    {
        "envelopeId": "123e4567-e89b-12d3-a456-426614174000",
        "senderId": "123e4567-e89b-12d3-a456-426614174001",
        ...
    }
)
```

---

### Publishing with RabbitMQ

```python
import pika
import json
from datetime import datetime
import uuid

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

def publish_event(exchange, routing_key, event_type, data, metadata=None):
    event = {
        "eventId": str(uuid.uuid4()),
        "eventType": event_type,
        "version": "1.0",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "source": "envelope-service",
        "traceId": get_current_trace_id(),
        "data": data,
        "metadata": metadata or {}
    }
    
    channel.basic_publish(
        exchange=exchange,
        routing_key=routing_key,
        body=json.dumps(event),
        properties=pika.BasicProperties(
            delivery_mode=2,  # Persistent
            content_type='application/json',
            message_id=event["eventId"]
        )
    )
    
    return event["eventId"]

# Usage
publish_event(
    "envelope-exchange",
    "envelope.sent",
    "envelope.sent",
    { ... }
)
```

---

## Event Consuming

### Consumer with Redis Streams

```python
def consume_events(stream_name, consumer_group, consumer_name, handler):
    redis_client.xgroup_create(stream_name, consumer_group, id='0', mkstream=True)
    
    while True:
        events = redis_client.xreadgroup(
            consumer_group,
            consumer_name,
            {stream_name: '>'},
            count=10,
            block=1000
        )
        
        for stream, messages in events:
            for message_id, message_data in messages:
                try:
                    event = json.loads(message_data[b'event'])
                    handler(event)
                    redis_client.xack(stream_name, consumer_group, message_id)
                except Exception as e:
                    logger.error(f"Error processing event: {e}")
                    # Event will be redelivered
```

---

### Consumer with RabbitMQ

```python
def callback(ch, method, properties, body):
    try:
        event = json.loads(body)
        handle_event(event)
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        logger.error(f"Error processing event: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

channel.basic_consume(
    queue='envelope-events',
    on_message_callback=callback,
    auto_ack=False
)

channel.start_consuming()
```

---

## Event Ordering

**Guarantee:** Events for the same envelope are processed in order.

**Implementation:**
- Use envelope ID as partition key (Redis Streams)
- Use envelope ID as routing key (RabbitMQ)
- Single consumer per partition/queue

---

## Dead Letter Queues

Failed events (after max retries) go to DLQ for manual inspection.

**Monitoring:**
- Alert when DLQ depth > 100
- Review DLQ daily
- Investigate and fix root cause
- Replay events after fix

---

## Event Replay

For debugging or recovery:

```python
def replay_events(envelope_id, from_timestamp):
    """Replay all events for envelope since timestamp"""
    events = redis_client.xrange(
        'envelope-events',
        min=f'{from_timestamp}-0',
        max='+'
    )
    
    for event_id, event_data in events:
        event = json.loads(event_data[b'event'])
        if event['data'].get('envelopeId') == envelope_id:
            process_event(event)
```

---

## Event Versioning

When event schema changes:

1. **Additive changes** (new fields): Add with default values
2. **Breaking changes**: Create new event version (e.g., `envelope.sent.v2`)
3. **Deprecation**: Support both versions for 6 months

---

## Monitoring & Observability

**Metrics to track:**
- Events published per second
- Event processing latency (p50, p95, p99)
- Dead letter queue depth
- Consumer lag
- Error rate per event type

**Distributed Tracing:**
- Use `traceId` to track events across services
- OpenTelemetry integration

---

**End of Event Bus Specification**
