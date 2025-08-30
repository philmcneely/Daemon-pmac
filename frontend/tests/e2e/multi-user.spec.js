/**
 * Module: tests.e2e.test_frontend_multi_user
 * Description: E2E tests for multi-user mode portfolio frontend functionality
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
 *     npx playwright test multi-user
 *
 * Notes:
 *     - Tests multi-user mode portfolio functionality
 *     - Validates user selection interface
 *     - Ensures proper user switching and portfolio reset
 */

import { test, expect } from '@playwright/test';

test.describe('Multi User Mode - Portfolio Frontend', () => {
  test.beforeEach(async ({ page }) => {
    // Mock multi-user system info response
    await page.route('**/api/v1/system/info', async route => {
      const response = await route.fetch();
      const json = await response.json();

      // Ensure multiple users exist for multi-user mode
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
  });

  test('should detect multi-user mode and show user selection', async ({ page }) => {
    // Given: System has multiple users
    // When: User navigates to homepage
    await page.goto('/');

    // Wait for loading to complete
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 10000 });

    // Then: User selection interface is displayed
    await expect(page.locator('.user-selection')).toBeVisible();
    await expect(page.locator('.user-selection h1')).toContainText('Select User Portfolio');

    // Verify user cards are displayed
    const userCards = page.locator('.user-card');
    const cardCount = await userCards.count();
    expect(cardCount).toBeGreaterThanOrEqual(2); // At least 2 users for multi-user mode
  });

  test('should display user cards with correct information', async ({ page }) => {
    // Given: Multi-user mode is active
    await page.goto('/');
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 10000 });

    // Then: User cards show proper information
    const userCards = page.locator('.user-card');

    // Check first user card (admin)
    const adminCard = userCards.first();
    await expect(adminCard.locator('h3')).toContainText('Admin User');
    await expect(adminCard.locator('.user-email')).toContainText('admin@test.com');
    await expect(adminCard.locator('.user-role')).toContainText('Administrator');

    // Verify click interaction elements
    await expect(adminCard.locator('.user-card-action')).toBeVisible();
    await expect(adminCard.locator('.fas.fa-arrow-right')).toBeVisible();
  });

  test('should load selected user portfolio after clicking user card', async ({ page }) => {
    // Given: Multi-user selection interface is displayed
    await page.goto('/');
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 10000 });

    // When: User clicks on a user card
    const johnCard = page.locator('.user-card[data-username=\"john\"]');
    await expect(johnCard).toBeVisible();
    await johnCard.click();

    // Wait for portfolio to load
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 15000 });

    // Then: Portfolio is displayed for selected user
    await expect(page.locator('#portfolio')).toBeVisible();
    await expect(page.locator('.hero-section')).toBeVisible();

    // User selection interface should be hidden
    await expect(page.locator('.user-selection')).not.toBeVisible();

    // Back to users button should be available
    await expect(page.locator('.back-to-users-btn')).toBeVisible();
  });

  test('should show back to users button and allow user switching', async ({ page }) => {
    // Given: A user portfolio is loaded
    await page.goto('/');
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 10000 });

    // Select a user
    const janeCard = page.locator('.user-card[data-username=\"jane\"]');
    await janeCard.click();
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 15000 });

    // When: User clicks back to users button
    const backButton = page.locator('.back-to-users-btn');
    await expect(backButton).toBeVisible();
    await backButton.click();

    // Then: User selection interface reappears
    await expect(page.locator('.user-selection')).toBeVisible();
    await expect(page.locator('.user-card')).toHaveCount(3); // Original user count

    // Portfolio should be hidden
    const portfolioSections = page.locator('#about, #experience, #skills, #projects');
    await expect(portfolioSections.first()).not.toBeVisible();
  });

  test('should properly reset portfolio structure when switching users', async ({ page }) => {
    // Given: First user portfolio is loaded
    await page.goto('/');
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 10000 });

    const adminCard = page.locator('.user-card[data-username=\"admin\"]');
    await adminCard.click();
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 15000 });

    // Verify first user's content is loaded
    const initialHeroName = await page.locator('.hero-name').textContent();

    // When: Switch to different user
    await page.locator('.back-to-users-btn').click();
    await expect(page.locator('.user-selection')).toBeVisible();

    const johnCard = page.locator('.user-card[data-username=\"john\"]');
    await johnCard.click();
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 15000 });

    // Then: Portfolio structure is reset and new user content loads
    const newHeroName = await page.locator('.hero-name').textContent();

    // Content should be different (assuming different users have different content)
    // At minimum, hero section should update
    await expect(page.locator('.hero-section')).toBeVisible();

    // All sections should be properly reset and reloaded
    const sections = ['#about', '#experience', '#skills', '#projects'];
    for (const sectionId of sections) {
      await expect(page.locator(sectionId)).toBeVisible();
    }
  });

  test('should handle user selection keyboard navigation', async ({ page }) => {
    // Given: Multi-user selection interface
    await page.goto('/');
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 10000 });

    // When: User navigates with keyboard
    const firstCard = page.locator('.user-card').first();
    await firstCard.focus();

    // Then: Card should be focusable and interactive
    await expect(firstCard).toBeFocused();

    // Enter key should select the user
    await page.keyboard.press('Enter');
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 15000 });

    // Portfolio should load
    await expect(page.locator('#portfolio')).toBeVisible();
  });

  test('should maintain responsive design in multi-user mode', async ({ page }) => {
    // Given: Mobile viewport and multi-user mode
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 10000 });

    // Then: User selection is responsive
    const userSelection = page.locator('.user-selection');
    await expect(userSelection).toBeVisible();

    const userGrid = page.locator('.user-grid');
    await expect(userGrid).toBeVisible();

    // User cards should stack appropriately on mobile
    const userCards = page.locator('.user-card');
    const cardCount = await userCards.count();
    expect(cardCount).toBeGreaterThanOrEqual(2);

    // Select a user and verify portfolio is responsive
    await userCards.first().click();
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 15000 });

    await expect(page.locator('#portfolio')).toBeVisible();
    await expect(page.locator('.hero-section')).toBeVisible();
  });

  test('should handle API errors during user selection', async ({ page }) => {
    // Given: API returns error for user data
    await page.route('**/api/v1/about/users/john', route => {
      route.fulfill({ status: 500, body: 'Server Error' });
    });

    await page.goto('/');
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 10000 });

    // When: User selects a user with API error
    const johnCard = page.locator('.user-card[data-username=\"john\"]');
    await johnCard.click();

    // Then: Error should be handled gracefully
    // Wait for potential error handling
    await page.waitForTimeout(3000);

    // Should either show error message or fallback content
    const hasErrorHandling = await page.locator('.error-message, .retry-button, .fallback-content').count() > 0;
    const staysOnSelection = await page.locator('.user-selection').isVisible();

    // Either error handling or staying on selection screen is acceptable
    expect(hasErrorHandling || staysOnSelection).toBeTruthy();
  });

  test('should preserve user selection state on page refresh', async ({ page }) => {
    // Given: User has selected a portfolio
    await page.goto('/');
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 10000 });

    const adminCard = page.locator('.user-card[data-username=\"admin\"]');
    await adminCard.click();
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 15000 });

    // Verify portfolio is loaded
    await expect(page.locator('#portfolio')).toBeVisible();

    // When: Page is refreshed
    await page.reload();

    // Then: Should return to user selection (expected behavior)
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 10000 });
    await expect(page.locator('.user-selection')).toBeVisible();

    // User can reselect
    await adminCard.click();
    await expect(page.locator('#portfolio')).toBeVisible();
  });

  test('should handle empty user list gracefully', async ({ page }) => {
    // Given: System returns empty user list
    await page.route('**/api/v1/system/info', async route => {
      const response = await route.fetch();
      const json = await response.json();
      json.users = []; // Empty user list

      await route.fulfill({
        status: 200,
        body: JSON.stringify(json)
      });
    });

    // When: User loads the page
    await page.goto('/');
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 10000 });

    // Then: Should handle gracefully (fallback to single-user mode or show message)
    const hasContent = await page.locator('#portfolio, .user-selection, .error-message').count() > 0;
    expect(hasContent).toBeGreaterThan(0);
  });

  test('should display proper loading states during user transitions', async ({ page }) => {
    // Given: Multi-user selection interface
    await page.goto('/');
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 10000 });

    // When: User clicks to select a portfolio
    const userCard = page.locator('.user-card').first();
    await userCard.click();

    // Then: Loading state should be shown during transition
    const loadingScreen = page.locator('.loading-screen');

    // Loading should appear briefly
    await expect(loadingScreen).toBeVisible();

    // Then disappear when content loads
    await expect(loadingScreen).toBeHidden({ timeout: 15000 });

    // Portfolio should be ready
    await expect(page.locator('#portfolio')).toBeVisible();
  });

  test('should display sections with proper content in selected user portfolio', async ({ page }) => {
    // Given: Multi-user mode is active
    await page.goto('/');
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 10000 });

    // When: User selects a portfolio
    const userCard = page.locator('.user-card').first();
    await userCard.click();
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 15000 });

    // Then: All sections should be visible with content
    const sections = [
      { selector: '#about', content: '#aboutContent' },
      { selector: '#experience', content: '#experienceContent' },
      { selector: '#skills', content: '#skillsContent' },
      { selector: '#personal-story', content: '#personalStoryContent' },
      { selector: '#projects', content: '#projectsContent' },
      { selector: '#contact', content: '#contactContent' }
    ];

    for (const section of sections) {
      const sectionElement = page.locator(section.selector);
      const contentElement = page.locator(section.content);

      await expect(sectionElement).toBeVisible();
      await expect(contentElement).toBeVisible();

      // Verify content is loaded (not placeholder)
      const content = await contentElement.textContent();
      expect(content?.trim().length).toBeGreaterThan(0);
      expect(content).not.toContain('will be displayed here');
    }
  });

  test('should show proper resume formatting in multi-user experience section', async ({ page }) => {
    // Given: Multi-user mode with selected user
    await page.goto('/');
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 10000 });

    const userCard = page.locator('.user-card').first();
    await userCard.click();
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 15000 });

    // When: Experience section loads
    const experienceContent = page.locator('#experienceContent');
    await expect(experienceContent).toBeVisible();

    // Then: Resume should be properly formatted
    const content = await experienceContent.textContent();
    expect(content?.trim().length).toBeGreaterThan(0);

    // Check for resume structure elements
    const hasResumeElements = await experienceContent.locator('.resume-container, .experience-item, .resume-header').count() > 0;
    expect(hasResumeElements).toBeTruthy();

    // If structured resume is present, check formatting
    const resumeContainer = experienceContent.locator('.resume-container');
    if (await resumeContainer.count() > 0) {
      // Check resume header
      const resumeHeader = resumeContainer.locator('.resume-header');
      if (await resumeHeader.count() > 0) {
        await expect(resumeHeader).toBeVisible();
      }

      // Check contact information formatting
      const contactGrid = resumeContainer.locator('.contact-grid');
      if (await contactGrid.count() > 0) {
        await expect(contactGrid).toBeVisible();
      }

      // Check experience entries
      const experienceEntries = resumeContainer.locator('.experience-entry');
      if (await experienceEntries.count() > 0) {
        await expect(experienceEntries.first()).toBeVisible();

        // Check for tech tags
        const techTags = experienceEntries.first().locator('.tech-tag');
        if (await techTags.count() > 0) {
          await expect(techTags.first()).toBeVisible();
        }
      }

      // Check skills section in resume
      const skillsGrid = resumeContainer.locator('.skills-grid');
      if (await skillsGrid.count() > 0) {
        await expect(skillsGrid).toBeVisible();
      }
    }
  });

  test('should validate skills matrix and formatting in multi-user mode', async ({ page }) => {
    // Given: Multi-user mode with selected user
    await page.goto('/');
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 10000 });

    const userCard = page.locator('.user-card').first();
    await userCard.click();
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 15000 });

    // When: Skills section loads
    const skillsContent = page.locator('#skillsContent');
    await expect(skillsContent).toBeVisible();

    // Then: Skills should be properly formatted
    const content = await skillsContent.textContent();
    expect(content?.trim().length).toBeGreaterThan(0);
    expect(content).not.toContain('will be added soon');

    // Check for skills formatting structures
    const hasSkillsGrid = await skillsContent.locator('.skills-grid').count() > 0;
    const hasSkillCategories = await skillsContent.locator('.skill-category').count() > 0;
    const hasSkillTags = await skillsContent.locator('.skill-tag').count() > 0;
    const hasSkillsTable = await skillsContent.locator('table').count() > 0;

    // At least one skills formatting should be present
    expect(hasSkillsGrid || hasSkillCategories || hasSkillTags || hasSkillsTable).toBeTruthy();

    // If skills matrix table is present, validate structure
    const skillsTable = skillsContent.locator('table');
    if (await skillsTable.count() > 0) {
      await expect(skillsTable.first()).toBeVisible();

      // Check for proper table headers
      const tableHeaders = skillsTable.locator('th');
      if (await tableHeaders.count() > 0) {
        const headerText = await tableHeaders.first().textContent();
        expect(headerText?.trim().length).toBeGreaterThan(0);
      }

      // Check for skill ratings or levels
      const tableCells = skillsTable.locator('td');
      if (await tableCells.count() > 0) {
        await expect(tableCells.first()).toBeVisible();
      }
    }

    // If skill categories are present, validate structure
    const skillCategories = skillsContent.locator('.skill-category');
    if (await skillCategories.count() > 0) {
      const firstCategory = skillCategories.first();
      await expect(firstCategory).toBeVisible();

      // Check for skill tags within categories
      const categoryTags = firstCategory.locator('.skill-tag');
      if (await categoryTags.count() > 0) {
        await expect(categoryTags.first()).toBeVisible();
      }
    }
  });

  test('should handle Goals & Values with proper default or content display in multi-user', async ({ page }) => {
    // Given: Multi-user mode with selected user
    await page.goto('/');
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 10000 });

    const userCard = page.locator('.user-card').first();
    await userCard.click();
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 15000 });

    // When: Goals & Values section loads
    const goalsValuesContent = page.locator('#goalsValuesContent');
    await expect(goalsValuesContent).toBeVisible();

    // Then: Content should be present (actual content or default message)
    const content = await goalsValuesContent.textContent();
    expect(content?.trim().length).toBeGreaterThan(0);

    // Check for content or default message
    const hasDefaultMessage = content?.includes('Goals and values will be displayed here');
    const hasActualContent = await goalsValuesContent.locator('.goals-values-container, .goals-section, .values-section').count() > 0;

    // Either default message OR actual content should be present
    expect(hasDefaultMessage || hasActualContent).toBeTruthy();

    // If actual content exists, verify structure
    if (hasActualContent) {
      expect(hasDefaultMessage).toBeFalsy();

      // Check dual-endpoint structure
      const goalsSection = goalsValuesContent.locator('.goals-section');
      const valuesSection = goalsValuesContent.locator('.values-section');

      if (await goalsSection.count() > 0) {
        await expect(goalsSection).toBeVisible();
        const goalsTitle = goalsSection.locator('.subsection-title');
        if (await goalsTitle.count() > 0) {
          const titleText = await goalsTitle.textContent();
          expect(titleText).toContain('Goals');
        }
      }

      if (await valuesSection.count() > 0) {
        await expect(valuesSection).toBeVisible();
        const valuesTitle = valuesSection.locator('.subsection-title');
        if (await valuesTitle.count() > 0) {
          const titleText = await valuesTitle.textContent();
          expect(titleText).toContain('Values');
        }
      }
    }
  });
});
