# Frontend E2E Tests

This directory contains comprehensive end-to-end tests for the Daemon portfolio frontend using Playwright.

## 🚀 Quick Start

### Prerequisites
- Node.js 16+
- Python 3.11+
- API server dependencies installed (`pip install -r requirements.txt` from project root)

### Installation
```bash
cd frontend/tests
npm install
npx playwright install
```

### Running Tests
```bash
# Run all tests
./run-tests.sh

# Run specific test suite
./run-tests.sh single-user
./run-tests.sh multi-user

# Run with visible browser
./run-tests.sh --headed

# Debug mode
./run-tests.sh --debug api-integration

# Generate HTML report
./run-tests.sh --report
```

## 📋 Test Suites

### 1. Single User Mode Tests (`single-user.spec.js`)
**Purpose**: Validates single-user portfolio functionality
- Portfolio homepage loading
- Hero section population
- Section content loading (About, Experience, Skills, Projects, Personal Story)
- Navigation between sections
- Contact section functionality
- API error handling
- Mobile responsiveness
- Deep linking to sections
- Meta tags and SEO elements

### 2. Multi User Mode Tests (`multi-user.spec.js`)
**Purpose**: Validates multi-user mode detection and user selection
- Multi-user mode detection
- User selection interface
- User card display with correct information
- User portfolio loading after selection
- Back to users functionality
- Portfolio structure reset between users
- Keyboard navigation in user selection
- Mobile responsive user selection
- API error handling during user selection
- Loading states during user transitions

### 3. API Integration Tests (`api-integration.spec.js`)
**Purpose**: Tests frontend-backend communication and error scenarios
- System info API connection
- API server unavailable scenarios
- Slow API response handling
- Malformed API response handling
- API request retry mechanisms
- Partial API failure handling
- Network timeout handling
- CORS error handling
- Intermittent connectivity scenarios
- Contextual error messaging

### 4. Performance Tests (`performance.spec.js`)
**Purpose**: Validates loading performance and resource optimization
- Initial page load timing
- Resource loading efficiency
- Concurrent section loading
- Responsive interactions during loading
- Image and media optimization
- Memory usage during extended use
- API call pattern optimization
- Smooth user experience during updates
- Large content volume handling
- Slow network performance

### 5. Accessibility Tests (`accessibility.spec.js`)
**Purpose**: Ensures WCAG 2.1 AA compliance and screen reader compatibility
- Semantic HTML structure
- Full keyboard navigation support
- ARIA labels and roles validation
- Color contrast requirements
- Screen reader compatibility
- 200% zoom support without horizontal scrolling
- Focus management
- Accessible error messages
- High contrast mode support
- Form accessibility (if forms exist)

## 🏗️ Test Architecture

### Configuration
- **Base URL**: `http://localhost:8006` (Frontend)
- **API URL**: `http://localhost:8007` (Backend)
- **Browsers**: Chrome, Firefox, Safari, Mobile Chrome, Mobile Safari
- **Retry Strategy**: 2 retries on CI, 0 locally
- **Timeouts**: 30s global, 10s assertions

### Test Helpers (`helpers/test-setup.js`)
Utility functions for common test patterns:
- `setupSingleUser()` - Configure single-user mode
- `setupMultiUser()` - Configure multi-user mode
- `mockEndpointData()` - Mock API responses
- `waitForPortfolioLoad()` - Wait for complete loading
- `selectUser()` - User selection in multi-user mode
- `navigateToSection()` - Section navigation
- `mockAPIError()` - Simulate API failures
- `createSampleContent()` - Generate test data

### Test Data Management
Tests use mocked API responses to ensure consistent scenarios:
- User data mocking for single/multi-user modes
- Endpoint content mocking for section tests
- Error scenario simulation
- Network condition simulation

## 🎯 Running in Different Modes

### Development Mode
```bash
# Quick test run with visible browser
./run-tests.sh --headed

# Debug specific failing test
./run-tests.sh --debug single-user

# Setup servers only (for manual testing)
./run-tests.sh --setup-only
```

### CI/CD Mode
```bash
# Automated CI run
./run-tests.sh --ci

# With HTML report generation
./run-tests.sh --ci --report
```

### Custom Configuration
```bash
# Custom ports
./run-tests.sh --port 3000 --api-port 8000

# Extended timeout for slower environments
./run-tests.sh --timeout 90000
```

## 📊 Test Reports

### HTML Reports
Generated in `playwright-report/` directory:
- Test execution timeline
- Screenshots of failures
- Video recordings of failed tests
- Detailed error traces
- Performance metrics

### CI Integration
- GitHub Actions workflow in `.github/workflows/frontend-e2e.yml`
- Automatic report uploads on test completion
- Artifact retention for 30 days
- Multi-browser testing matrix

## 🔧 Troubleshooting

### Common Issues

#### Port Conflicts
```bash
# Kill existing processes
./run-tests.sh --cleanup-only
# Or manually
pkill -f "uvicorn.*:8007"
pkill -f "frontend_server.*8006"
```

#### Browser Installation
```bash
# Reinstall Playwright browsers
npx playwright install --with-deps
```

#### API Connection Issues
```bash
# Verify API server
curl http://localhost:8007/health

# Check frontend server
curl http://localhost:8006/
```

#### Test Debugging
```bash
# Debug mode with breakpoints
./run-tests.sh --debug --headed

# Run single test file
npx playwright test single-user.spec.js --headed

# Verbose output
npx playwright test --reporter=line
```

### Environment Variables
- `CI=true` - Enables CI-specific behaviors
- `FRONTEND_PORT` - Frontend server port
- `API_PORT` - API server port
- `TEST_TIMEOUT` - Global test timeout

## 🎨 Writing New Tests

### Test Structure
```javascript
import { test, expect } from '@playwright/test';
import { setupSingleUser, waitForPortfolioLoad } from './helpers/test-setup.js';

test.describe('Feature Group', () => {
  test.beforeEach(async ({ page }) => {
    await setupSingleUser(page);
  });

  test('should validate specific behavior', async ({ page }) => {
    // Given: Setup condition
    await page.goto('/');

    // When: Perform action
    await waitForPortfolioLoad(page);

    // Then: Verify result
    await expect(page.locator('#portfolio')).toBeVisible();
  });
});
```

### Best Practices
- Use descriptive test names with Given-When-Then structure
- Leverage helper functions for common operations
- Mock external dependencies consistently
- Test both happy path and error scenarios
- Include accessibility checks in UI tests
- Use appropriate timeouts for different operations
- Clean up state between tests

## 📚 Additional Resources

- [Playwright Documentation](https://playwright.dev/docs/intro)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [Frontend Portfolio Specification](../docs/FRONTEND_PORTFOLIO_SPECIFICATION.md)
- [API Requirements](../docs/API_REQUIREMENTS.md)

## Test Results

Tests provide detailed feedback with the following result types:

- **PASS** ✅: Test completed successfully
- **FAIL** ❌: Test failed and requires attention
- **WARNING** ⚠️: Test passed with concerns
- **INFO** ℹ️: Informational message

## Manual Testing Checklist

### Visual Design
- [ ] Professional, clean layout
- [ ] Consistent typography and spacing
- [ ] Proper color scheme and contrast
- [ ] Smooth animations and transitions
- [ ] Loading states are user-friendly

### Content Display
- [ ] All sections load content automatically
- [ ] No clicking required to view content
- [ ] Content is properly formatted (not raw JSON)
- [ ] Markdown-style content renders correctly
- [ ] Images and icons display properly

### Responsive Behavior
- [ ] Mobile layout adjusts appropriately
- [ ] Navigation collapses on small screens
- [ ] Content remains readable at all sizes
- [ ] Touch targets are appropriately sized
- [ ] Horizontal scrolling is avoided

### Performance
- [ ] Initial page load is under 3 seconds
- [ ] Smooth scrolling between sections
- [ ] No layout shift during content loading
- [ ] Minimal resource requests
- [ ] Proper caching behavior

### Accessibility
- [ ] Proper heading hierarchy
- [ ] Alt text for images
- [ ] Keyboard navigation works
- [ ] Color contrast meets WCAG standards
- [ ] Screen reader compatibility

### Browser Compatibility
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)
- [ ] Mobile Safari
- [ ] Chrome Mobile

## Known Issues

Document any known issues or limitations here:

1. **Placeholder Content**: Some sections may show placeholder text if API endpoints return empty data
2. **External Dependencies**: Requires Font Awesome and Google Fonts CDN access
3. **API Dependency**: Frontend requires backend API to be running for full functionality

## Future Improvements

- [ ] Add automated screenshot testing
- [ ] Implement visual regression testing
- [ ] Add performance monitoring
- [ ] Include accessibility audit tools
- [ ] Add cross-browser automated testing
