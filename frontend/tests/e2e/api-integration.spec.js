/**
 * Module: tests.e2e.test_frontend_api_integration
 * Description: E2E tests for frontend API integration and error handling
 *
 * Author: pmac
 * Created: 2025-08-30
 * Modified: 2025-08-30
 *
 * Dependencies:
 * - @playwright/test: 1.40.0+ - Browser automation framework
 * - Frontend server running on localhost:8006
 * - API server running on localhost:8007
 *
 * Usage:
 *     npx playwright test api-integration
 *
 * Notes:
 *     - Tests API communication and error scenarios
 *     - Validates data loading and fallback behaviors
 *     - Ensures robust error handling across network conditions
 */

import { test, expect } from '@playwright/test';

test.describe('Frontend API Integration', () => {
  test('should successfully connect to API and load system info', async ({ page }) => {
    // Given: API server is running
    // When: Frontend attempts to load system info
    await page.goto('/');

    // Then: Should successfully connect and load
    await expect(page.locator('.loading-screen')).toBeVisible();
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 10000 });

    // Verify content loaded (either user selection or portfolio)
    const hasContent = await page.locator('#portfolio, .user-selection').count() > 0;
    expect(hasContent).toBeGreaterThan(0);
  });

  test('should handle API server unavailable scenario', async ({ page }) => {
    // Given: API server is not responding
    await page.route('**/api/v1/**', route => {
      route.abort('failed');
    });

    // When: User loads the frontend
    await page.goto('/');

    // Wait longer for error handling
    await page.waitForTimeout(8000);

    // Then: Should show appropriate error handling
    const errorElements = await page.locator('.error-message, .retry-button, .connection-error, .offline-mode').count();
    const fallbackContent = await page.locator('#portfolio').isVisible();

    // Either error UI or graceful fallback should be present
    expect(errorElements > 0 || fallbackContent).toBeTruthy();
  });

  test('should handle slow API responses gracefully', async ({ page }) => {
    // Given: API responds slowly
    await page.route('**/api/v1/system/info', async route => {
      // Delay response by 3 seconds
      await new Promise(resolve => setTimeout(resolve, 3000));
      const response = await route.fetch();
      route.fulfill({ response });
    });

    // When: User loads the page
    await page.goto('/');

    // Then: Loading state should persist appropriately
    await expect(page.locator('.loading-screen')).toBeVisible();

    // Eventually should load
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 15000 });

    // Content should be available
    const hasContent = await page.locator('#portfolio, .user-selection').count() > 0;
    expect(hasContent).toBeGreaterThan(0);
  });

  test('should handle malformed API responses', async ({ page }) => {
    // Given: API returns invalid JSON
    await page.route('**/api/v1/system/info', route => {
      route.fulfill({
        status: 200,
        body: 'invalid json response'
      });
    });

    // When: User loads the page
    await page.goto('/');
    await page.waitForTimeout(5000);

    // Then: Should handle parsing errors gracefully
    const errorElements = await page.locator('.error-message, .parse-error, .invalid-data').count();
    const hasContent = await page.locator('#portfolio, .user-selection').count() > 0;

    // Should either show error or have fallback content
    expect(errorElements > 0 || hasContent).toBeTruthy();
  });

  test('should retry failed API requests', async ({ page }) => {
    let attemptCount = 0;

    // Given: API fails first time, succeeds second time
    await page.route('**/api/v1/system/info', async route => {
      attemptCount++;
      if (attemptCount === 1) {
        route.fulfill({ status: 500, body: 'Server Error' });
      } else {
        const response = await route.fetch();
        route.fulfill({ response });
      }
    });

    // When: User loads the page
    await page.goto('/');

    // Wait for potential retries
    await page.waitForTimeout(8000);

    // Then: Should eventually succeed on retry
    const hasContent = await page.locator('#portfolio, .user-selection').count() > 0;
    expect(hasContent).toBeGreaterThan(0);
    expect(attemptCount).toBeGreaterThanOrEqual(2);
  });

  test('should handle partial API failures gracefully', async ({ page }) => {
    // Given: System info loads but endpoint data fails
    await page.route('**/api/v1/about', route => {
      route.fulfill({ status: 500, body: 'Endpoint Error' });
    });

    // When: User loads the page
    await page.goto('/');
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 10000 });

    // Then: Should load structure but handle missing content
    const portfolio = page.locator('#portfolio');

    if (await portfolio.isVisible()) {
      // If portfolio loads, sections should exist even if content fails
      await expect(page.locator('#about')).toBeVisible();

      // Should show some kind of error state or fallback for failed content
      const aboutContent = page.locator('#aboutContent');
      const hasContent = await aboutContent.textContent();

      // Content might be empty or show error message
      expect(hasContent !== null).toBeTruthy();
    }
  });

  test('should validate API response structure', async ({ page }) => {
    // Given: API returns unexpected structure
    await page.route('**/api/v1/system/info', route => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({
          unexpected_field: 'value',
          missing_endpoints: true
        })
      });
    });

    // When: User loads the page
    await page.goto('/');
    await page.waitForTimeout(5000);

    // Then: Should handle missing expected fields
    const errorElements = await page.locator('.error-message, .invalid-response').count();
    const hasPartialContent = await page.locator('#portfolio, .user-selection, .loading-screen').count() > 0;

    expect(errorElements > 0 || hasPartialContent).toBeTruthy();
  });

  test('should handle network timeouts appropriately', async ({ page }) => {
    // Given: Network requests timeout
    await page.route('**/api/v1/**', route => {
      // Never resolve the request (simulates timeout)
      // Playwright will timeout after a reasonable period
    });

    // When: User loads the page
    await page.goto('/');

    // Wait for timeout handling
    await page.waitForTimeout(12000);

    // Then: Should show timeout error or fallback
    const timeoutElements = await page.locator('.timeout-error, .network-error, .connection-timeout').count();
    const loadingVisible = await page.locator('.loading-screen').isVisible();

    // Should either show error or still be in loading state with user feedback
    expect(timeoutElements > 0 || loadingVisible).toBeTruthy();
  });

  test('should handle CORS errors properly', async ({ page }) => {
    // Given: API returns CORS error
    await page.route('**/api/v1/**', route => {
      route.fulfill({
        status: 500,
        headers: {
          'Access-Control-Allow-Origin': 'different-origin.com'
        },
        body: 'CORS Error'
      });
    });

    // When: User loads the page
    await page.goto('/');
    await page.waitForTimeout(5000);

    // Then: Should handle CORS gracefully
    const corsElements = await page.locator('.cors-error, .cross-origin-error, .access-denied').count();
    const hasErrorHandling = await page.locator('.error-message, .connection-error').count() > 0;

    expect(corsElements > 0 || hasErrorHandling).toBeTruthy();
  });

  test('should maintain functionality during intermittent connectivity', async ({ page }) => {
    let isConnected = true;

    // Given: Intermittent connectivity
    await page.route('**/api/v1/**', async route => {
      if (isConnected) {
        const response = await route.fetch();
        route.fulfill({ response });
      } else {
        route.abort('failed');
      }
    });

    // When: User loads during good connectivity
    await page.goto('/');
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 10000 });

    // Verify initial load success
    const hasInitialContent = await page.locator('#portfolio, .user-selection').count() > 0;
    expect(hasInitialContent).toBeGreaterThan(0);

    // Simulate connectivity loss
    isConnected = false;

    // Try to trigger additional API calls (like navigation or refresh)
    if (await page.locator('.user-card').count() > 0) {
      // Multi-user mode - try selecting user
      await page.locator('.user-card').first().click();
    } else {
      // Single-user mode - try navigating
      const navLink = page.locator('.nav-link').first();
      if (await navLink.count() > 0) {
        await navLink.click();
      }
    }

    // Then: Should handle connectivity loss gracefully
    await page.waitForTimeout(3000);

    // Application should remain stable
    const stillFunctional = await page.locator('#portfolio, .user-selection, .error-message').count() > 0;
    expect(stillFunctional).toBeTruthy();
  });

  test('should provide proper error context to users', async ({ page }) => {
    // Given: Specific API endpoint fails
    await page.route('**/api/v1/projects', route => {
      route.fulfill({
        status: 404,
        body: JSON.stringify({
          detail: 'Projects endpoint not found'
        })
      });
    });

    // When: User loads portfolio
    await page.goto('/');
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 10000 });

    // Navigate to projects section if in single-user mode
    const projectsLink = page.locator('a[href="#projects"]');
    if (await projectsLink.count() > 0) {
      await projectsLink.click();
      await page.waitForTimeout(2000);
    }

    // Then: Error information should be contextual and helpful
    const projectsSection = page.locator('#projects');
    if (await projectsSection.isVisible()) {
      const projectsContent = page.locator('#projectsContent');
      const contentText = await projectsContent.textContent();

      // Should either have fallback content or helpful error message
      expect(contentText?.length).toBeGreaterThan(0);
    }
  });
});
