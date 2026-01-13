# Envelope Management Specification

## Purpose
Provides the core workflow orchestration for document signing. Manages envelopes that contain documents and recipients, tracks signing progress, enforces signing order, and coordinates the complete signing lifecycle from creation to completion.

## ADDED Requirements

### Requirement: Envelope Creation
The system SHALL allow users to create envelopes to group documents and recipients for signing.

#### Scenario: Create draft envelope with valid data
- **WHEN** a user creates an envelope with subject and message
- **THEN** the system creates envelope in draft status
- **AND** assigns unique envelope ID
- **AND** sets sender as current user
- **AND** sets creation timestamp
- **AND** returns envelope ID and details

#### Scenario: Create envelope with documents
- **WHEN** a user attaches documents to a new envelope
- **THEN** the system validates documents exist and are accessible
- **AND** links documents to envelope
- **AND** stores document display order

#### Scenario: Create envelope without documents
- **WHEN** a user attempts to send envelope without documents
- **THEN** the system returns an error "Envelope must have at least one document"

### Requirement: Recipient Management
The system SHALL allow users to add and manage recipients for envelopes.

#### Scenario: Add recipient to draft envelope
- **WHEN** a user adds a recipient with name, email, and role
- **THEN** the system validates email format
- **AND** adds recipient to envelope
- **AND** generates unique access code
- **AND** assigns signing order position

#### Scenario: Add duplicate recipient email
- **WHEN** a user adds recipient with email already in envelope
- **THEN** the system returns an error "Recipient already added to envelope"

#### Scenario: Update recipient information in draft
- **WHEN** a user updates recipient name or email in draft envelope
- **THEN** the system updates recipient record
- **AND** maintains signing order

#### Scenario: Remove recipient from draft envelope
- **WHEN** a user removes a recipient from draft envelope
- **THEN** the system deletes recipient
- **AND** adjusts signing order for remaining recipients

#### Scenario: Attempt to modify recipients in sent envelope
- **WHEN** a user attempts to modify recipients in sent envelope
- **THEN** the system returns an error "Cannot modify sent envelope"

### Requirement: Signing Order Configuration
The system SHALL support sequential and parallel signing workflows.

#### Scenario: Configure parallel signing
- **WHEN** a user sets signing order to parallel
- **THEN** the system allows all recipients to sign simultaneously
- **AND** sets all recipients to signing order 1

#### Scenario: Configure sequential signing
- **WHEN** a user sets signing order to sequential
- **THEN** the system assigns signing order numbers (1, 2, 3...)
- **AND** enforces signing in specified order

#### Scenario: Reorder sequential signers
- **WHEN** a user changes signing order in draft envelope
- **THEN** the system updates signing order numbers
- **AND** validates no gaps in sequence

### Requirement: Envelope Sending
The system SHALL allow users to send draft envelopes to recipients.

#### Scenario: Send valid draft envelope
- **WHEN** a user sends a draft envelope
- **THEN** the system validates envelope has documents
- **AND** validates envelope has at least one recipient
- **AND** validates all signature fields are assigned
- **AND** changes status to "sent"
- **AND** records sent timestamp
- **AND** triggers email notifications to appropriate recipients

#### Scenario: Send envelope with missing signature fields
- **WHEN** a user attempts to send envelope without signature fields
- **THEN** the system returns an error "Envelope must have at least one signature field"

#### Scenario: Send envelope with expiration date
- **WHEN** a user sends envelope with custom expiration
- **THEN** the system validates expiration is future date
- **AND** stores expiration date
- **AND** schedules expiration check

### Requirement: Envelope Status Tracking
The system SHALL track envelope progress through its lifecycle.

#### Scenario: Track sent to delivered transition
- **WHEN** first recipient accesses the envelope
- **THEN** the system updates status to "delivered"
- **AND** records delivered timestamp for that recipient

#### Scenario: Track delivered to signed transition
- **WHEN** at least one recipient completes signing
- **THEN** the system updates status to "signed"
- **AND** records signed timestamp for that recipient

#### Scenario: Track signed to completed transition
- **WHEN** all required recipients complete signing
- **THEN** the system updates status to "completed"
- **AND** records completion timestamp
- **AND** triggers completion notifications
- **AND** generates certificate of completion

#### Scenario: View envelope current status
- **WHEN** a user requests envelope status
- **THEN** the system returns current status
- **AND** returns list of recipients with individual status
- **AND** returns completion percentage
- **AND** returns timestamps for status changes

### Requirement: Sequential Signing Enforcement
The system SHALL enforce signing order for sequential envelopes.

#### Scenario: Allow first signer to access envelope
- **WHEN** sequential envelope is sent
- **THEN** the system allows only signing order 1 recipient to sign
- **AND** blocks access for other recipients

#### Scenario: Notify next signer after completion
- **WHEN** a signer completes their part in sequential envelope
- **THEN** the system unlocks access for next signing order recipient
- **AND** sends notification to next recipient
- **AND** updates recipient status to "awaiting signature"

#### Scenario: Prevent out-of-order signing
- **WHEN** recipient with signing order 3 attempts to sign before recipient 2
- **THEN** the system returns an error "Not your turn to sign yet"
- **AND** displays current signer information

### Requirement: Parallel Signing Support
The system SHALL allow simultaneous signing for parallel envelopes.

#### Scenario: Allow all recipients to sign simultaneously
- **WHEN** parallel envelope is sent
- **THEN** the system allows all recipients to access immediately
- **AND** sends notifications to all recipients
- **AND** allows signing in any order

#### Scenario: Track parallel signing progress
- **WHEN** users query parallel envelope status
- **THEN** the system returns list of all recipients
- **AND** shows which have signed and which are pending

### Requirement: Envelope Expiration
The system SHALL automatically expire envelopes after configured time period.

#### Scenario: Set default expiration on send
- **WHEN** a user sends envelope without specifying expiration
- **THEN** the system sets expiration to 30 days from send date

#### Scenario: Set custom expiration date
- **WHEN** a user sends envelope with custom expiration date
- **THEN** the system validates date is in the future
- **AND** validates date is not more than 365 days out
- **AND** stores custom expiration date

#### Scenario: Expire envelope after timeout
- **WHEN** current date exceeds envelope expiration date
- **AND** envelope is not completed
- **THEN** the system changes status to "expired"
- **AND** prevents further signing
- **AND** notifies sender and pending recipients

#### Scenario: Extend envelope expiration
- **WHEN** sender extends expiration before it expires
- **THEN** the system updates expiration date
- **AND** notifies recipients of extension

### Requirement: Envelope Voiding
The system SHALL allow senders to cancel envelopes before completion.

#### Scenario: Void active envelope
- **WHEN** sender voids an envelope in sent, delivered, or signed status
- **THEN** the system changes status to "voided"
- **AND** records void reason
- **AND** records void timestamp
- **AND** prevents further actions on envelope
- **AND** notifies all recipients of cancellation

#### Scenario: Attempt to void completed envelope
- **WHEN** sender attempts to void completed envelope
- **THEN** the system returns an error "Cannot void completed envelope"

#### Scenario: Attempt to void by non-sender
- **WHEN** non-sender attempts to void envelope
- **THEN** the system returns 403 Forbidden
- **AND** logs unauthorized attempt

### Requirement: Envelope Listing and Search
The system SHALL allow users to view and search their envelopes.

#### Scenario: List user's sent envelopes
- **WHEN** a user requests their sent envelopes
- **THEN** the system returns envelopes where user is sender
- **AND** includes status, subject, recipient count, creation date
- **AND** supports pagination (25 per page)
- **AND** sorts by creation date (newest first)

#### Scenario: List user's received envelopes
- **WHEN** a user requests envelopes they need to sign
- **THEN** the system returns envelopes where user is recipient
- **AND** filters to envelopes requiring action
- **AND** shows sender, subject, status, due date

#### Scenario: Filter envelopes by status
- **WHEN** a user filters by status (draft, sent, completed, etc.)
- **THEN** the system returns only envelopes with matching status
- **AND** maintains pagination and sorting

#### Scenario: Search envelopes by recipient email
- **WHEN** a user searches by recipient email
- **THEN** the system returns envelopes containing that recipient
- **AND** performs case-insensitive search

#### Scenario: Search envelopes by subject
- **WHEN** a user searches by subject text
- **THEN** the system returns envelopes with matching subject
- **AND** performs case-insensitive partial match

### Requirement: Envelope Templates
The system SHALL allow users to create and reuse envelope templates.

#### Scenario: Create template from envelope
- **WHEN** a user saves an envelope as template
- **THEN** the system stores envelope structure (documents, recipients, fields)
- **AND** assigns template name and description
- **AND** removes specific recipient email addresses
- **AND** stores as reusable template

#### Scenario: Create envelope from template
- **WHEN** a user creates envelope from template
- **THEN** the system copies template structure
- **AND** prompts for recipient information
- **AND** creates draft envelope
- **AND** allows modifications before sending

#### Scenario: List user's templates
- **WHEN** a user requests their templates
- **THEN** the system returns templates created by user
- **AND** includes template name, description, creation date
- **AND** shows document and recipient count

### Requirement: Reminder Notifications
The system SHALL allow senders to send reminder notifications to pending recipients.

#### Scenario: Send reminder to pending recipient
- **WHEN** sender requests reminder for specific recipient
- **THEN** the system validates recipient status is pending
- **AND** sends reminder email and/or SMS
- **AND** records reminder sent timestamp
- **AND** limits reminders to 3 per day per recipient

#### Scenario: Automatic reminder after 7 days
- **WHEN** 7 days pass without recipient action
- **THEN** the system automatically sends reminder
- **AND** records auto-reminder sent

#### Scenario: Attempt reminder for completed recipient
- **WHEN** sender attempts reminder for recipient who already signed
- **THEN** the system returns an error "Recipient has already signed"

### Requirement: Envelope Metadata
The system SHALL store and provide comprehensive envelope metadata.

#### Scenario: Retrieve envelope details
- **WHEN** a user requests envelope details
- **THEN** the system returns full envelope information
- **AND** includes sender, subject, message, status
- **AND** includes all recipients with roles and status
- **AND** includes all attached documents
- **AND** includes creation, sent, completed timestamps
- **AND** includes expiration date

#### Scenario: Calculate envelope completion percentage
- **WHEN** a user requests envelope progress
- **THEN** the system calculates percentage of completed signatures
- **AND** returns completion percentage
- **AND** shows pending recipient count
