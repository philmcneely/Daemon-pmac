/**
 * Module: tests.e2e.test_frontend_performance
 * Description: E2E tests for frontend performance and optimization
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
 *     npx playwright test performance
 *
 * Notes:
 *     - Tests loading performance and optimization
 *     - Validates resource usage and timing
 *     - Ensures responsive user experience
 */

import { test, expect } from '@playwright/test';

test.describe('Frontend Performance & Optimization', () => {
  test('should have fast loading, efficient resources, and responsive interactions', async ({ page }) => {
    // Given: Performance timing tracking
    const startTime = Date.now();
    const responses = [];
    page.on('response', response => {
      responses.push({
        url: response.url(),
        status: response.status(),
        size: response.headers()['content-length'] || 0
      });
    });

    // When: User loads the homepage
    await page.goto('/');
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 3000 });
    await expect(page.locator('#portfolio, .user-selection')).toBeVisible();

    const loadTime = Date.now() - startTime;

    // Then: Load time should be reasonable (under 8 seconds for full load)
    expect(loadTime).toBeLessThan(8000);

    // Resource loading should be efficient
    const cssFiles = responses.filter(r => r.url.includes('.css'));
    const jsFiles = responses.filter(r => r.url.includes('.js'));
    const failedResources = responses.filter(r => r.status >= 400);

    expect(cssFiles.length).toBeLessThan(10);
    expect(jsFiles.length).toBeLessThan(10);
    expect(failedResources.length).toBe(0);

    // Skip if in multi-user mode and test section loading
    const isMultiUser = await page.locator('.user-selection').isVisible();
    if (isMultiUser) {
      await page.locator('.user-card').first().click();
      await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 3000 });
    }

    // Test concurrent section loading
    const sectionsStartTime = Date.now();
    const sections = ['#about', '#experience', '#skills', '#projects'];
    for (const sectionId of sections) {
      await expect(page.locator(sectionId)).toBeVisible({ timeout: 5000 });
    }
    const sectionsLoadTime = Date.now() - sectionsStartTime;
    expect(sectionsLoadTime).toBeLessThan(5000);

    // Test responsive interactions
    const interactiveElement = page.locator('.nav-link, .user-card, .hero-section').first();
    await expect(interactiveElement).toBeVisible();
    await interactiveElement.click();
    await expect(page.locator('#portfolio, .user-selection')).toBeVisible();
  });

  test('should handle memory usage and API optimization efficiently', async ({ page }) => {
    // Given: API call monitoring
    const apiCalls = [];
    page.on('request', request => {
      if (request.url().includes('/api/')) {
        apiCalls.push({
          url: request.url(),
          method: request.method(),
          timestamp: Date.now()
        });
      }
    });

    await page.goto('/');
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 3000 });

    const isMultiUser = await page.locator('.user-selection').isVisible();
    if (isMultiUser) {
      // Test user switching for memory usage
      for (let i = 0; i < 2; i++) {
        const userCards = page.locator('.user-card');
        const cardCount = await userCards.count();
        if (cardCount > 1) {
          await userCards.nth(i % cardCount).click();
          await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 3000 });
          const backButton = page.locator('.back-to-users-btn');
          if (await backButton.isVisible()) {
            await backButton.click();
            await expect(page.locator('.user-selection')).toBeVisible();
          }
        }
      }
    } else {
      // Test navigation for memory usage
      const navLinks = page.locator('.nav-link');
      const linkCount = await navLinks.count();
      for (let i = 0; i < Math.min(linkCount, 3); i++) {
        await navLinks.nth(i).click();
        await page.waitForTimeout(500);
      }
    }

    // Check memory usage
    const memoryUsage = await page.evaluate(() => {
      return window.performance.memory ? {
        usedJSHeapSize: window.performance.memory.usedJSHeapSize,
        totalJSHeapSize: window.performance.memory.totalJSHeapSize
      } : null;
    });

    if (memoryUsage) {
      expect(memoryUsage.usedJSHeapSize).toBeLessThan(50 * 1024 * 1024);
    }

    // API calls should be optimized
    const uniqueUrls = new Set(apiCalls.map(call => call.url));
    const duplicateRatio = apiCalls.length / uniqueUrls.size;
    expect(duplicateRatio).toBeLessThan(3);

    // System info should only be called reasonably
    const systemInfoCalls = apiCalls.filter(call => call.url.includes('/system/info'));
    expect(systemInfoCalls.length).toBeLessThanOrEqual(2);
  });

  test('should handle slow networks and large content efficiently', async ({ page }) => {
    // Given: Simulated slow network
    await page.route('**/*', async route => {
      await new Promise(resolve => setTimeout(resolve, 50)); // Reduced delay for faster testing
      const response = await route.fetch();
      route.fulfill({ response });
    });

    const startTime = Date.now();
    await page.goto('/');
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 3000 });

    const loadTime = Date.now() - startTime;
    expect(loadTime).toBeLessThan(15000);

    await expect(page.locator('#portfolio, .user-selection')).toBeVisible();

    // Test large content handling
    const isMultiUser = await page.locator('.user-selection').isVisible();
    if (isMultiUser) {
      await page.locator('.user-card').first().click();
      await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 3000 });
    }

    const sections = ['#about', '#experience', '#skills', '#projects'];
    for (const sectionId of sections) {
      const section = page.locator(sectionId);
      if (await section.isVisible()) {
        const content = section.locator('div, p, span');
        const contentCount = await content.count();
        if (contentCount > 10) {
          await section.scrollIntoView();
          await page.waitForTimeout(100);
          await expect(section).toBeInViewport();
        }
      }
    }

    // Navigation should remain smooth
    const navStartTime = Date.now();
    const navLinks = page.locator('.nav-link');
    const linkCount = await navLinks.count();
    if (linkCount > 0) {
      await navLinks.first().click();
      await page.waitForTimeout(100);
      const section = page.locator(await navLinks.first().getAttribute('href'));
      await expect(section).toBeInViewport({ timeout: 3000 });
    }
    const navTime = Date.now() - navStartTime;
    expect(navTime).toBeLessThan(2000);
  });
});
