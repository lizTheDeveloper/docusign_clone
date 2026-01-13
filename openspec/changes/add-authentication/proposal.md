# Change: Add User Authentication and Account Management

## Why
Users need secure accounts to send and sign legal documents. Authentication ensures only authorized users can access documents, create envelopes, and perform legally binding actions. This is the foundation for all document workflows and security.

## What Changes
- User registration with email and password
- Secure login with JWT token-based authentication
- Password hashing with industry-standard algorithms (bcrypt/argon2)
- User profile management (name, email, phone)
- Email verification for new accounts
- Password reset functionality
- Session management with token expiration
- Role-based access control (sender, signer, admin)
- OAuth2 integration (optional for Google/Microsoft)

## Impact
- Affected specs: `authentication` (new)
- Affected code: 
  - New authentication API endpoints
  - User database schema and models
  - JWT middleware for protected routes
  - Email service for verification
- Dependencies: JWT library, bcrypt/argon2, database ORM
- Security: Foundation for all document access control

## Interface Definitions

**REST API Endpoints:** See [REST API Specification](../../specs/rest-api.md#authentication-endpoints)
- POST /auth/register
- POST /auth/login
- POST /auth/refresh
- POST /auth/verify-email
- POST /auth/forgot-password
- POST /auth/reset-password
- GET /users/me
- PATCH /users/me

**Database Schema:** See [Database Schema](../../specs/database-schema.md)
- Table: `users`
- Table: `email_verifications`
- Table: `password_resets`
- Table: `refresh_tokens`

**Data Models:** See [Data Models](../../specs/data-models.md#user-models)
- Type: `User`
- Type: `UserProfile`
- Type: `LoginRequest`
- Type: `LoginResponse`
- Type: `RegisterRequest`
- Type: `JWTPayload`

**Internal APIs:** See [Service Interfaces](../../specs/service-interfaces.md#auth-service-internal-apis)
- POST /internal/auth/validate-token
- POST /internal/auth/create-access-code
- POST /internal/auth/validate-access-code

**Events Published:** See [Event Bus](../../specs/event-bus.md#system-events)
- `user.registered`
- `user.verified`
- `user.password.reset`
- `user.account.locked`
