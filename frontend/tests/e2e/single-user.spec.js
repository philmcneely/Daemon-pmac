/**
 * Module: tests.e2e.test_frontend_single_user
 * Description: E2E tests for single-user mode portfolio frontend functionality
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
 *     npx playwright test single-user
 *
 * Notes:
 *     - Tests single-user mode portfolio functionality
 *     - Validates section loading and content display
 *     - Ensures proper navigation and hero section
 */

import { test, expect } from '@playwright/test';

test.describe('Single User Mode - Portfolio Frontend', () => {
  test.beforeEach(async ({ page }) => {
    // Set up single-user mode by ensuring only one user exists
    // This would typically be done via API setup
    await page.goto('/');
  });

  test('should load portfolio homepage in single-user mode', async ({ page }) => {
    // Given: System is in single-user mode
    // When: User navigates to homepage
    await page.goto('/');

    // Then: Page loads with portfolio structure
    await expect(page).toHaveTitle(/Portfolio/);
    await expect(page.locator('#portfolio')).toBeVisible();
    await expect(page.locator('.hero-section')).toBeVisible();
  });

  test('should display hero section with user information', async ({ page }) => {
    // Given: Single-user portfolio is loaded
    await page.goto('/');

    // Wait for loading to complete
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 10000 });

    // Then: Hero section shows user details
    const heroName = page.locator('.hero-name');
    const heroTitle = page.locator('.hero-title');

    await expect(heroName).toBeVisible();
    await expect(heroTitle).toBeVisible();

    // Verify hero content is populated (not default values)
    const nameText = await heroName.textContent();
    const titleText = await heroTitle.textContent();

    expect(nameText).toBeTruthy();
    expect(nameText).not.toBe('Portfolio');
    expect(titleText).toBeTruthy();
    expect(titleText).not.toBe('Personal Portfolio');
  });

  test('should load and display About section', async ({ page }) => {
    // Given: Single-user portfolio is loaded
    await page.goto('/');
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 10000 });

    // When: About section loads
    const aboutSection = page.locator('#about');
    const aboutContent = page.locator('#aboutContent');

    // Then: About section is visible with content
    await expect(aboutSection).toBeVisible();
    await expect(aboutContent).toBeVisible();

    // Verify content is loaded (not empty)
    const content = await aboutContent.textContent();
    expect(content?.trim().length).toBeGreaterThan(0);
  });

  test('should load and display Experience/Resume section', async ({ page }) => {
    // Given: Single-user portfolio is loaded
    await page.goto('/');
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 10000 });

    // When: Experience section loads
    const experienceSection = page.locator('#experience');
    const experienceContent = page.locator('#experienceContent');

    // Then: Experience section is visible with content
    await expect(experienceSection).toBeVisible();
    await expect(experienceContent).toBeVisible();

    // Verify content structure
    const content = await experienceContent.textContent();
    expect(content?.trim().length).toBeGreaterThan(0);
  });

  test('should load and display Skills section', async ({ page }) => {
    // Given: Single-user portfolio is loaded
    await page.goto('/');
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 10000 });

    // When: Skills section loads
    const skillsSection = page.locator('#skills');
    const skillsContent = page.locator('#skillsContent');

    // Then: Skills section is visible with content
    await expect(skillsSection).toBeVisible();
    await expect(skillsContent).toBeVisible();
  });

  test('should load and display Projects section', async ({ page }) => {
    // Given: Single-user portfolio is loaded
    await page.goto('/');
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 10000 });

    // When: Projects section loads
    const projectsSection = page.locator('#projects');
    const projectsContent = page.locator('#projectsContent');

    // Then: Projects section is visible with content
    await expect(projectsSection).toBeVisible();
    await expect(projectsContent).toBeVisible();
  });

  test('should load and display Personal Story section', async ({ page }) => {
    // Given: Single-user portfolio is loaded
    await page.goto('/');
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 10000 });

    // When: Personal Story section loads
    const storySection = page.locator('#personal-story');
    const storyContent = page.locator('#personalStoryContent');

    // Then: Personal Story section is visible with content
    await expect(storySection).toBeVisible();
    await expect(storyContent).toBeVisible();
  });

  test('should have working navigation between sections', async ({ page }) => {
    // Given: Single-user portfolio is loaded
    await page.goto('/');
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 10000 });

    // When: User clicks navigation links
    const aboutLink = page.locator('a[href=\"#about\"]');
    const projectsLink = page.locator('a[href=\"#projects\"]');

    await expect(aboutLink).toBeVisible();
    await expect(projectsLink).toBeVisible();

    // Then: Navigation works correctly
    await aboutLink.click();
    await expect(page.locator('#about')).toBeInViewport();

    await projectsLink.click();
    await expect(page.locator('#projects')).toBeInViewport();
  });

  test('should display contact section with proper information', async ({ page }) => {
    // Given: Single-user portfolio is loaded
    await page.goto('/');
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 10000 });

    // When: Contact section loads
    const contactSection = page.locator('#contact');
    const contactContent = page.locator('#contactContent');

    // Then: Contact section is visible and functional
    await expect(contactSection).toBeVisible();
    await expect(contactContent).toBeVisible();
  });

  test('should handle API errors gracefully', async ({ page }) => {
    // Given: API server is potentially unavailable
    // Mock API failure scenarios
    await page.route('**/api/v1/system/info', route => {
      route.fulfill({ status: 500, body: 'Server Error' });
    });

    // When: User loads the portfolio
    await page.goto('/');

    // Then: Error handling is displayed
    // Wait longer for potential error states
    await page.waitForTimeout(5000);

    // Should show some kind of error state or fallback
    const hasErrorState = await page.locator('.error-message, .fallback-content, .retry-button').count() > 0;
    const hasContent = await page.locator('#portfolio').isVisible();

    // Either error handling or graceful degradation should occur
    expect(hasErrorState || hasContent).toBeTruthy();
  });

  test('should be responsive on mobile viewport', async ({ page }) => {
    // Given: Mobile viewport
    await page.setViewportSize({ width: 375, height: 667 }); // iPhone size

    // When: User loads portfolio
    await page.goto('/');
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 10000 });

    // Then: Layout adapts to mobile
    const portfolio = page.locator('#portfolio');
    await expect(portfolio).toBeVisible();

    // Hero section should be responsive
    const heroSection = page.locator('.hero-section');
    await expect(heroSection).toBeVisible();

    // Navigation should work on mobile
    const navLinks = page.locator('.nav-link');
    const navCount = await navLinks.count();
    expect(navCount).toBeGreaterThan(0);
  });

  test('should load all sections without no-user mode interference', async ({ page }) => {
    // Given: Single-user mode is active
    await page.goto('/');
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 10000 });

    // When: All sections are loaded
    const sections = [
      '#about',
      '#experience',
      '#skills',
      '#personal-story',
      '#projects',
      '#contact'
    ];

    // Then: All sections should be present and visible
    for (const sectionSelector of sections) {
      const section = page.locator(sectionSelector);
      await expect(section).toBeVisible();
    }

    // Verify we're not in user selection mode
    const userSelection = page.locator('.user-selection');
    await expect(userSelection).not.toBeVisible();
  });

  test('should have proper meta tags and SEO elements', async ({ page }) => {
    // Given: Single-user portfolio loads
    await page.goto('/');

    // Then: Proper meta tags are set
    await expect(page).toHaveTitle(/Phil McNeely|Portfolio/);

    // Check for viewport meta tag
    const viewportMeta = page.locator('meta[name=\"viewport\"]');
    await expect(viewportMeta).toHaveAttribute('content', /width=device-width/);
  });

  test('should handle deep links to specific sections', async ({ page }) => {
    // Given: User navigates directly to a section
    await page.goto('/#projects');
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 10000 });

    // Then: Page loads and scrolls to the correct section
    await expect(page.locator('#projects')).toBeInViewport();

    // And portfolio is fully functional
    await expect(page.locator('#portfolio')).toBeVisible();
    await expect(page.locator('.hero-section')).toBeVisible();
  });
});
