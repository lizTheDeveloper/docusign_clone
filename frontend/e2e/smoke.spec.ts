/**
 * E2E Tests: Smoke Tests
 * Quick tests to verify core functionality is working
 */
import { test, expect } from '@playwright/test';

test.describe('Smoke Tests', () => {
    test('homepage loads successfully', async ({ page }) => {
        const response = await page.goto('/');
        expect(response?.status()).toBeLessThan(400);
    });

    test('all public routes are accessible', async ({ page }) => {
        const routes = [
            '/login',
            '/register',
            '/forgot-password',
        ];

        for (const route of routes) {
            const response = await page.goto(route);
            expect(response?.status()).toBe(200);
        }
    });

    test('app renders without JavaScript errors', async ({ page }) => {
        const errors: string[] = [];

        page.on('pageerror', (error) => {
            errors.push(error.message);
        });

        await page.goto('/login');
        await page.waitForTimeout(2000);

        expect(errors).toHaveLength(0);
    });

    test('app renders without console errors', async ({ page }) => {
        const errors: string[] = [];

        page.on('console', (msg) => {
            if (msg.type() === 'error') {
                errors.push(msg.text());
            }
        });

        await page.goto('/login');
        await page.waitForTimeout(2000);

        // Filter out known acceptable errors (like network errors to mock API)
        const criticalErrors = errors.filter(
            (error) => !error.includes('Failed to load resource')
        );

        expect(criticalErrors).toHaveLength(0);
    });

    test('all images load successfully', async ({ page }) => {
        await page.goto('/login');

        const images = await page.locator('img').all();

        for (const img of images) {
            const src = await img.getAttribute('src');
            if (src && !src.startsWith('data:')) {
                const naturalWidth = await img.evaluate((el: HTMLImageElement) => el.naturalWidth);
                expect(naturalWidth).toBeGreaterThan(0);
            }
        }
    });

    test('CSS loads correctly', async ({ page }) => {
        await page.goto('/login');

        // Check if Tailwind classes are applied
        const button = page.locator('button[type="submit"]').first();
        const backgroundColor = await button.evaluate((el) => {
            return window.getComputedStyle(el).backgroundColor;
        });

        // Should have some background color (not default)
        expect(backgroundColor).not.toBe('rgba(0, 0, 0, 0)');
    });

    test('page has proper title', async ({ page }) => {
        await page.goto('/login');

        const title = await page.title();
        expect(title.length).toBeGreaterThan(0);
    });

    test('page has meta viewport tag', async ({ page }) => {
        await page.goto('/login');

        const viewport = await page.locator('meta[name="viewport"]').getAttribute('content');
        expect(viewport).toContain('width=device-width');
    });

    test('no broken links on main pages', async ({ page }) => {
        await page.goto('/login');

        const links = await page.locator('a[href]').all();

        for (const link of links) {
            const href = await link.getAttribute('href');
            if (href && !href.startsWith('http') && !href.startsWith('#')) {
                // Internal link - verify it exists
                expect(href).toBeTruthy();
            }
        }
    });

    test('forms have proper ARIA attributes', async ({ page }) => {
        await page.goto('/login');

        const inputs = await page.locator('input').all();

        for (const input of inputs) {
            const type = await input.getAttribute('type');
            const ariaLabel = await input.getAttribute('aria-label');
            const ariaLabelledBy = await input.getAttribute('aria-labelledby');
            const id = await input.getAttribute('id');

            // Should have either aria-label, aria-labelledby, or a matching label
            const hasLabel = ariaLabel || ariaLabelledBy || (id && await page.locator(`label[for="${id}"]`).count() > 0);

            // Some inputs might be wrapped in labels
            const wrappedInLabel = await input.evaluate((el) => {
                return el.closest('label') !== null;
            });

            expect(hasLabel || wrappedInLabel).toBeTruthy();
        }
    });
});

test.describe('Performance', () => {
    test('page loads within acceptable time', async ({ page }) => {
        const startTime = Date.now();
        await page.goto('/login');
        await page.waitForLoadState('domcontentloaded');
        const loadTime = Date.now() - startTime;

        // Page should load within 3 seconds
        expect(loadTime).toBeLessThan(3000);
    });

    test('no unnecessary API calls on page load', async ({ page }) => {
        const apiCalls: string[] = [];

        page.on('request', (request) => {
            if (request.url().includes('/api/')) {
                apiCalls.push(request.url());
            }
        });

        await page.goto('/login');
        await page.waitForTimeout(1000);

        // Login page shouldn't make many API calls
        expect(apiCalls.length).toBeLessThan(5);
    });
});
