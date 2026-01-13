# Project Context

## Purpose
This is a DocuSign clone - an electronic signature platform that enables users to securely send, sign, and manage digital documents. The system facilitates legally binding electronic signatures, document workflow management, and comprehensive audit trails for compliance.

**Core Goals:**
- Provide secure, legally compliant electronic signature workflows
- Enable multi-party document signing with role-based access
- Maintain complete audit trails for regulatory compliance
- Support various document formats (PDF, Word, etc.)
- Deliver intuitive user experience for senders and signers

## Tech Stack
- **Backend:** Python (preferred), or TypeScript/Node.js
- **Frontend:** React or similar modern framework
- **Database:** PostgreSQL for relational data, Redis for caching/sessions
- **Storage:** S3-compatible object storage for documents
- **Authentication:** JWT-based auth with OAuth2 support
- **Email:** SMTP integration for notifications
- **PDF Processing:** PDF manipulation libraries (PyPDF2/pdfplumber for Python)
- **Cryptography:** Industry-standard libraries for encryption and digital signatures

## Project Conventions

### Code Style
- **Python:** PEP 8 compliant, use type hints, docstrings for all public functions/classes
- **TypeScript:** Strict mode enabled, ESLint + Prettier configured
- **Naming:**
  - Classes: PascalCase
  - Functions/methods: snake_case (Python) or camelCase (TypeScript)
  - Constants: UPPER_SNAKE_CASE
  - Files: lowercase with underscores (Python) or kebab-case (TypeScript)
- **Documentation:** Clear comments explaining business logic, especially around security and compliance
- **Error Handling:** Always handle exceptions, provide meaningful error messages
- **Logging:** Structured logging with appropriate levels (INFO, WARNING, ERROR)

### Architecture Patterns
- **Clean Architecture:** Separation of concerns (domain, application, infrastructure layers)
- **Repository Pattern:** Data access abstraction
- **Service Layer:** Business logic encapsulation
- **API Design:** RESTful APIs with clear versioning (v1, v2)
- **Event-Driven:** Use events for workflow state changes and notifications
- **Stateless Services:** Design for horizontal scalability
- **Configuration:** Environment-based config (dev, staging, production)

### Testing Strategy
- **Unit Tests:** Required for all business logic (minimum 80% coverage)
- **Integration Tests:** Required for API endpoints and database interactions
- **E2E Tests:** Required for critical workflows (document send → sign → complete)
- **Security Tests:** Required for authentication, authorization, and data access
- **Test Frameworks:** pytest (Python), Jest/Vitest (TypeScript)
- **Mocking:** Use mocks for external dependencies (email, storage, etc.)
- **Test Data:** Faker or similar for generating test data
- **CI/CD:** All tests run in CI pipeline before merge

### Git Workflow
- **Branch Strategy:** GitFlow or trunk-based development
- **Branch Naming:** `feature/`, `bugfix/`, `hotfix/`, `refactor/`
- **Commits:** Conventional commits format: `type(scope): description`
  - Types: feat, fix, docs, style, refactor, test, chore
- **Pull Requests:** Required for all changes, minimum 1 reviewer
- **Merge Strategy:** Squash and merge for features, rebase for clean history

## Domain Context

### Core Concepts
- **Document:** A file that requires signatures (PDF, Word, etc.)
- **Envelope:** A container for one or more documents sent for signing
- **Signer/Recipient:** Person who needs to sign or review the document
- **Signing Order:** Sequential or parallel signing workflows
- **Fields:** Form fields (signature, initial, date, text) placed on documents
- **Template:** Pre-configured document with fields for reuse
- **Audit Trail:** Complete history of all actions on a document
- **Certificate of Completion:** Final proof of completed signing

### Workflow States
1. **Draft:** Envelope created but not sent
2. **Sent:** Envelope delivered to recipients
3. **Delivered:** Recipients have accessed the envelope
4. **Signed:** All required signatures completed
5. **Completed:** All workflows finished, document finalized
6. **Declined:** Recipient refused to sign
7. **Voided:** Sender cancelled the envelope
8. **Expired:** Envelope exceeded time limit

### Security & Compliance
- **Legal Requirements:** eIDAS (EU), ESIGN Act (US), UETA compliance
- **Data Protection:** GDPR, CCPA compliance
- **Encryption:** All documents encrypted at rest and in transit
- **Audit Logs:** Immutable, tamper-proof audit trails
- **Authentication:** Multi-factor authentication options
- **Access Control:** Role-based and document-level permissions

## Important Constraints

### Security Constraints
- All PII and document data must be encrypted
- Audit trails must be immutable and cryptographically verifiable
- Session tokens expire after 24 hours (configurable)
- Password requirements: minimum 12 characters, complexity rules
- Rate limiting on API endpoints to prevent abuse

### Performance Constraints
- API response time: < 200ms for 95th percentile
- Document upload: Support files up to 50MB
- Concurrent users: Design for 10,000+ simultaneous users
- Email delivery: Queue-based for reliability and scalability

### Business Constraints
- Free tier: Limited envelopes per month
- Paid tiers: Unlimited envelopes with advanced features
- Document retention: Configurable by plan (7 years default)
- Branding: White-label support for enterprise customers

### Technical Constraints
- Database: PostgreSQL 14+ required
- Python: Version 3.11+ (if using Python)
- Node.js: Version 20+ (if using TypeScript)
- Browser support: Modern browsers (Chrome, Firefox, Safari, Edge - last 2 versions)

## External Dependencies

### Required Services
- **Email Service:** SMTP server or email API (SendGrid, AWS SES, Mailgun)
- **Object Storage:** AWS S3, MinIO, or S3-compatible service
- **Authentication (Optional):** OAuth providers (Google, Microsoft, GitHub)
- **Payment Processing (Future):** Stripe or similar for subscriptions
- **SMS (Optional):** Twilio or similar for OTP verification

### Third-Party Libraries
- **PDF Processing:** PyPDF2, pdfplumber (Python) or pdf-lib (JavaScript)
- **Document Generation:** ReportLab (Python) or jsPDF (JavaScript)
- **Encryption:** cryptography (Python) or crypto (Node.js)
- **JWT:** PyJWT (Python) or jsonwebtoken (Node.js)
- **Database ORM:** SQLAlchemy (Python) or Prisma/TypeORM (TypeScript)
- **Validation:** Pydantic (Python) or Zod (TypeScript)

### Development Tools
- **Linting:** Ruff/Black (Python) or ESLint/Prettier (TypeScript)
- **Type Checking:** mypy (Python) or tsc (TypeScript)
- **Testing:** pytest (Python) or Jest/Vitest (TypeScript)
- **API Documentation:** OpenAPI/Swagger
- **Container:** No container
