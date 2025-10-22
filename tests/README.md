# Void Bot Testing Framework

This document describes the comprehensive testing framework for the Void Bot project.

## Overview

The testing framework provides:
- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test interactions between components
- **End-to-End Tests**: Test complete workflows
- **Code Coverage**: Track test coverage
- **Linting**: Code quality checks
- **Security Scanning**: Vulnerability detection
- **CI/CD Pipeline**: Automated testing on GitHub Actions

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Unit tests
│   ├── test_config_loader.py
│   ├── test_utils.py
│   └── test_notification_db.py
├── integration/             # Integration tests
│   └── test_tools.py
├── e2e/                     # End-to-end tests
│   └── test_workflows.py
├── fixtures/                # Test fixtures
└── data/                    # Test data files
```

## Prerequisites

- **Python 3.8+** - Required for running tests
- **Virtual Environment** - Recommended for isolated testing

## Setup

### 1. Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
# Install production dependencies
pip install -r requirements.txt

# Install test dependencies
pip install -r requirements-test.txt
```

## Running Tests

### Using the Test Runner

```bash
# Run all tests
python run_tests.py

# Run specific test types
python run_tests.py --type unit
python run_tests.py --type integration
python run_tests.py --type e2e

# Run with verbose output
python run_tests.py --verbose

# Run tests in parallel
python run_tests.py --parallel

# Run all checks (tests + linting + security)
python run_tests.py --all-checks
```

### Using pytest Directly

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_config_loader.py

# Run specific test class
pytest tests/unit/test_config_loader.py::TestConfigLoader

# Run specific test method
pytest tests/unit/test_config_loader.py::TestConfigLoader::test_init_with_existing_config

# Run with coverage
pytest --cov=. --cov-report=html

# Run tests in parallel
pytest -n auto
```

## Test Categories

### Unit Tests (`tests/unit/`)

Test individual components in isolation:
- Configuration loading
- Utility functions
- Database operations
- Individual tool functions

**Markers**: `@pytest.mark.unit`

### Integration Tests (`tests/integration/`)

Test interactions between components:
- Tool system integration
- API interactions
- Configuration with external services

**Markers**: `@pytest.mark.integration`

### End-to-End Tests (`tests/e2e/`)

Test complete workflows:
- Notification processing workflow
- Configuration loading workflow
- Queue management workflow
- Error recovery workflows

**Markers**: `@pytest.mark.e2e`

## Test Fixtures

The `conftest.py` file provides shared fixtures:

- `mock_config`: Mock configuration data
- `mock_config_file`: Temporary config file
- `mock_env_vars`: Mock environment variables
- `mock_letta_client`: Mock Letta client
- `mock_bluesky_client`: Mock Bluesky client
- `mock_x_client`: Mock X client
- `sample_notification`: Sample notification data
- `sample_thread`: Sample thread data
- `temp_dir`: Temporary directory for test isolation
- `frozen_time`: Freeze time for consistent testing

## Configuration

### pytest.ini

Main pytest configuration:
- Test discovery patterns
- Output options
- Coverage settings
- Custom markers
- Warning filters

### Coverage Configuration

Coverage is configured to:
- Exclude test files and virtual environments
- Generate HTML and XML reports
- Require 80% minimum coverage
- Exclude certain patterns (abstract methods, etc.)

## Code Quality

### Linting

```bash
# Run linting
python run_tests.py --lint

# Or run individual tools
flake8 .
mypy . --ignore-missing-imports
bandit -r . -f json -o reports/bandit.json
```

### Security Scanning

```bash
# Run security scan
python run_tests.py --security

# Or run individual tools
safety check --json --output reports/safety.json
```

## CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/ci.yml`) runs:

1. **Test Matrix**: Tests on multiple OS and Python versions
2. **Linting**: Code quality checks
3. **Security**: Vulnerability scanning
4. **Coverage**: Upload coverage reports to Codecov
5. **Build**: Create distribution packages
6. **Deploy**: Deploy to production (on main branch)

## Test Data

### Sample Data

Test fixtures provide realistic sample data:
- Bluesky notifications
- X mentions and users
- Thread structures
- Configuration data

### Mock Services

External services are mocked to:
- Avoid API rate limits
- Ensure test reliability
- Enable offline testing
- Control test scenarios

## Best Practices

### Writing Tests

1. **Use descriptive test names**: `test_config_loader_handles_missing_file`
2. **One assertion per test**: Focus on single behavior
3. **Use fixtures**: Reuse common setup
4. **Mock external dependencies**: Isolate units under test
5. **Test edge cases**: Empty inputs, error conditions
6. **Use parametrized tests**: Test multiple scenarios

### Test Organization

1. **Group related tests**: Use test classes
2. **Separate concerns**: Unit vs integration vs e2e
3. **Use markers**: Categorize tests by type
4. **Keep tests independent**: No test should depend on another

### Performance

1. **Use parallel execution**: `pytest -n auto`
2. **Mock slow operations**: Database, API calls
3. **Use fixtures efficiently**: Scope appropriately
4. **Clean up resources**: Use context managers

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure virtual environment is activated
2. **Missing dependencies**: Run `pip install -r requirements-test.txt`
3. **Test failures**: Check test data and mock setup
4. **Coverage issues**: Verify source paths in pytest.ini

### Debug Mode

```bash
# Run with debug output
pytest -v -s --tb=long

# Run single test with debug
pytest tests/unit/test_config_loader.py::TestConfigLoader::test_init_with_existing_config -v -s
```

## Reports

Test reports are generated in the `reports/` directory:
- `pytest-report.html`: HTML test report
- `junit.xml`: JUnit XML format
- `htmlcov/`: Coverage HTML report
- `coverage.xml`: Coverage XML report
- `bandit.json`: Security scan results
- `safety.json`: Dependency vulnerability scan

## Contributing

When adding new tests:

1. Follow the existing structure
2. Use appropriate test markers
3. Add fixtures for reusable data
4. Update this documentation
5. Ensure tests pass in CI/CD

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [Factory Boy Documentation](https://factoryboy.readthedocs.io/)
- [Faker Documentation](https://faker.readthedocs.io/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
