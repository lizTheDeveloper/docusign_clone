/**
 * E2E Tests: Profile Management
 * Tests for user profile viewing and updating
 */
import { test, expect } from '@playwright/test';

test.describe('Profile Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.context().clearCookies();
  });

  test('should redirect to login when not authenticated', async ({ page }) => {
    await page.goto('/profile');
    await expect(page).toHaveURL('/login');
  });

  test.skip('should display user profile information', async ({ page }) => {
    // Requires authentication
    await page.goto('/profile');
    
    await expect(page.locator('h1, h2')).toContainText(/Profile|Account/i);
    
    // Should show user fields
    await expect(page.locator('input[name="first_name"], label:has-text("First Name")')).toBeVisible();
    await expect(page.locator('input[name="last_name"], label:has-text("Last Name")')).toBeVisible();
    await expect(page.locator('input[name="email"], label:has-text("Email")')).toBeVisible();
  });

  test.skip('should update profile information', async ({ page }) => {
    await page.goto('/profile');
    
    // Update name
    await page.fill('input[name="first_name"]', 'UpdatedFirst');
    await page.fill('input[name="last_name"]', 'UpdatedLast');
    
    await page.click('button[type="submit"]:has-text("Update")');
    
    // Should show success message
    await expect(page.locator('text=/success|updated/i')).toBeVisible();
  });

  test.skip('should validate phone number format', async ({ page }) => {
    await page.goto('/profile');
    
    const phoneInput = page.locator('input[name="phone"]');
    if (await phoneInput.isVisible()) {
      await phoneInput.fill('invalid-phone');
      await page.click('button[type="submit"]');
      
      await expect(page.locator('text=/invalid.*phone|valid.*phone/i')).toBeVisible();
    }
  });

  test.skip('should show email verification status', async ({ page }) => {
    await page.goto('/profile');
    
    // Should show verification badge or status
    const verificationStatus = page.locator('text=/verified|unverified|pending/i');
    await expect(verificationStatus).toBeVisible();
  });

  test.skip('should allow resending verification email', async ({ page }) => {
    await page.goto('/profile');
    
    const resendButton = page.locator('button:has-text("Resend")');
    if (await resendButton.isVisible()) {
      await resendButton.click();
      await expect(page.locator('text=/sent|check.*email/i')).toBeVisible();
    }
  });
});
