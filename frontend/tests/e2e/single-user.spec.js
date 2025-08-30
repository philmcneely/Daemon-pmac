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

    // Verify content is loaded (not default placeholder)
    const content = await aboutContent.textContent();
    expect(content?.trim().length).toBeGreaterThan(0);
    expect(content).not.toContain('Welcome to my personal portfolio');
    expect(content).not.toContain('will be displayed here');

    // Check for proper content structure
    const hasFormattedContent = await aboutContent.locator('p, h1, h2, h3, ul, ol').count() > 0;
    expect(hasFormattedContent).toBeTruthy();
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
    expect(content).not.toContain('will be displayed here');

    // Check for resume structure elements
    const hasResumeElements = await experienceContent.locator('.resume-container, .experience-item, .resume-header, .experience-list').count() > 0;
    expect(hasResumeElements).toBeTruthy();

    // Verify proper resume formatting if structured resume is present
    const resumeContainer = experienceContent.locator('.resume-container');
    if (await resumeContainer.count() > 0) {
      // Check for resume header elements
      const resumeHeader = resumeContainer.locator('.resume-header');
      if (await resumeHeader.count() > 0) {
        await expect(resumeHeader).toBeVisible();

        // Check for name and title
        const resumeName = resumeHeader.locator('.resume-name');
        const resumeTitle = resumeHeader.locator('.resume-title');

        if (await resumeName.count() > 0) {
          const nameText = await resumeName.textContent();
          expect(nameText?.trim().length).toBeGreaterThan(0);
        }
      }

      // Check for experience entries if present
      const experienceEntries = resumeContainer.locator('.experience-entry');
      if (await experienceEntries.count() > 0) {
        // Verify experience entry structure
        const firstEntry = experienceEntries.first();
        await expect(firstEntry).toBeVisible();

        // Check for position and company information
        const position = firstEntry.locator('.position, .experience-title');
        if (await position.count() > 0) {
          const positionText = await position.textContent();
          expect(positionText?.trim().length).toBeGreaterThan(0);
        }
      }

      // Check for skills section in resume if present
      const skillsSection = resumeContainer.locator('.skills-grid, .skill-category');
      if (await skillsSection.count() > 0) {
        await expect(skillsSection.first()).toBeVisible();
      }
    }
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

    // Verify content is loaded (not default placeholder)
    const content = await skillsContent.textContent();
    expect(content?.trim().length).toBeGreaterThan(0);
    expect(content).not.toContain('will be displayed here');
    expect(content).not.toContain('Skills information will be added soon');

    // Check for skills formatting structures
    const hasSkillsGrid = await skillsContent.locator('.skills-grid').count() > 0;
    const hasSkillItems = await skillsContent.locator('.skill-item').count() > 0;
    const hasSkillCategories = await skillsContent.locator('.skill-category').count() > 0;
    const hasSkillTags = await skillsContent.locator('.skill-tag').count() > 0;
    const hasFormattedContent = await skillsContent.locator('ul, ol, h1, h2, h3, h4, table').count() > 0;

    // At least one skills formatting structure should be present
    expect(hasSkillsGrid || hasSkillItems || hasSkillCategories || hasSkillTags || hasFormattedContent).toBeTruthy();

    // If skills matrix is present, check table formatting
    const skillsTable = skillsContent.locator('table');
    if (await skillsTable.count() > 0) {
      await expect(skillsTable.first()).toBeVisible();

      // Check for table headers
      const tableHeaders = skillsTable.locator('th');
      if (await tableHeaders.count() > 0) {
        const headerText = await tableHeaders.first().textContent();
        expect(headerText?.trim().length).toBeGreaterThan(0);
      }

      // Check for table data
      const tableData = skillsTable.locator('td');
      if (await tableData.count() > 0) {
        await expect(tableData.first()).toBeVisible();
      }
    }

    // If skill categories are present, verify structure
    const skillCategories = skillsContent.locator('.skill-category');
    if (await skillCategories.count() > 0) {
      const firstCategory = skillCategories.first();
      await expect(firstCategory).toBeVisible();

      // Check for category title
      const categoryTitle = firstCategory.locator('h4, h5, h6');
      if (await categoryTitle.count() > 0) {
        const titleText = await categoryTitle.textContent();
        expect(titleText?.trim().length).toBeGreaterThan(0);
      }
    }
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

    // Verify content is loaded (not default placeholder)
    const content = await projectsContent.textContent();
    expect(content?.trim().length).toBeGreaterThan(0);
    expect(content).not.toContain('will be displayed here');

    // Check for project formatting structures
    const hasProjectsContainer = await projectsContent.locator('.projects-container').count() > 0;
    const hasProjectItems = await projectsContent.locator('.project-item').count() > 0;
    const hasExperienceItems = await projectsContent.locator('.experience-item').count() > 0;
    const hasFormattedContent = await projectsContent.locator('h1, h2, h3, h4, ul, ol').count() > 0;

    // At least one project formatting structure should be present
    expect(hasProjectsContainer || hasProjectItems || hasExperienceItems || hasFormattedContent).toBeTruthy();

    // If project items are present, verify structure
    const projectItems = projectsContent.locator('.project-item, .experience-item');
    if (await projectItems.count() > 0) {
      const firstProject = projectItems.first();
      await expect(firstProject).toBeVisible();

      // Check for project content
      const projectContent = firstProject.locator('.project-content, .experience-content');
      if (await projectContent.count() > 0) {
        await expect(projectContent).toBeVisible();
        const projectText = await projectContent.textContent();
        expect(projectText?.trim().length).toBeGreaterThan(0);
      }

      // Check for technology tags if present
      const techTags = firstProject.locator('.tech-tag, .technology, .technologies');
      if (await techTags.count() > 0) {
        await expect(techTags.first()).toBeVisible();
      }

      // Check for project titles
      const projectTitle = firstProject.locator('.experience-title, .project-title, h3, h4');
      if (await projectTitle.count() > 0) {
        const titleText = await projectTitle.first().textContent();
        expect(titleText?.trim().length).toBeGreaterThan(0);
      }
    }
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

    // Verify content is loaded (not default placeholder)
    const content = await storyContent.textContent();
    expect(content?.trim().length).toBeGreaterThan(0);
    expect(content).not.toContain('will be displayed here');
    expect(content).not.toContain('Personal narrative and biography');

    // Check for story formatting structures
    const hasStoryContainer = await storyContent.locator('.personal-story-container').count() > 0;
    const hasStoryItems = await storyContent.locator('.story-item').count() > 0;
    const hasFormattedContent = await storyContent.locator('p, h1, h2, h3, h4, ul, ol').count() > 0;

    // At least one story formatting structure should be present
    expect(hasStoryContainer || hasStoryItems || hasFormattedContent).toBeTruthy();

    // If story items are present, verify structure
    const storyItems = storyContent.locator('.story-item');
    if (await storyItems.count() > 0) {
      const firstStory = storyItems.first();
      await expect(firstStory).toBeVisible();

      // Check for story content
      const storyText = firstStory.locator('.story-content');
      if (await storyText.count() > 0) {
        await expect(storyText).toBeVisible();
        const text = await storyText.textContent();
        expect(text?.trim().length).toBeGreaterThan(0);
      }
    }

    // Check for narrative elements
    const hasParagraphs = await storyContent.locator('p').count() > 0;
    if (hasParagraphs) {
      const firstParagraph = storyContent.locator('p').first();
      const paragraphText = await firstParagraph.textContent();
      expect(paragraphText?.trim().length).toBeGreaterThan(0);
    }
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

    // Verify content is present
    const content = await contactContent.textContent();
    expect(content?.trim().length).toBeGreaterThan(0);

    // Check for contact structure elements
    const hasContactMethods = await contactContent.locator('.contact-methods').count() > 0;
    const hasContactMethod = await contactContent.locator('.contact-method').count() > 0;
    const hasContactContent = await contactContent.locator('.contact-content').count() > 0;
    const hasFormattedContent = await contactContent.locator('p, h1, h2, h3, h4, ul, ol').count() > 0;

    // At least one contact formatting structure should be present
    expect(hasContactMethods || hasContactMethod || hasContactContent || hasFormattedContent).toBeTruthy();

    // If contact methods are present, verify structure
    const contactMethods = contactContent.locator('.contact-method');
    if (await contactMethods.count() > 0) {
      const firstMethod = contactMethods.first();
      await expect(firstMethod).toBeVisible();

      // Check for contact method content
      const methodText = await firstMethod.textContent();
      expect(methodText?.trim().length).toBeGreaterThan(0);
    }

    // Check for email links if present
    const emailLinks = contactContent.locator('a[href^="mailto:"]');
    if (await emailLinks.count() > 0) {
      await expect(emailLinks.first()).toBeVisible();
      const href = await emailLinks.first().getAttribute('href');
      expect(href).toContain('mailto:');
    }

    // Check for external links if present
    const externalLinks = contactContent.locator('a[href^="http"], a[href^="https"]');
    if (await externalLinks.count() > 0) {
      await expect(externalLinks.first()).toBeVisible();
    }
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

  test('should display Goals & Values section with content or default message', async ({ page }) => {
    // Given: Single-user portfolio is loaded
    await page.goto('/');
    await expect(page.locator('.loading-screen')).toBeHidden({ timeout: 10000 });

    // When: Goals & Values section loads
    const goalsValuesSection = page.locator('#goals-values');
    const goalsValuesContent = page.locator('#goalsValuesContent');

    // Then: Goals & Values section is visible
    await expect(goalsValuesSection).toBeVisible();
    await expect(goalsValuesContent).toBeVisible();

    // Verify content is present
    const content = await goalsValuesContent.textContent();
    expect(content?.trim().length).toBeGreaterThan(0);

    // Check if actual content is loaded or default message is shown
    const hasDefaultMessage = content?.includes('Goals and values will be displayed here');
    const hasGoalsSection = await goalsValuesContent.locator('.goals-section').count() > 0;
    const hasValuesSection = await goalsValuesContent.locator('.values-section').count() > 0;
    const hasGoalsValuesContainer = await goalsValuesContent.locator('.goals-values-container').count() > 0;

    // Either default message OR actual content should be present
    expect(hasDefaultMessage || hasGoalsSection || hasValuesSection || hasGoalsValuesContainer).toBeTruthy();

    // If actual content is present, verify structure
    if (hasGoalsSection || hasValuesSection || hasGoalsValuesContainer) {
      // Should not show default message when content is present
      expect(hasDefaultMessage).toBeFalsy();

      // Check goals section if present
      const goalsSection = goalsValuesContent.locator('.goals-section');
      if (await goalsSection.count() > 0) {
        await expect(goalsSection).toBeVisible();

        // Check for goals title
        const goalsTitle = goalsSection.locator('.subsection-title');
        if (await goalsTitle.count() > 0) {
          const titleText = await goalsTitle.textContent();
          expect(titleText).toContain('Goals');
        }

        // Check for goals content
        const goalsItems = goalsSection.locator('.goals-item');
        if (await goalsItems.count() > 0) {
          await expect(goalsItems.first()).toBeVisible();
        }
      }

      // Check values section if present
      const valuesSection = goalsValuesContent.locator('.values-section');
      if (await valuesSection.count() > 0) {
        await expect(valuesSection).toBeVisible();

        // Check for values title
        const valuesTitle = valuesSection.locator('.subsection-title');
        if (await valuesTitle.count() > 0) {
          const titleText = await valuesTitle.textContent();
          expect(titleText).toContain('Values');
        }

        // Check for values content
        const valuesItems = valuesSection.locator('.values-item');
        if (await valuesItems.count() > 0) {
          await expect(valuesItems.first()).toBeVisible();
        }
      }
    }
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
