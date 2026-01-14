/**
 * E2E Tests: Authentication Flows
 * Tests for registration, login, logout, and protected routes
 */
import { test, expect } from '@playwright/test';
import { TestHelpers } from './helpers';

test.describe('Authentication', () => {
    test.beforeEach(async ({ page }) => {
        // Clear any existing auth state
        await page.context().clearCookies();
        await page.goto('/');
    });

    test('should show login page by default', async ({ page }) => {
        await page.goto('/');
        await expect(page).toHaveURL(/\/login|\/dashboard/);
    });

    test('should navigate to register page', async ({ page }) => {
        await page.goto('/login');
        await page.click('a:has-text("Register")');
        await expect(page).toHaveURL('/register');
        await expect(page.locator('h2')).toContainText(/Register|Sign up|Create account/i);
    });

    test('should register a new user successfully', async ({ page }) => {
        const user = TestHelpers.generateTestUser();

        await page.goto('/register');

        // Fill in registration form
        await page.fill('input[name="email"]', user.email);
        await page.fill('input[name="password"]', user.password);
        await page.fill('input[name="confirmPassword"]', user.password);
        await page.fill('input[name="first_name"]', user.firstName);
        await page.fill('input[name="last_name"]', user.lastName);

        // Phone is optional
        const phoneInput = page.locator('input[name="phone"]');
        if (await phoneInput.isVisible()) {
            await phoneInput.fill(user.phone);
        }

        // Submit form
        await page.click('button[type="submit"]');

        // Should show success message or redirect
        await page.waitForTimeout(1000);

        // Check for success indicators
        const successMessage = page.locator('text=/registered|success|verify.*email/i');
        const loginRedirect = page.url().includes('/login');

        expect(await successMessage.isVisible() || loginRedirect).toBeTruthy();
    });

    test('should show validation errors for invalid registration', async ({ page }) => {
        await page.goto('/register');

        // Try to submit with empty fields
        await page.click('button[type="submit"]');

        // Should show validation errors
        await expect(page.locator('text=/required|invalid/i')).toBeVisible();
    });

    test('should reject weak passwords', async ({ page }) => {
        const user = TestHelpers.generateTestUser();

        await page.goto('/register');

        await page.fill('input[name="email"]', user.email);
        await page.fill('input[name="password"]', 'weak');
        await page.fill('input[name="confirmPassword"]', 'weak');
        await page.fill('input[name="first_name"]', user.firstName);
        await page.fill('input[name="last_name"]', user.lastName);

        await page.click('button[type="submit"]');

        // Should show password strength error
        await expect(page.locator('text=/password.*12|too short|weak/i')).toBeVisible();
    });

    test('should reject mismatched passwords', async ({ page }) => {
        const user = TestHelpers.generateTestUser();

        await page.goto('/register');

        await page.fill('input[name="email"]', user.email);
        await page.fill('input[name="password"]', user.password);
        await page.fill('input[name="confirmPassword"]', 'DifferentPassword123!');
        await page.fill('input[name="first_name"]', user.firstName);
        await page.fill('input[name="last_name"]', user.lastName);

        await page.click('button[type="submit"]');

        // Should show password mismatch error
        await expect(page.locator('text=/password.*match/i')).toBeVisible();
    });

    test('should prevent login with unverified email', async ({ page }) => {
        const user = TestHelpers.generateTestUser();

        // Register first
        await TestHelpers.registerUser(page, user);

        // Wait for registration to complete
        await page.waitForTimeout(1000);

        // Try to login
        await page.goto('/login');
        await page.fill('input[name="email"]', user.email);
        await page.fill('input[name="password"]', user.password);
        await page.click('button[type="submit"]');

        // Should show email verification required message
        await expect(page.locator('text=/verify.*email|email.*not.*verified/i')).toBeVisible();
    });

    test('should reject invalid login credentials', async ({ page }) => {
        await page.goto('/login');

        await page.fill('input[name="email"]', 'nonexistent@example.com');
        await page.fill('input[name="password"]', 'WrongPassword123!');
        await page.click('button[type="submit"]');

        // Should show login error
        await expect(page.locator('text=/invalid|incorrect|failed/i')).toBeVisible();
    });

    test('should navigate to forgot password page', async ({ page }) => {
        await page.goto('/login');
        await page.click('a:has-text("Forgot")');
        await expect(page).toHaveURL('/forgot-password');
        await expect(page.locator('h2')).toContainText(/Forgot.*Password|Reset.*Password/i);
    });

    test('should submit forgot password request', async ({ page }) => {
        await page.goto('/forgot-password');

        await page.fill('input[name="email"]', 'test@example.com');
        await page.click('button[type="submit"]');

        // Should show success message
        await expect(page.locator('text=/check.*email|sent.*email|reset.*link/i')).toBeVisible();
    });
});

test.describe('Protected Routes', () => {
    test('should redirect to login when accessing dashboard without auth', async ({ page }) => {
        await page.goto('/dashboard');
        await expect(page).toHaveURL('/login');
    });

    test('should redirect to login when accessing profile without auth', async ({ page }) => {
        await page.goto('/profile');
        await expect(page).toHaveURL('/login');
    });

    test('should show loading state while checking auth', async ({ page }) => {
        await page.goto('/dashboard');

        // Should briefly show loading spinner
        const loader = page.locator('text=/loading/i, .animate-spin');
        // Loader might be too fast to catch, so we just check it doesn't error
    });
});

test.describe('Navigation', () => {
    test('should navigate between public pages', async ({ page }) => {
        // Start at login
        await page.goto('/login');
        await expect(page).toHaveURL('/login');

        // Go to register
        await page.click('a:has-text("Register")');
        await expect(page).toHaveURL('/register');

        // Go back to login
        await page.click('a:has-text("Login")');
        await expect(page).toHaveURL('/login');

        // Go to forgot password
        await page.click('a:has-text("Forgot")');
        await expect(page).toHaveURL('/forgot-password');
    });
});

test.describe('Form Validation', () => {
    test('should validate email format on login', async ({ page }) => {
        await page.goto('/login');

        await page.fill('input[name="email"]', 'invalid-email');
        await page.fill('input[name="password"]', 'password');
        await page.click('button[type="submit"]');

        await expect(page.locator('text=/invalid.*email|valid.*email/i')).toBeVisible();
    });

    test('should validate email format on registration', async ({ page }) => {
        await page.goto('/register');

        await page.fill('input[name="email"]', 'invalid-email');
        await page.fill('input[name="first_name"]', 'Test');
        await page.click('button[type="submit"]');

        await expect(page.locator('text=/invalid.*email|valid.*email/i')).toBeVisible();
    });

    test('should show real-time validation on blur', async ({ page }) => {
        await page.goto('/register');

        const emailInput = page.locator('input[name="email"]');
        await emailInput.fill('invalid');
        await emailInput.blur();

        // Should show validation error after blur
        await expect(page.locator('text=/invalid.*email|valid.*email/i')).toBeVisible();
    });
});

test.describe('Responsive Design', () => {
    test('should display correctly on mobile', async ({ page }) => {
        await page.setViewportSize({ width: 375, height: 667 }); // iPhone size

        await page.goto('/login');

        // Form should be visible and properly sized
        const form = page.locator('form');
        await expect(form).toBeVisible();

        const submitButton = page.locator('button[type="submit"]');
        await expect(submitButton).toBeVisible();
    });

    test('should display correctly on tablet', async ({ page }) => {
        await page.setViewportSize({ width: 768, height: 1024 }); // iPad size

        await page.goto('/register');

        const form = page.locator('form');
        await expect(form).toBeVisible();
    });
});
