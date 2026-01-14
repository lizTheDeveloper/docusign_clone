/**
 * E2E Tests: Document Management
 * Tests for uploading, viewing, downloading, and deleting documents
 */
import { test, expect, Page } from '@playwright/test';
import { TestHelpers } from './helpers';
import * as path from 'path';
import * as fs from 'fs';
import { fileURLToPath } from 'url';

// ES module alternative to __dirname
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Test fixtures
const TEST_PDF_PATH = path.join(__dirname, 'fixtures', 'test-document.pdf');
const LARGE_PDF_PATH = path.join(__dirname, 'fixtures', 'large-document.pdf');

test.describe('Document Management', () => {
    let testUser: ReturnType<typeof TestHelpers.generateTestUser>;

    test.beforeAll(async () => {
        // Create test PDF files if they don't exist
        await createTestFixtures();
    });

    test.beforeEach(async ({ page }) => {
        // Generate unique test user for each test
        testUser = TestHelpers.generateTestUser();

        // Register and login via API (faster setup)
        await registerAndVerifyUser(page, testUser);
        await TestHelpers.loginViaAPI(page, testUser.email, testUser.password);

        // Navigate to documents page
        await page.goto('/documents');
        await expect(page).toHaveURL('/documents');
    });

    test.describe('Document Upload', () => {
        test('should show upload interface', async ({ page }) => {
            // Click upload button/tab
            await page.click('button:has-text("Upload")');

            // Should show drag & drop area or file input
            const uploadArea = page.locator('text=/drag and drop|click to upload/i');
            await expect(uploadArea).toBeVisible();
        });

        test('should upload a PDF file via file input', async ({ page }) => {
            await page.click('button:has-text("Upload")');

            // Upload file via input
            const fileInput = page.locator('input[type="file"]');
            await fileInput.setInputFiles(TEST_PDF_PATH);

            // Should show file selected
            await expect(page.locator('text=/test-document.pdf/i')).toBeVisible();

            // Click upload button
            await page.click('button:has-text("Upload Document")');

            // Should show success message
            await expect(page.locator('text=/uploaded successfully|upload complete/i')).toBeVisible({ timeout: 10000 });

            // Should redirect to list view
            await page.waitForTimeout(1000);
            await expect(page.locator('text=/My Documents|Document List/i')).toBeVisible();

            // Should see the uploaded document in the list
            await expect(page.locator('text=test-document')).toBeVisible();
        });

        test('should upload PDF with custom name', async ({ page }) => {
            await page.click('button:has-text("Upload")');

            const fileInput = page.locator('input[type="file"]');
            await fileInput.setInputFiles(TEST_PDF_PATH);

            // Enter custom name
            const nameInput = page.locator('input[id="document-name"]');
            await nameInput.fill('My Custom Document Name');

            await page.click('button:has-text("Upload Document")');

            // Wait for success
            await expect(page.locator('text=/uploaded successfully/i')).toBeVisible({ timeout: 10000 });

            // Should see custom name in list
            await expect(page.locator('text=My Custom Document Name')).toBeVisible();
        });

        test('should reject non-PDF files', async ({ page }) => {
            await page.click('button:has-text("Upload")');

            // Try to upload a text file
            const textFilePath = path.join(__dirname, 'fixtures', 'test.txt');
            if (!fs.existsSync(textFilePath)) {
                fs.writeFileSync(textFilePath, 'This is a test file');
            }

            const fileInput = page.locator('input[type="file"]');
            await fileInput.setInputFiles(textFilePath);

            // Should show error message
            await expect(page.locator('text=/only pdf files|pdf only/i')).toBeVisible();
        });

        test('should show upload progress', async ({ page }) => {
            await page.click('button:has-text("Upload")');

            const fileInput = page.locator('input[type="file"]');
            await fileInput.setInputFiles(TEST_PDF_PATH);

            await page.click('button:has-text("Upload Document")');

            // Should show progress indicator
            await expect(page.locator('text=/uploading|progress/i')).toBeVisible();
        });

        test('should allow canceling file selection', async ({ page }) => {
            await page.click('button:has-text("Upload")');

            const fileInput = page.locator('input[type="file"]');
            await fileInput.setInputFiles(TEST_PDF_PATH);

            // Click cancel/close button
            const closeButton = page.locator('button[aria-label="Remove file"], button:has-text("×")').first();
            await closeButton.click();

            // Should clear the file
            await expect(page.locator('text=/drag and drop|click to upload/i')).toBeVisible();
        });
    });

    test.describe('Document List', () => {
        test.beforeEach(async ({ page }) => {
            // Upload a test document for list tests
            await uploadTestDocument(page, 'Test Document 1');
        });

        test('should display uploaded documents in grid', async ({ page }) => {
            await page.click('button:has-text("My Documents")');

            // Should show grid of documents
            const documentCard = page.locator('text=Test Document 1').first();
            await expect(documentCard).toBeVisible();

            // Should show metadata
            await expect(page.locator('text=/pages|MB|KB/i')).toBeVisible();
        });

        test('should search documents by name', async ({ page }) => {
            // Upload multiple documents
            await uploadTestDocument(page, 'Important Report');
            await uploadTestDocument(page, 'Unrelated Document');

            await page.click('button:has-text("My Documents")');

            // Type in search box
            const searchInput = page.locator('input[placeholder*="Search"]');
            await searchInput.fill('Important');

            // Should show only matching documents
            await expect(page.locator('text=Important Report')).toBeVisible();
            await expect(page.locator('text=Unrelated Document')).not.toBeVisible();
        });

        test('should sort documents', async ({ page }) => {
            // Upload multiple documents
            await uploadTestDocument(page, 'Alpha Document');
            await uploadTestDocument(page, 'Zeta Document');

            await page.click('button:has-text("My Documents")');

            // Change sort option
            const sortSelect = page.locator('select').first();
            await sortSelect.selectOption('name');

            // Should reorder documents
            await page.waitForTimeout(500);
            const firstDocument = page.locator('[class*="grid"] > div').first();
            await expect(firstDocument).toContainText(/Alpha|Test/i);
        });

        test('should toggle sort order', async ({ page }) => {
            await page.click('button:has-text("My Documents")');

            // Click sort direction button
            const sortButton = page.locator('button[title*="Sort"]').first();
            await sortButton.click();

            // Should change arrow direction
            await expect(sortButton).toContainText(/↑|↓/);
        });

        test('should paginate documents', async ({ page }) => {
            // Upload more than 12 documents to trigger pagination
            for (let i = 1; i <= 15; i++) {
                await uploadTestDocument(page, `Document ${i}`);
            }

            await page.click('button:has-text("My Documents")');

            // Should show pagination controls
            await expect(page.locator('text=/Page|Next|Previous/i')).toBeVisible();

            // Click next page
            await page.click('button:has-text("Next")');

            // Should show page 2
            await expect(page.locator('text=Page 2')).toBeVisible();
        });

        test('should show empty state when no documents', async ({ page }) => {
            // Start fresh without uploading documents
            await page.reload();
            await page.click('button:has-text("My Documents")');

            // Should show empty state message
            await expect(page.locator('text=/no documents|get started/i')).toBeVisible();
        });
    });

    test.describe('Document Viewer', () => {
        test.beforeEach(async ({ page }) => {
            await uploadTestDocument(page, 'Viewable Document');
            await page.click('button:has-text("My Documents")');
        });

        test('should open document viewer on click', async ({ page }) => {
            // Click on document card
            const documentCard = page.locator('text=Viewable Document').first();
            await documentCard.click();

            // Should show document viewer
            await expect(page.locator('text=Viewable Document').first()).toBeVisible();

            // Should show metadata
            await expect(page.locator('text=/pages|size|uploaded/i')).toBeVisible();
        });

        test('should display document metadata', async ({ page }) => {
            await page.locator('text=Viewable Document').first().click();

            // Should show all metadata fields
            await expect(page.locator('text=/Original Filename/i')).toBeVisible();
            await expect(page.locator('text=/File Type/i')).toBeVisible();
            await expect(page.locator('text=/Uploaded By/i')).toBeVisible();
            await expect(page.locator('text=/Checksum/i')).toBeVisible();
        });

        test('should show PDF preview when ready', async ({ page }) => {
            await page.locator('text=Viewable Document').first().click();

            // Wait for processing (if needed)
            await page.waitForTimeout(2000);

            // Should show preview or processing message
            const hasPreview = await page.locator('iframe').isVisible().catch(() => false);
            const isProcessing = await page.locator('text=/processing/i').isVisible().catch(() => false);

            expect(hasPreview || isProcessing).toBeTruthy();
        });

        test('should close viewer and return to list', async ({ page }) => {
            await page.locator('text=Viewable Document').first().click();

            // Click close button
            await page.click('button:has-text("Close")');

            // Should return to list view
            await expect(page.locator('text=/My Documents/i')).toBeVisible();
        });
    });

    test.describe('Document Download', () => {
        test.beforeEach(async ({ page }) => {
            await uploadTestDocument(page, 'Downloadable Document');
            await page.click('button:has-text("My Documents")');
        });

        test('should download document from card', async ({ page }) => {
            // Wait for download to start
            const downloadPromise = page.waitForEvent('download');

            // Click download button on card
            const downloadButton = page.locator('button[title="Download"]').first();
            await downloadButton.click();

            // Wait for download
            const download = await downloadPromise;

            // Verify download started
            expect(download).toBeTruthy();
            expect(download.suggestedFilename()).toContain('.pdf');
        });

        test('should download document from viewer', async ({ page }) => {
            // Open viewer
            await page.locator('text=Downloadable Document').first().click();

            // Wait for download
            const downloadPromise = page.waitForEvent('download');

            // Click download button in viewer
            await page.click('button:has-text("Download")');

            const download = await downloadPromise;
            expect(download).toBeTruthy();
        });
    });

    test.describe('Document Delete', () => {
        test.beforeEach(async ({ page }) => {
            await uploadTestDocument(page, 'Deletable Document');
            await page.click('button:has-text("My Documents")');
        });

        test('should show confirmation dialog before delete', async ({ page }) => {
            // Click delete button
            const deleteButton = page.locator('button[title="Delete"]').first();
            await deleteButton.click();

            // Should show confirmation dialog
            page.once('dialog', dialog => {
                expect(dialog.message()).toContain(/sure|delete|confirm/i);
            });
        });

        test('should delete document after confirmation', async ({ page }) => {
            // Handle confirmation dialog
            page.once('dialog', dialog => dialog.accept());

            // Click delete button
            const deleteButton = page.locator('button[title="Delete"]').first();
            await deleteButton.click();

            // Wait for deletion
            await page.waitForTimeout(1000);

            // Document should be removed from list
            await expect(page.locator('text=Deletable Document')).not.toBeVisible();
        });

        test('should cancel delete on dialog dismiss', async ({ page }) => {
            // Handle confirmation dialog - dismiss it
            page.once('dialog', dialog => dialog.dismiss());

            // Click delete button
            const deleteButton = page.locator('button[title="Delete"]').first();
            await deleteButton.click();

            // Wait a bit
            await page.waitForTimeout(500);

            // Document should still be visible
            await expect(page.locator('text=Deletable Document')).toBeVisible();
        });
    });

    test.describe('Responsive Design', () => {
        test.beforeEach(async ({ page }) => {
            await uploadTestDocument(page, 'Responsive Test');
            await page.click('button:has-text("My Documents")');
        });

        test('should work on mobile viewport', async ({ page }) => {
            // Set mobile viewport
            await page.setViewportSize({ width: 375, height: 667 });

            // Should show mobile layout
            await expect(page.locator('text=Responsive Test')).toBeVisible();

            // Should be able to interact
            await page.locator('text=Responsive Test').first().click();
            await expect(page.locator('text=/uploaded/i')).toBeVisible();
        });

        test('should work on tablet viewport', async ({ page }) => {
            await page.setViewportSize({ width: 768, height: 1024 });

            // Should adapt layout
            await expect(page.locator('text=Responsive Test')).toBeVisible();
        });

        test('should work on desktop viewport', async ({ page }) => {
            await page.setViewportSize({ width: 1920, height: 1080 });

            // Should show full desktop layout
            await expect(page.locator('text=Responsive Test')).toBeVisible();
        });
    });

    test.describe('Error Handling', () => {
        test('should handle upload errors gracefully', async ({ page }) => {
            await page.click('button:has-text("Upload")');

            // Mock a failing upload by intercepting API call
            await page.route('**/api/v1/documents', route => {
                route.fulfill({
                    status: 500,
                    body: JSON.stringify({ detail: 'Server error' }),
                });
            });

            const fileInput = page.locator('input[type="file"]');
            await fileInput.setInputFiles(TEST_PDF_PATH);
            await page.click('button:has-text("Upload Document")');

            // Should show error message
            await expect(page.locator('text=/error|failed/i')).toBeVisible({ timeout: 5000 });
        });

        test('should handle network errors', async ({ page }) => {
            // Simulate offline mode
            await page.context().setOffline(true);

            await page.click('button:has-text("Upload")');
            const fileInput = page.locator('input[type="file"]');
            await fileInput.setInputFiles(TEST_PDF_PATH);
            await page.click('button:has-text("Upload Document")');

            // Should show error
            await expect(page.locator('text=/error|failed|network/i')).toBeVisible({ timeout: 5000 });

            // Restore connection
            await page.context().setOffline(false);
        });

        test('should handle authentication errors', async ({ page }) => {
            // Clear auth tokens
            await page.evaluate(() => {
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
            });

            // Try to access documents
            await page.goto('/documents');

            // Should redirect to login
            await expect(page).toHaveURL(/\/login/);
        });
    });

    test.describe('Performance', () => {
        test('should handle multiple rapid uploads', async ({ page }) => {
            await page.click('button:has-text("Upload")');

            // Upload 3 files in quick succession
            for (let i = 1; i <= 3; i++) {
                const fileInput = page.locator('input[type="file"]');
                await fileInput.setInputFiles(TEST_PDF_PATH);
                await page.locator('input[id="document-name"]').fill(`Rapid Upload ${i}`);
                await page.click('button:has-text("Upload Document")');
                await page.waitForTimeout(500);
                await page.click('button:has-text("Upload")');
            }

            // All should eventually appear
            await page.click('button:has-text("My Documents")');
            await expect(page.locator('text=Rapid Upload 1')).toBeVisible();
        });

        test('should load list view quickly', async ({ page }) => {
            const startTime = Date.now();

            await page.click('button:has-text("My Documents")');
            await page.waitForLoadState('networkidle');

            const loadTime = Date.now() - startTime;

            // Should load in under 3 seconds
            expect(loadTime).toBeLessThan(3000);
        });
    });
});

// Helper Functions
async function createTestFixtures() {
    const fixturesDir = path.join(__dirname, 'fixtures');
    if (!fs.existsSync(fixturesDir)) {
        fs.mkdirSync(fixturesDir, { recursive: true });
    }

    // Create a minimal valid PDF
    if (!fs.existsSync(TEST_PDF_PATH)) {
        const pdfContent = `%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
>>
>>
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test Document) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000317 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
410
%%EOF`;
        fs.writeFileSync(TEST_PDF_PATH, pdfContent);
    }
}

async function registerAndVerifyUser(page: Page, user: ReturnType<typeof TestHelpers.generateTestUser>) {
    // Register via API
    const registerResponse = await page.request.post('http://localhost:8000/api/v1/auth/register', {
        data: {
            email: user.email,
            password: user.password,
            first_name: user.firstName,
            last_name: user.lastName,
            phone: user.phone,
        },
    });

    const registerData = await registerResponse.json();

    // Verify email via API (simulate clicking verification link)
    // In a real scenario, you'd extract the token from email or database
    // For now, we'll assume email verification is optional or handled differently
}

async function uploadTestDocument(page: Page, name: string) {
    await page.click('button:has-text("Upload")');

    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(TEST_PDF_PATH);

    await page.locator('input[id="document-name"]').fill(name);
    await page.click('button:has-text("Upload Document")');

    // Wait for success
    await page.waitForTimeout(2000);
}
