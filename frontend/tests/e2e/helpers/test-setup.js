/**
 * Module: tests.e2e.helpers.test_setup
 * Description: Test setup utilities and helpers for E2E tests
 *
 * Author: pmac
 * Created: 2025-08-30
 * Modified: 2025-08-30
 *
 * Dependencies:
 * - @playwright/test: 1.40.0+ - Browser automation framework
 *
 * Usage:
 *     import { setupSingleUser, setupMultiUser } from './helpers/test-setup.js';
 *
 * Notes:
 *     - Provides common test setup patterns
 *     - Handles user mode configuration
 *     - Centralizes test data management
 */

import { expect } from '@playwright/test';

/**
 * Setup single user mode for testing
 */
export async function setupSingleUser(page) {
  await page.route('**/api/v1/system/info', async route => {
    const response = await route.fetch();
    const json = await response.json();

    // Ensure only one user for single-user mode
    json.users = [
      {
        username: 'testuser',
        full_name: 'Test User',
        email: 'test@example.com',
        is_admin: true
      }
    ];

    await route.fulfill({
      status: 200,
      body: JSON.stringify(json)
    });
  });
}

/**
 * Setup multi-user mode for testing
 */
export async function setupMultiUser(page) {
  await page.route('**/api/v1/system/info', async route => {
    const response = await route.fetch();
    const json = await response.json();

    // Ensure multiple users for multi-user mode
    json.users = [
      {
        username: 'admin',
        full_name: 'Admin User',
        email: 'admin@test.com',
        is_admin: true
      },
      {
        username: 'john',
        full_name: 'John Doe',
        email: 'john@test.com',
        is_admin: false
      },
      {
        username: 'jane',
        full_name: 'Jane Smith',
        email: 'jane@test.com',
        is_admin: false
      }
    ];

    await route.fulfill({
      status: 200,
      body: JSON.stringify(json)
    });
  });
}

/**
 * Mock endpoint data for testing
 */
export async function mockEndpointData(page, endpoint, data) {
  await page.route(`**/api/v1/${endpoint}`, route => {
    route.fulfill({
      status: 200,
      body: JSON.stringify({
        items: Array.isArray(data) ? data : [data],
        total: Array.isArray(data) ? data.length : 1
      })
    });
  });

  // Also mock user-specific endpoints
  await page.route(`**/api/v1/${endpoint}/users/*`, route => {
    route.fulfill({
      status: 200,
      body: JSON.stringify({
        items: Array.isArray(data) ? data : [data],
        total: Array.isArray(data) ? data.length : 1
      })
    });
  });
}

/**
 * Wait for portfolio to load completely
 */
export async function waitForPortfolioLoad(page, timeout = 10000) {
  await expect(page.locator('.loading-screen')).toBeHidden({ timeout });

  // Verify either user selection or portfolio is visible
  const hasContent = await page.locator('#portfolio, .user-selection').count();
  expect(hasContent).toBeGreaterThan(0);
}

/**
 * Select user in multi-user mode
 */
export async function selectUser(page, username) {
  const userCard = page.locator(`.user-card[data-username="${username}"]`);
  await expect(userCard).toBeVisible();
  await userCard.click();
  await waitForPortfolioLoad(page, 15000);
}

/**
 * Navigate to section in portfolio
 */
export async function navigateToSection(page, sectionId) {
  const navLink = page.locator(`a[href="#${sectionId}"]`);
  await expect(navLink).toBeVisible();
  await navLink.click();
  await expect(page.locator(`#${sectionId}`)).toBeInViewport();
}

/**
 * Check if system is in multi-user mode
 */
export async function isMultiUserMode(page) {
  return await page.locator('.user-selection').isVisible();
}

/**
 * Get all available sections in portfolio
 */
export async function getPortfolioSections(page) {
  const sections = [];
  const sectionIds = ['about', 'experience', 'skills', 'personal-story', 'projects', 'contact'];

  for (const id of sectionIds) {
    const section = page.locator(`#${id}`);
    if (await section.isVisible()) {
      sections.push(id);
    }
  }

  return sections;
}

/**
 * Mock API error for specific endpoint
 */
export async function mockAPIError(page, endpoint, status = 500, message = 'Server Error') {
  await page.route(`**/api/v1/${endpoint}*`, route => {
    route.fulfill({
      status,
      body: JSON.stringify({ detail: message })
    });
  });
}

/**
 * Mock slow API response
 */
export async function mockSlowResponse(page, endpoint, delay = 3000) {
  await page.route(`**/api/v1/${endpoint}*`, async route => {
    await new Promise(resolve => setTimeout(resolve, delay));
    const response = await route.fetch();
    route.fulfill({ response });
  });
}

/**
 * Create sample content data for testing
 */
export function createSampleContent(type = 'about') {
  const sampleData = {
    about: {
      content: 'This is sample about content for testing.',
      meta: { title: 'About', section: 'about' }
    },
    experience: {
      content: 'Sample work experience and career history.',
      meta: { title: 'Experience', section: 'experience' }
    },
    skills: {
      content: 'Programming languages and technical skills.',
      meta: { title: 'Skills', section: 'skills' }
    },
    projects: {
      content: 'Portfolio of completed projects.',
      meta: { title: 'Projects', section: 'projects' }
    },
    'personal-story': {
      content: 'Personal journey and background story.',
      meta: { title: 'My Story', section: 'personal-story' }
    },
    contact: {
      content: 'Contact information and ways to reach out.',
      meta: { title: 'Contact', section: 'contact' }
    }
  };

  return sampleData[type] || sampleData.about;
}

/**
 * Verify section has content loaded
 */
export async function verifySectionContent(page, sectionId) {
  const section = page.locator(`#${sectionId}`);
  await expect(section).toBeVisible();

  const contentContainer = page.locator(`#${sectionId.replace('-', '')}Content`);
  await expect(contentContainer).toBeVisible();

  const content = await contentContainer.textContent();
  expect(content?.trim().length).toBeGreaterThan(0);
}

/**
 * Wait for all sections to be ready
 */
export async function waitForAllSections(page) {
  const expectedSections = ['about', 'experience', 'skills', 'projects'];

  for (const sectionId of expectedSections) {
    const section = page.locator(`#${sectionId}`);
    if (await section.count() > 0) {
      await expect(section).toBeVisible();
    }
  }
}

/**
 * Check console for JavaScript errors
 */
export async function checkConsoleErrors(page) {
  const errors = [];
  page.on('console', msg => {
    if (msg.type() === 'error') {
      errors.push(msg.text());
    }
  });

  return errors;
}

/**
 * Simulate network conditions
 */
export async function simulateNetworkCondition(page, condition = 'slow') {
  const conditions = {
    offline: () => page.route('**/*', route => route.abort()),
    slow: () => page.route('**/*', async route => {
      await new Promise(resolve => setTimeout(resolve, 200));
      const response = await route.fetch();
      route.fulfill({ response });
    }),
    fast: () => page.route('**/*', async route => {
      const response = await route.fetch();
      route.fulfill({ response });
    })
  };

  if (conditions[condition]) {
    await conditions[condition]();
  }
}
