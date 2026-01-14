# Frontend - DocuSign Clone

Modern React + TypeScript frontend for the DocuSign Clone authentication system.

## Features

### ✅ Authentication Flows
- **User Registration** - Create account with email/password validation
- **Email Verification** - Required before login access
- **Login** - JWT-based authentication with auto token refresh
- **Forgot Password** - Email-based password reset flow
- **Reset Password** - Secure token-based password reset
- **User Profile** - View and update user information
- **Protected Routes** - Automatic redirect for unauthenticated users

### 🔐 Security Features
- Password validation (12+ chars, uppercase, lowercase, numbers)
- JWT token management with automatic refresh
- Secure token storage in localStorage
- CSRF protection ready
- Auto-logout on token expiration

### 🎨 UI/UX
- Tailwind CSS for styling
- Responsive design (mobile-first)
- Form validation with real-time feedback
- Loading states and error handling
- Success/error notifications

## Tech Stack

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **React Router** - Client-side routing
- **Axios** - HTTP client with interceptors
- **React Hook Form** - Form management
- **Zod** - Schema validation
- **Tailwind CSS** - Utility-first styling

## Getting Started

### Prerequisites
- Node.js 18+ and npm
- Backend API running on `http://localhost:8000`

### Installation

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.example .env

# Start development server
npm run dev
```

The app will be available at `http://localhost:3000`

### Available Scripts

```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run preview      # Preview production build
npm run lint         # Run ESLint
npm run test         # Run tests
npm run test:ui      # Run tests with UI
npm run test:coverage # Generate coverage report
```

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── auth/
│   │   │   ├── LoginForm.tsx          # Login component
│   │   │   ├── RegisterForm.tsx       # Registration component
│   │   │   ├── ForgotPasswordForm.tsx # Forgot password component
│   │   │   ├── ResetPasswordForm.tsx  # Reset password component
│   │   │   ├── VerifyEmail.tsx        # Email verification handler
│   │   │   └── ProtectedRoute.tsx     # Route guard component
│   │   └── profile/
│   │       └── UserProfile.tsx        # User profile management
│   ├── contexts/
│   │   └── AuthContext.tsx            # Authentication state management
│   ├── services/
│   │   └── auth.service.ts            # Authentication API calls
│   ├── types/
│   │   └── auth.ts                    # TypeScript type definitions
│   ├── lib/
│   │   └── api.ts                     # Axios instance with interceptors
│   ├── App.tsx                        # Main app component with routing
│   ├── main.tsx                       # Application entry point
│   └── index.css                      # Global styles
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

## Authentication Flow

### Registration Flow
1. User fills registration form
2. Form validates (email format, password strength)
3. API creates user account
4. Email verification sent
5. User redirected to login with success message

### Login Flow
1. User enters email/password
2. API validates credentials
3. JWT tokens returned (access + refresh)
4. Tokens stored in localStorage
5. User redirected to dashboard

### Token Refresh Flow
1. API request returns 401
2. Interceptor catches error
3. Refresh token sent to `/auth/refresh-token`
4. New tokens received and stored
5. Original request retried with new token
6. If refresh fails, user redirected to login

### Protected Routes
- Routes wrapped in `<ProtectedRoute />` check authentication
- Unauthenticated users redirected to `/login`
- Loading state shown during auth check

## API Integration

All API calls go through the configured Axios instance in `src/lib/api.ts`:

```typescript
// Automatic token attachment
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Automatic token refresh on 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Refresh token logic...
    }
  }
);
```

### API Endpoints Used

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/auth/register` | POST | Create new user |
| `/api/v1/auth/login` | POST | Authenticate user |
| `/api/v1/auth/logout` | POST | End user session |
| `/api/v1/auth/refresh-token` | POST | Refresh access token |
| `/api/v1/auth/me` | GET | Get current user |
| `/api/v1/auth/me` | PATCH | Update user profile |
| `/api/v1/auth/verify-email` | POST | Verify email token |
| `/api/v1/auth/resend-verification` | POST | Resend verification |
| `/api/v1/auth/forgot-password` | POST | Request password reset |
| `/api/v1/auth/reset-password` | POST | Reset password |

## Environment Variables

```bash
# Backend API base URL
VITE_API_BASE_URL=http://localhost:8000/api/v1

# Environment
VITE_ENVIRONMENT=development
```

## Form Validation

Forms use Zod schemas for validation:

```typescript
// Example: Password validation
const registerSchema = z.object({
  password: z.string()
    .min(12, 'Password must be at least 12 characters')
    .regex(/[A-Z]/, 'Must contain uppercase')
    .regex(/[a-z]/, 'Must contain lowercase')
    .regex(/[0-9]/, 'Must contain number'),
});
```

## State Management

Uses React Context API for authentication state:

```typescript
const { user, isAuthenticated, login, logout } = useAuth();
```

Available throughout the app via `useAuth()` hook.

## Error Handling

All API errors are caught and displayed to users:

```typescript
try {
  await login(email, password);
} catch (err) {
  const axiosError = err as AxiosError<ApiError>;
  setError(axiosError.response?.data?.detail || 'Login failed');
}
```

## Testing

```bash
# Run all tests
npm test

# Run tests with UI
npm run test:ui

# Generate coverage report
npm run test:coverage
```

## Production Build

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

## Integration with Backend

Ensure the backend is running on `http://localhost:8000` or update `VITE_API_BASE_URL` in `.env`.

The Vite dev server proxies `/api` requests to the backend automatically.

## Next Steps

1. **Install dependencies**: `npm install`
2. **Start backend**: Ensure backend is running on port 8000
3. **Start frontend**: `npm run dev`
4. **Test flows**: Register → Verify → Login → Profile

## Troubleshooting

### CORS Errors
- Ensure backend has CORS configured for `http://localhost:3000`
- Check backend CORS settings in `backend/app/config.py`

### Token Issues
- Clear localStorage: `localStorage.clear()`
- Check token expiration settings match backend
- Verify JWT_SECRET_KEY matches between frontend env and backend

### Form Validation
- Check Zod schema matches backend validation rules
- Password must be 12+ chars with uppercase, lowercase, numbers
- Email must be valid format

## Contributing

Follow the project's TypeScript and React conventions:
- Use functional components with hooks
- TypeScript strict mode enabled
- ESLint + Prettier for code formatting
- Component-based architecture
- Reusable service layer for API calls
