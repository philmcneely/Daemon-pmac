# Unit Tests

This directory contains unit tests created after commit 634c96d7e41004d64ef16fe907f8c2c981c9492a to improve test coverage.

## Test Files

### Working Tests
- `test_utils_comprehensive.py` - Comprehensive unit tests for utils.py
- `test_cli.py` - CLI command tests (unit tests with mocks)

### E2E Tests (moved here temporarily)
- `test_admin_comprehensive.py` - Admin router end-to-end tests
- `test_data_loader_comprehensive.py` - Data loader comprehensive tests
- `test_data_loader_simple.py` - Simple data loader tests
- `test_multi_user_import_comprehensive.py` - Multi-user import tests
- `test_multi_user_import_simple.py` - Simple multi-user import tests
- `test_resume_loader_simple.py` - Simple resume loader tests

### Legacy/Broken Tests
- `test_cli_broken.py` - Original CLI tests that had failures
- `test_data_loader.py` - Original data loader tests with database issues
- `test_multi_user_import.py` - Original multi-user import tests
- `test_resume_loader.py` - Original resume loader tests

## Notes

These tests were moved here to restore the original working test suite from commit 634c96d. The E2E tests should eventually be moved back to the main tests directory once proper database isolation is implemented.
