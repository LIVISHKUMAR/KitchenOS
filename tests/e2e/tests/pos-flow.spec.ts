import { test, expect } from '@playwright/test';

test.describe('POS Billing Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('/');
    // If login page, fill credentials
    const emailInput = page.locator('input[type="email"]');
    if (await emailInput.isVisible()) {
      await emailInput.fill('admin@demo.com');
      await page.locator('input[type="password"]').fill('password123');
      await page.locator('button[type="submit"]').click();
      await page.waitForURL('/');
    }
  });

  test('should display menu items', async ({ page }) => {
    // Wait for menu to load
    await page.waitForSelector('[data-testid="menu-grid"]', { timeout: 10000 });

    // Should have menu items
    const items = page.locator('[data-testid="menu-item"]');
    await expect(items.first()).toBeVisible();
  });

  test('should add item to cart', async ({ page }) => {
    await page.waitForSelector('[data-testid="menu-item"]', { timeout: 10000 });

    // Click first menu item
    await page.locator('[data-testid="menu-item"]').first().click();

    // Cart should show 1 item
    const cartCount = page.locator('[data-testid="cart-count"]');
    await expect(cartCount).toContainText('1');
  });

  test('should complete billing flow', async ({ page }) => {
    await page.waitForSelector('[data-testid="menu-item"]', { timeout: 10000 });

    // Add 2 items
    await page.locator('[data-testid="menu-item"]').first().click();
    await page.locator('[data-testid="menu-item"]').nth(1).click();

    // Cart should show 2 items
    const cartCount = page.locator('[data-testid="cart-count"]');
    await expect(cartCount).toContainText('2');

    // Click checkout
    await page.locator('[data-testid="checkout-btn"]').click();

    // Payment modal should appear
    const paymentModal = page.locator('[data-testid="payment-modal"]');
    await expect(paymentModal).toBeVisible();

    // Select cash payment
    await page.locator('[data-testid="pay-cash"]').click();

    // Should show success
    await expect(page.locator('[data-testid="order-success"]')).toBeVisible({ timeout: 10000 });
  });

  test('should handle table selection', async ({ page }) => {
    await page.waitForSelector('[data-testid="table-btn"]', { timeout: 10000 });

    // Click a table
    await page.locator('[data-testid="table-btn"]').first().click();

    // Table should be selected
    const selectedTable = page.locator('[data-testid="selected-table"]');
    await expect(selectedTable).toBeVisible();
  });

  test('should search menu items', async ({ page }) => {
    await page.waitForSelector('[data-testid="menu-search"]', { timeout: 10000 });

    // Search for "pizza"
    await page.locator('[data-testid="menu-search"]').fill('pizza');

    // Should filter items
    const items = page.locator('[data-testid="menu-item"]');
    const count = await items.count();
    expect(count).toBeLessThanOrEqual(5);
  });

  test('should update item quantity', async ({ page }) => {
    await page.waitForSelector('[data-testid="menu-item"]', { timeout: 10000 });

    // Add item
    await page.locator('[data-testid="menu-item"]').first().click();

    // Increase quantity
    await page.locator('[data-testid="qty-increase"]').first().click();

    // Quantity should be 2
    const qty = page.locator('[data-testid="item-quantity"]').first();
    await expect(qty).toContainText('2');
  });

  test('should remove item from cart', async ({ page }) => {
    await page.waitForSelector('[data-testid="menu-item"]', { timeout: 10000 });

    // Add item
    await page.locator('[data-testid="menu-item"]').first().click();

    // Remove item
    await page.locator('[data-testid="remove-item"]').first().click();

    // Cart should be empty
    const emptyCart = page.locator('[data-testid="empty-cart"]');
    await expect(emptyCart).toBeVisible();
  });
});
