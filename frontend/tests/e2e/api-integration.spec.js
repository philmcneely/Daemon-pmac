import { test, expect } from '@playwright/test';

test.describe('Frontend API Integration', () => {
  test('should handle complete API integration and error scenarios', async ({ page }) => {
    // TEST 1: SUCCESSFUL API CONNECTION
    await page.goto('/');
    await expect(page.locator('.loading-screen')).toBeVisible();
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 3000 });

    // Verify content loaded (either user selection or portfolio)
    const hasContent = await page.locator('#portfolio, .user-selection').count();
    expect(hasContent).toBeGreaterThan(0);

    // TEST 2: API ERROR HANDLING
    // Route API calls to simulate errors
    await page.route('**/api/v1/**', route => {
      route.abort('failed');
    });

    // Reload page to test error handling
    await page.reload();
    await page.waitForTimeout(2000); // Give error handling time

    // Should show some form of error state or fallback
    const hasErrorOrFallback = await page.locator('.error, .offline, #portfolio, .user-selection').count();
    expect(hasErrorOrFallback).toBeGreaterThan(0);

    // TEST 3: SLOW NETWORK SIMULATION
    await page.unroute('**/api/v1/**');
    await page.route('**/api/v1/**', async route => {
      await new Promise(resolve => setTimeout(resolve, 1000)); // 1 second delay
      route.continue();
    });

    await page.reload();
    await expect(page.locator('.loading-screen')).toBeVisible();
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 3000 });

    // TEST 4: PARTIAL API FAILURE
    await page.unroute('**/api/v1/**');
    await page.route('**/api/v1/system/**', route => route.abort('failed'));
    await page.route('**/api/v1/portfolio/**', route => route.continue());

    await page.reload();
    await page.waitForTimeout(2000);

    // Should still show some content even with partial failures
    const stillHasContent = await page.locator('#portfolio, .user-selection, .error').count();
    expect(stillHasContent).toBeGreaterThan(0);

    console.log('API integration tests completed successfully');
  });
});
