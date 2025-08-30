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
  test('should load initial page within acceptable time limits', async ({ page }) => {
    // Given: Performance timing tracking
    const startTime = Date.now();

    // When: User loads the homepage
    await page.goto('/');

    // Wait for meaningful content
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 10000 });
    await expect(page.locator('#portfolio, .user-selection')).toBeVisible();

    const loadTime = Date.now() - startTime;

    // Then: Load time should be reasonable (under 8 seconds for full load)
    expect(loadTime).toBeLessThan(8000);
    console.log(`Page load time: ${loadTime}ms`);
  });

  test('should have efficient resource loading', async ({ page }) => {
    // Given: Resource monitoring
    const responses = [];
    page.on('response', response => {
      responses.push({
        url: response.url(),
        status: response.status(),
        size: response.headers()['content-length'] || 0
      });
    });

    // When: Page loads
    await page.goto('/');
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 10000 });

    // Then: Resource loading should be efficient
    const cssFiles = responses.filter(r => r.url.includes('.css'));
    const jsFiles = responses.filter(r => r.url.includes('.js'));
    const apiCalls = responses.filter(r => r.url.includes('/api/'));

    // Should have reasonable number of resources
    expect(cssFiles.length).toBeLessThan(10);
    expect(jsFiles.length).toBeLessThan(10);

    // All critical resources should load successfully
    const failedResources = responses.filter(r => r.status >= 400);
    expect(failedResources.length).toBe(0);

    console.log(`CSS files: ${cssFiles.length}, JS files: ${jsFiles.length}, API calls: ${apiCalls.length}`);
  });

  test('should handle concurrent section loading efficiently', async ({ page }) => {
    // Given: Multiple sections need to load
    await page.goto('/');
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 10000 });

    // Skip if in multi-user mode
    const isMultiUser = await page.locator('.user-selection').isVisible();
    if (isMultiUser) {
      await page.locator('.user-card').first().click();
      await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 10000 });
    }

    // When: All sections should be loading/loaded
    const startTime = Date.now();

    // Wait for multiple sections to be visible
    const sections = ['#about', '#experience', '#skills', '#projects'];
    for (const sectionId of sections) {
      await expect(page.locator(sectionId)).toBeVisible({ timeout: 5000 });
    }

    const sectionsLoadTime = Date.now() - startTime;

    // Then: Sections should load efficiently
    expect(sectionsLoadTime).toBeLessThan(5000);
    console.log(`Sections load time: ${sectionsLoadTime}ms`);
  });

  test('should maintain responsive interactions during loading', async ({ page }) => {
    // Given: Page is loading
    await page.goto('/');

    // When: User tries to interact during loading
    const loadingScreen = page.locator('.loading-screen');

    if (await loadingScreen.isVisible()) {
      // Try clicking around during loading - should not break
      await page.click('body', { timeout: 1000 }).catch(() => {
        // Expected to potentially fail during loading
      });
    }

    // Wait for loading to complete
    await expect(loadingScreen).toBeHidden({ timeout: 10000 });

    // Then: Interface should be responsive after loading
    const interactiveElement = page.locator('.nav-link, .user-card, .hero-section').first();
    await expect(interactiveElement).toBeVisible();

    // Element should be clickable
    await interactiveElement.click();

    // Page should remain stable
    await expect(page.locator('#portfolio, .user-selection')).toBeVisible();
  });

  test('should optimize image and media loading', async ({ page }) => {
    // Given: Media monitoring
    const mediaRequests = [];
    page.on('request', request => {
      const url = request.url();
      if (url.includes('.jpg') || url.includes('.png') || url.includes('.svg') || url.includes('.gif')) {
        mediaRequests.push(url);
      }
    });

    // When: Page loads with potential media
    await page.goto('/');
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 10000 });

    // Select user if in multi-user mode
    const isMultiUser = await page.locator('.user-selection').isVisible();
    if (isMultiUser) {
      await page.locator('.user-card').first().click();
      await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 10000 });
    }

    // Then: Media requests should be reasonable
    console.log(`Media requests: ${mediaRequests.length}`);

    // Check for any broken images
    const images = page.locator('img');
    const imageCount = await images.count();

    for (let i = 0; i < imageCount; i++) {
      const img = images.nth(i);
      const isLoaded = await img.evaluate((el) => el.complete && el.naturalHeight !== 0);
      expect(isLoaded).toBeTruthy();
    }
  });

  test('should handle memory usage efficiently during extended use', async ({ page }) => {
    // Given: Extended usage simulation
    await page.goto('/');
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 10000 });

    // When: Simulate extended usage
    const isMultiUser = await page.locator('.user-selection').isVisible();

    if (isMultiUser) {
      // Switch between users multiple times
      for (let i = 0; i < 3; i++) {
        const userCards = page.locator('.user-card');
        const cardCount = await userCards.count();

        if (cardCount > 1) {
          await userCards.nth(i % cardCount).click();
          await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 10000 });

          const backButton = page.locator('.back-to-users-btn');
          if (await backButton.isVisible()) {
            await backButton.click();
            await expect(page.locator('.user-selection')).toBeVisible();
          }
        }
      }
    } else {
      // Navigate between sections multiple times
      const navLinks = page.locator('.nav-link');
      const linkCount = await navLinks.count();

      for (let i = 0; i < Math.min(linkCount, 5); i++) {
        await navLinks.nth(i).click();
        await page.waitForTimeout(500);
      }
    }

    // Then: Page should remain responsive
    await expect(page.locator('#portfolio, .user-selection')).toBeVisible();

    // No console errors related to memory
    const errors = await page.evaluate(() => {
      return window.performance.memory ? {
        usedJSHeapSize: window.performance.memory.usedJSHeapSize,
        totalJSHeapSize: window.performance.memory.totalJSHeapSize
      } : null;
    });

    if (errors) {
      console.log('Memory usage:', errors);
      // Memory usage should be reasonable (less than 50MB)
      expect(errors.usedJSHeapSize).toBeLessThan(50 * 1024 * 1024);
    }
  });

  test('should optimize API call patterns', async ({ page }) => {
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

    // When: Page loads and user interacts
    await page.goto('/');
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 10000 });

    const isMultiUser = await page.locator('.user-selection').isVisible();
    if (isMultiUser) {
      await page.locator('.user-card').first().click();
      await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 10000 });
    }

    // Then: API calls should be optimized
    console.log(`Total API calls: ${apiCalls.length}`);

    // Should not have excessive duplicate calls
    const uniqueUrls = new Set(apiCalls.map(call => call.url));
    const duplicateRatio = apiCalls.length / uniqueUrls.size;

    // Allow some duplicates but not excessive
    expect(duplicateRatio).toBeLessThan(3);

    // System info should only be called once initially
    const systemInfoCalls = apiCalls.filter(call => call.url.includes('/system/info'));
    expect(systemInfoCalls.length).toBeLessThanOrEqual(2);
  });

  test('should provide smooth user experience during data updates', async ({ page }) => {
    // Given: Page is loaded
    await page.goto('/');
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 10000 });

    // Handle both user modes
    const isMultiUser = await page.locator('.user-selection').isVisible();
    if (isMultiUser) {
      await page.locator('.user-card').first().click();
      await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 10000 });
    }

    // When: Content is updating/loading
    const startTime = Date.now();

    // Navigate between sections to trigger content updates
    const navLinks = page.locator('.nav-link');
    const linkCount = await navLinks.count();

    if (linkCount > 0) {
      await navLinks.first().click();

      // Check for smooth transitions
      await page.waitForTimeout(100);

      // Should not have layout thrashing
      const section = page.locator(await navLinks.first().getAttribute('href'));
      await expect(section).toBeInViewport({ timeout: 3000 });
    }

    const interactionTime = Date.now() - startTime;

    // Then: Interactions should be smooth
    expect(interactionTime).toBeLessThan(2000);
    console.log(`Navigation response time: ${interactionTime}ms`);
  });

  test('should handle large content volumes efficiently', async ({ page }) => {
    // Given: Potentially large content loads
    await page.goto('/');
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 10000 });

    const isMultiUser = await page.locator('.user-selection').isVisible();
    if (isMultiUser) {
      await page.locator('.user-card').first().click();
      await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 10000 });
    }

    // When: Large content sections load
    const sections = ['#about', '#experience', '#skills', '#projects'];

    for (const sectionId of sections) {
      const section = page.locator(sectionId);
      if (await section.isVisible()) {
        const content = section.locator('div, p, span');
        const contentCount = await content.count();

        // If there's a lot of content, scrolling should still be smooth
        if (contentCount > 10) {
          await section.scrollIntoView();
          await page.waitForTimeout(200);

          // Check that content is still responsive
          await expect(section).toBeInViewport();
        }
      }
    }

    // Then: Page should remain responsive with large content
    const hero = page.locator('.hero-section');
    await expect(hero).toBeVisible();
  });

  test('should maintain performance on slower networks', async ({ page }) => {
    // Given: Simulated slow network
    await page.route('**/*', async route => {
      // Add artificial delay to simulate slow network
      await new Promise(resolve => setTimeout(resolve, 100));
      const response = await route.fetch();
      route.fulfill({ response });
    });

    // When: User loads on slow network
    const startTime = Date.now();
    await page.goto('/');

    // Should still load within reasonable time
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 20000 });

    const loadTime = Date.now() - startTime;

    // Then: Should handle slow network gracefully
    expect(loadTime).toBeLessThan(20000);

    // Content should be available
    await expect(page.locator('#portfolio, .user-selection')).toBeVisible();

    console.log(`Slow network load time: ${loadTime}ms`);
  });
});
