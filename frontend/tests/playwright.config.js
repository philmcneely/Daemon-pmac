import { defineConfig, devices } from '@playwright/test';

/**
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  testDir: './e2e',
  /* Run tests in files in parallel */
  fullyParallel: true,
  /* Fail the build on CI if you accidentally left test.only in the source code. */
  forbidOnly: !!process.env.CI,
  /* Retry on CI only */
  retries: process.env.CI ? 2 : 0,
  /* Opt out of parallel tests on CI. */
  workers: process.env.CI ? 1 : undefined,
  /* Reporter to use. See https://playwright.dev/docs/test-reporters */
  reporter: process.env.CI ? [['html'], ['github']] : [['html']],
  /* Shared settings for all the projects below. See https://playwright.dev/docs/api/class-testoptions. */
  use: {
    /* Base URL to use in actions like `await page.goto('/')`. */
    baseURL: 'http://localhost:8006',
    /* Collect trace when retrying the failed test. See https://playwright.dev/docs/trace-viewer */
    trace: 'on-first-retry',
    /* Take screenshots on failure */
    screenshot: 'only-on-failure',
    /* Record video on failure */
    video: 'retain-on-failure',
  },

  /* Configure projects for major browsers */
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
      // Run all tests in Chrome for comprehensive coverage
    },

    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
      // Run only content verification test for cross-browser compatibility
      testMatch: '**/single-user.spec.js',
      grep: /should load and display About section/,
    },

    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
      // Run only content verification test for cross-browser compatibility
      testMatch: '**/single-user.spec.js',
      grep: /should load and display About section/,
    },

    /* Test against mobile viewports. */
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
      // Run only content verification test for mobile compatibility
      testMatch: '**/single-user.spec.js',
      grep: /should load and display About section/,
    },
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 12'] },
      // Run only content verification test for mobile compatibility
      testMatch: '**/single-user.spec.js',
      grep: /should load and display About section/,
    },
  ],

  /* Run your local dev server before starting the tests */
  webServer: [
    {
      command: 'python frontend_server.py',
      port: 8006,
      reuseExistingServer: !process.env.CI,
      cwd: '../..',
    },
    {
      command: 'python -m uvicorn app.main:app --host 0.0.0.0 --port 8007',
      port: 8007,
      reuseExistingServer: !process.env.CI,
      cwd: '../..',
    }
  ],

  /* Global test timeout */
  timeout: 30000,

  /* Expect timeout for assertions */
  expect: {
    timeout: 10000,
  },
});
