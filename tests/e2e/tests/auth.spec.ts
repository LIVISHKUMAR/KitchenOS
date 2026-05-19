import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test('should show login page', async ({ page }) => {
    await page.goto('/');

    // Should have login form
    const emailInput = page.locator('input[type="email"]');
    const passwordInput = page.locator('input[type="password"]');
    const submitBtn = page.locator('button[type="submit"]');

    await expect(emailInput).toBeVisible();
    await expect(passwordInput).toBeVisible();
    await expect(submitBtn).toBeVisible();
  });

  test('should login with valid credentials', async ({ page }) => {
    await page.goto('/');

    await page.locator('input[type="email"]').fill('admin@demo.com');
    await page.locator('input[type="password"]').fill('password123');
    await page.locator('button[type="submit"]').click();

    // Should redirect to POS
    await page.waitForURL('/', { timeout: 10000 });
    await expect(page.locator('[data-testid="menu-grid"]')).toBeVisible();
  });

  test('should show error for invalid credentials', async ({ page }) => {
    await page.goto('/');

    await page.locator('input[type="email"]').fill('wrong@email.com');
    await page.locator('input[type="password"]').fill('wrongpass');
    await page.locator('button[type="submit"]').click();

    // Should show error
    const error = page.locator('[data-testid="login-error"]');
    await expect(error).toBeVisible();
  });

  test('should logout', async ({ page }) => {
    // Login first
    await page.goto('/');
    await page.locator('input[type="email"]').fill('admin@demo.com');
    await page.locator('input[type="password"]').fill('password123');
    await page.locator('button[type="submit"]').click();
    await page.waitForURL('/');

    // Logout
    await page.locator('[data-testid="logout-btn"]').click();

    // Should redirect to login
    await expect(page.locator('input[type="email"]')).toBeVisible();
  });
});
