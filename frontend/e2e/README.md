# E2E Tests

End-to-end tests using Playwright for the DocuSign Clone frontend.

## Running Tests

```bash
# Run all tests (headless)
npm run test:e2e

# Run with UI mode (interactive)
npm run test:e2e:ui

# Run with headed browser (see the browser)
npm run test:e2e:headed

# Debug mode
npm run test:e2e:debug

# View test report
npm run test:e2e:report
```

## Test Structure

- **auth.spec.ts** - Authentication flows (register, login, logout, validation)
- **dashboard.spec.ts** - Dashboard and navigation (requires auth)
- **profile.spec.ts** - Profile management
- **api-integration.spec.ts** - API error handling, loading states, security
- **smoke.spec.ts** - Quick smoke tests for core functionality

## Test Coverage

✅ **Authentication**
- User registration with validation
- Login/logout flows
- Password strength validation
- Email verification requirement
- Forgot password flow
- Form validation

✅ **Protected Routes**
- Redirect to login when unauthenticated
- Loading states during auth check
- Access control

✅ **Navigation**
- Public page navigation
- Authenticated navigation (with mock)
- Deep linking

✅ **API Integration**
- Network error handling
- Loading states
- 500/404 error handling
- Token refresh retry logic

✅ **Accessibility**
- Form labels and ARIA attributes
- Keyboard navigation
- Semantic HTML
- Focus indicators

✅ **Security**
- No sensitive data in URLs
- Token storage
- Logout clears tokens

✅ **Responsive Design**
- Mobile viewport (375x667)
- Tablet viewport (768x1024)
- Desktop

✅ **Performance**
- Page load times
- API call optimization
- Resource loading

## Prerequisites

Both backend and frontend servers must be running:

```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# Terminal 2: Frontend  
cd frontend
npm run dev
```

## Configuration

Tests are configured in `playwright.config.ts`:
- Base URL: http://localhost:3000
- Browser: Chromium (headless by default)
- Retries: 2 in CI, 0 locally
- Screenshots: On failure only
- Traces: On first retry

## Notes

- Tests marked with `.skip()` require a real authenticated user session
- Some tests use mocked API responses to test error handling
- Tests assume backend is running on http://localhost:8000
- Frontend dev server is automatically started if not running

## Adding New Tests

1. Create a new `.spec.ts` file in the `e2e/` directory
2. Import test helpers from `helpers.ts`
3. Use descriptive test names
4. Clean up test data after tests (use beforeEach/afterEach)
5. Use data-testid attributes for stable selectors

## CI/CD Integration

Add to GitHub Actions:

```yaml
- name: Install Playwright
  run: npx playwright install --with-deps

- name: Run E2E tests
  run: npm run test:e2e

- name: Upload test results
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: playwright-report
    path: playwright-report/
```
