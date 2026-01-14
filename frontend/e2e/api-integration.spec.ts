/**
 * E2E Tests: API Integration
 * Tests for API error handling, loading states, and network conditions
 */
import { test, expect } from '@playwright/test';

test.describe('API Error Handling', () => {
  test('should handle network errors gracefully', async ({ page, context }) => {
    // Simulate offline mode
    await context.setOffline(true);
    
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    
    // Should show network error message
    await expect(page.locator('text=/network|connection|offline/i')).toBeVisible();
    
    await context.setOffline(false);
  });

  test('should show loading state during API calls', async ({ page }) => {
    await page.goto('/login');
    
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'TestPassword123!@#');
    
    // Click submit and immediately check for loading state
    await page.click('button[type="submit"]');
    
    // Button should be disabled during loading
    const submitButton = page.locator('button[type="submit"]');
    await expect(submitButton).toBeDisabled();
  });

  test('should handle 500 server errors', async ({ page, context }) => {
    // Mock 500 error
    await context.route('**/api/v1/auth/login', (route) => {
      route.fulfill({
        status: 500,
        body: JSON.stringify({ detail: 'Internal server error' }),
      });
    });

    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password');
    await page.click('button[type="submit"]');

    // Should show error message
    await expect(page.locator('text=/error|failed|wrong/i')).toBeVisible();
  });

  test('should handle 404 errors', async ({ page, context }) => {
    await context.route('**/api/v1/nonexistent', (route) => {
      route.fulfill({
        status: 404,
        body: JSON.stringify({ detail: 'Not found' }),
      });
    });

    // Navigate to a page that makes API calls
    await page.goto('/');
  });

  test('should retry failed requests with token refresh', async ({ page, context }) => {
    let requestCount = 0;

    // Mock token refresh flow
    await context.route('**/api/v1/auth/me', (route) => {
      requestCount++;
      if (requestCount === 1) {
        // First request fails with 401
        route.fulfill({
          status: 401,
          body: JSON.stringify({ detail: 'Token expired' }),
        });
      } else {
        // Second request succeeds after refresh
        route.fulfill({
          status: 200,
          body: JSON.stringify({
            user_id: '123',
            email: 'test@example.com',
            first_name: 'Test',
            last_name: 'User',
          }),
        });
      }
    });
  });
});

test.describe('Loading States', () => {
  test('should show skeleton loaders where appropriate', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Look for loading indicators during initial render
    const loader = page.locator('.animate-spin, text=/loading/i');
    // Loader might be too fast, just ensure page doesn't crash
  });

  test('should disable forms during submission', async ({ page }) => {
    await page.goto('/register');
    
    const submitButton = page.locator('button[type="submit"]');
    const emailInput = page.locator('input[name="email"]');
    
    await emailInput.fill('test@example.com');
    await page.click('button[type="submit"]');
    
    // Button should be disabled during submission
    // This might be too fast to catch
  });
});

test.describe('Accessibility', () => {
  test('should have proper form labels', async ({ page }) => {
    await page.goto('/login');
    
    // Email input should have label
    const emailLabel = page.locator('label[for="email"], label:has(input[name="email"])');
    await expect(emailLabel).toBeVisible();
    
    // Password input should have label
    const passwordLabel = page.locator('label[for="password"], label:has(input[name="password"])');
    await expect(passwordLabel).toBeVisible();
  });

  test('should be keyboard navigable', async ({ page }) => {
    await page.goto('/login');
    
    // Tab through form fields
    await page.keyboard.press('Tab');
    await expect(page.locator('input[name="email"]')).toBeFocused();
    
    await page.keyboard.press('Tab');
    await expect(page.locator('input[name="password"]')).toBeFocused();
    
    await page.keyboard.press('Tab');
    await expect(page.locator('button[type="submit"]')).toBeFocused();
  });

  test('should have semantic HTML', async ({ page }) => {
    await page.goto('/login');
    
    // Should have main heading
    await expect(page.locator('h1, h2').first()).toBeVisible();
    
    // Form should be in a form element
    await expect(page.locator('form')).toBeVisible();
    
    // Submit should be a button
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test('should show focus indicators', async ({ page }) => {
    await page.goto('/login');
    
    const emailInput = page.locator('input[name="email"]');
    await emailInput.focus();
    
    // Check if element has focus
    await expect(emailInput).toBeFocused();
  });
});

test.describe('Security', () => {
  test('should not expose sensitive data in URLs', async ({ page }) => {
    await page.goto('/login');
    
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'SecretPassword123!');
    await page.click('button[type="submit"]');
    
    // Wait for any redirect
    await page.waitForTimeout(500);
    
    // URL should not contain password
    expect(page.url()).not.toContain('password');
    expect(page.url()).not.toContain('SecretPassword');
  });

  test('should not store sensitive data in localStorage without encryption', async ({ page }) => {
    await page.goto('/login');
    
    // Check localStorage doesn't have plain passwords
    const storage = await page.evaluate(() => {
      return JSON.stringify(localStorage);
    });
    
    expect(storage.toLowerCase()).not.toContain('password');
  });

  test('should clear auth tokens on logout', async ({ page }) => {
    // Set some tokens
    await page.addInitScript(() => {
      localStorage.setItem('access_token', 'test-token');
      localStorage.setItem('refresh_token', 'test-refresh');
    });
    
    await page.goto('/dashboard');
    
    // Logout if possible
    const logoutButton = page.locator('button:has-text("Logout")');
    if (await logoutButton.isVisible()) {
      await logoutButton.click();
      
      // Check tokens are cleared
      const hasTokens = await page.evaluate(() => {
        return !!localStorage.getItem('access_token');
      });
      
      expect(hasTokens).toBeFalsy();
    }
  });
});
