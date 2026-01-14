/**
 * E2E Test Utilities
 * Helper functions for common test operations
 */
import { Page, expect } from '@playwright/test';

export class TestHelpers {
  /**
   * Generate unique test user credentials
   */
  static generateTestUser() {
    const timestamp = Date.now();
    return {
      email: `test.user.${timestamp}@example.com`,
      password: 'TestPassword123!@#',
      firstName: 'Test',
      lastName: 'User',
      phone: '+1234567890',
    };
  }

  /**
   * Register a new user via the UI
   */
  static async registerUser(page: Page, user: ReturnType<typeof TestHelpers.generateTestUser>) {
    await page.goto('/register');
    await page.fill('input[name="email"]', user.email);
    await page.fill('input[name="password"]', user.password);
    await page.fill('input[name="confirmPassword"]', user.password);
    await page.fill('input[name="first_name"]', user.firstName);
    await page.fill('input[name="last_name"]', user.lastName);
    await page.fill('input[name="phone"]', user.phone);
    await page.click('button[type="submit"]');
  }

  /**
   * Login via the UI
   */
  static async login(page: Page, email: string, password: string) {
    await page.goto('/login');
    await page.fill('input[name="email"]', email);
    await page.fill('input[name="password"]', password);
    await page.click('button[type="submit"]');
  }

  /**
   * Login via API (faster for setup)
   */
  static async loginViaAPI(page: Page, email: string, password: string) {
    const response = await page.request.post('http://localhost:8000/api/v1/auth/login', {
      data: { email, password },
    });
    
    const data = await response.json();
    
    // Set tokens in localStorage
    await page.addInitScript((accessToken) => {
      localStorage.setItem('access_token', accessToken);
    }, data.access_token);
    
    if (data.refresh_token) {
      await page.addInitScript((refreshToken) => {
        localStorage.setItem('refresh_token', refreshToken);
      }, data.refresh_token);
    }
  }

  /**
   * Verify email via API (simulates clicking email link)
   */
  static async verifyEmailViaAPI(page: Page, userId: string) {
    // This would need the verification token from the database
    // For now, we'll update the user directly via SQL in tests
    // Or mock the email service
  }

  /**
   * Wait for navigation to complete
   */
  static async waitForNavigation(page: Page, url: string) {
    await page.waitForURL(url, { timeout: 5000 });
  }

  /**
   * Check if user is logged in
   */
  static async isLoggedIn(page: Page): Promise<boolean> {
    await page.goto('/dashboard');
    return page.url().includes('/dashboard');
  }

  /**
   * Logout
   */
  static async logout(page: Page) {
    await page.click('button:has-text("Logout")');
  }

  /**
   * Take a screenshot with a descriptive name
   */
  static async screenshot(page: Page, name: string) {
    await page.screenshot({ path: `screenshots/${name}.png`, fullPage: true });
  }

  /**
   * Upload a document via UI
   */
  static async uploadDocument(page: Page, filePath: string, customName?: string) {
    // Click upload button
    await page.click('button:has-text("Upload")');
    
    // Select file
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(filePath);
    
    // Optionally enter custom name
    if (customName) {
      await page.locator('input[id="document-name"]').fill(customName);
    }
    
    // Submit upload
    await page.click('button:has-text("Upload Document")');
    
    // Wait for success
    await page.waitForSelector('text=/uploaded successfully/i', { timeout: 10000 });
  }

  /**
   * Navigate to documents page
   */
  static async goToDocuments(page: Page) {
    await page.goto('/documents');
    await expect(page).toHaveURL('/documents');
  }

  /**
   * Wait for document to appear in list
   */
  static async waitForDocumentInList(page: Page, documentName: string) {
    await page.click('button:has-text("My Documents")');
    await expect(page.locator(`text=${documentName}`).first()).toBeVisible({ timeout: 5000 });
  }

  /**
   * Delete a document by name
   */
  static async deleteDocument(page: Page, documentName: string, confirm = true) {
    // Find the document card
    const documentCard = page.locator(`text=${documentName}`).first().locator('xpath=ancestor::div[contains(@class, "rounded")]');
    
    // Click delete button
    const deleteButton = documentCard.locator('button[title="Delete"]');
    
    // Handle confirmation dialog
    if (confirm) {
      page.once('dialog', dialog => dialog.accept());
    } else {
      page.once('dialog', dialog => dialog.dismiss());
    }
    
    await deleteButton.click();
    
    // Wait for deletion to complete
    if (confirm) {
      await page.waitForTimeout(1000);
    }
  }

  /**
   * Search for documents
   */
  static async searchDocuments(page: Page, searchTerm: string) {
    const searchInput = page.locator('input[placeholder*="Search"]');
    await searchInput.fill(searchTerm);
    await page.waitForTimeout(500); // Debounce
  }

  /**
   * Clear authentication tokens
   */
  static async clearAuth(page: Page) {
    await page.evaluate(() => {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    });
  }
}
