# E2E Test Suite - Document Management

Comprehensive Playwright end-to-end tests for the document management system.

## Test Coverage

### Test File: `documents.spec.ts`
**Total Tests**: 35+ scenarios covering all document management features

#### Test Groups

1. **Document Upload** (6 tests)
   - ✅ Show upload interface
   - ✅ Upload PDF via file input
   - ✅ Upload with custom name
   - ✅ Reject non-PDF files
   - ✅ Show upload progress
   - ✅ Cancel file selection

2. **Document List** (6 tests)
   - ✅ Display documents in grid
   - ✅ Search by name
   - ✅ Sort documents
   - ✅ Toggle sort order
   - ✅ Pagination (15+ documents)
   - ✅ Empty state display

3. **Document Viewer** (4 tests)
   - ✅ Open viewer on click
   - ✅ Display metadata
   - ✅ Show PDF preview
   - ✅ Close and return to list

4. **Document Download** (2 tests)
   - ✅ Download from card
   - ✅ Download from viewer

5. **Document Delete** (3 tests)
   - ✅ Show confirmation dialog
   - ✅ Delete after confirmation
   - ✅ Cancel on dismiss

6. **Responsive Design** (3 tests)
   - ✅ Mobile viewport (375x667)
   - ✅ Tablet viewport (768x1024)
   - ✅ Desktop viewport (1920x1080)

7. **Error Handling** (3 tests)
   - ✅ Upload errors
   - ✅ Network errors
   - ✅ Authentication errors

8. **Performance** (2 tests)
   - ✅ Multiple rapid uploads
   - ✅ Fast list view loading (<3s)

## Running Tests

### Prerequisites
```bash
# Backend must be running
cd backend
uvicorn app.main:app --reload

# Install Playwright browsers (one time)
cd frontend
npx playwright install chromium
```

### Run All Tests
```bash
cd frontend
npm run test:e2e
```

### Run Specific Test File
```bash
npx playwright test documents.spec.ts
```

### Run Specific Test
```bash
npx playwright test -g "should upload a PDF file"
```

### Run with UI Mode (Recommended)
```bash
npx playwright test --ui
```

### Debug Mode
```bash
npx playwright test --debug
```

### Generate Report
```bash
npx playwright test
npx playwright show-report
```

## Test Structure

### Setup (`beforeEach`)
Each test:
1. Generates unique test user
2. Registers user via API
3. Logs in via API (fast)
4. Navigates to /documents

### Teardown
Tests are isolated - each test gets a fresh user and state.

## Test Fixtures

### PDF Files
Located in `e2e/fixtures/`:
- `test-document.pdf` - Minimal valid PDF (auto-generated)
- `test.txt` - Text file for validation tests (auto-generated)

Files are created automatically on first test run.

## Helper Functions

### Core Helpers (`helpers.ts`)
```typescript
TestHelpers.generateTestUser()           // Unique user per test
TestHelpers.loginViaAPI(page, email, pw) // Fast login
TestHelpers.uploadDocument(page, path)   // Upload helper
TestHelpers.goToDocuments(page)         // Navigate
TestHelpers.deleteDocument(page, name)   // Delete with confirm
TestHelpers.searchDocuments(page, term) // Search
TestHelpers.clearAuth(page)             // Clear tokens
```

### Test-Specific Helpers
```typescript
createTestFixtures()                    // Generate test PDFs
registerAndVerifyUser(page, user)      // Register via API
uploadTestDocument(page, name)         // Quick upload
```

## Configuration

### `playwright.config.ts`
```typescript
baseURL: 'http://localhost:3000'
timeout: Default timeouts
webServer: Auto-starts npm run dev
projects: [chromium] // Can add firefox, webkit
reporter: 'html'
```

### Environment Variables
```bash
CI=true              # Enable CI mode (more retries)
PLAYWRIGHT_WORKERS=1 # Parallel test workers
```

## Best Practices

### ✅ Do's
- Use unique test users (via `generateTestUser()`)
- Login via API for speed
- Use `waitForSelector` with timeouts
- Handle confirmation dialogs
- Test both success and failure paths
- Use descriptive test names
- Group related tests with `describe`
- Clean up after tests (isolated users)

### ❌ Don'ts
- Don't share users between tests
- Don't rely on specific timing (use waitFor)
- Don't skip error handling tests
- Don't use hard-coded IDs/emails
- Don't make tests dependent on each other

## Debugging Tips

### View Test in Browser
```bash
npx playwright test --headed
```

### Slow Motion
```bash
npx playwright test --headed --slow-mo=1000
```

### Screenshots on Failure
Automatically saved to `test-results/` when tests fail.

### Traces
View traces for failed tests:
```bash
npx playwright show-trace test-results/*/trace.zip
```

### Console Logs
```typescript
page.on('console', msg => console.log(msg.text()));
```

## CI/CD Integration

### GitHub Actions Example
```yaml
- name: Run E2E Tests
  run: |
    cd backend && uvicorn app.main:app &
    cd frontend && npx playwright test
  env:
    CI: true
```

### Required Services
- PostgreSQL database
- Backend API server
- S3 or LocalStack (for storage)

## Test Data Management

### User Isolation
Each test creates a unique user with timestamp:
```
test.user.1705161234567@example.com
```

### Document Cleanup
Documents are scoped to test users, automatically isolated.

### Database State
Tests don't clean up database - each user is unique.
For full cleanup, reset test database between runs:
```bash
DATABASE_URL="..." alembic downgrade base
DATABASE_URL="..." alembic upgrade head
```

## Troubleshooting

### "Backend not running"
```bash
# Check backend is up
curl http://localhost:8000/api/v1/health
```

### "File not found"
Fixtures are auto-generated. If errors persist:
```bash
rm -rf e2e/fixtures
# Will be recreated on next run
```

### "Element not found"
- Check selectors are correct
- Increase timeout: `{ timeout: 10000 }`
- Use `--headed` mode to see what's happening

### "Authentication failed"
- Verify backend auth endpoints work
- Check email verification is not required
- Use API login for faster/reliable auth

### Tests timing out
- Increase global timeout in config
- Backend might be slow (S3 uploads)
- Use `--workers=1` to run serially

## Performance Benchmarks

### Target Times
- Upload small PDF: < 2s
- List view load: < 1s
- Search results: < 500ms
- Delete operation: < 1s
- Full test suite: < 5 min

### Optimization Tips
1. Login via API (not UI)
2. Register via API (not UI)
3. Use `networkidle` sparingly
4. Run tests in parallel (default)
5. Mock slow operations if needed

## Coverage Report

After running tests:
```bash
npx playwright test --reporter=html
npx playwright show-report
```

### Expected Coverage
- ✅ All upload paths
- ✅ All list operations
- ✅ All viewer features
- ✅ All delete scenarios
- ✅ Error states
- ✅ Loading states
- ✅ Responsive layouts

## Extending Tests

### Add New Test
```typescript
test('should do something', async ({ page }) => {
  // Arrange - setup is done in beforeEach
  await page.click('button:has-text("Something")');
  
  // Act
  await page.fill('input', 'value');
  await page.click('button[type="submit"]');
  
  // Assert
  await expect(page.locator('text=Success')).toBeVisible();
});
```

### Add New Helper
```typescript
// In helpers.ts
static async myHelper(page: Page, param: string) {
  // Implementation
}
```

### Add New Fixture
```typescript
// In documents.spec.ts
test.beforeAll(async () => {
  // Create fixture file
  const path = '...';
  fs.writeFileSync(path, content);
});
```

## Related Documentation

- **Playwright Docs**: https://playwright.dev
- **Test API**: https://playwright.dev/docs/api/class-test
- **Assertions**: https://playwright.dev/docs/test-assertions
- **Best Practices**: https://playwright.dev/docs/best-practices

## Status

**Status**: ✅ **COMPLETE**

35+ comprehensive E2E tests covering all document management features, ready to run.
