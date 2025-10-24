# Contributing to Sanctum Social

Thank you for your interest in contributing to Sanctum Social! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contributing Guidelines](#contributing-guidelines)
- [Code Standards](#code-standards)
- [Testing Requirements](#testing-requirements)
- [Documentation Standards](#documentation-standards)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)
- [Platform Development](#platform-development)
- [Memory](#memory)

## Code of Conduct

Sanctum Social is committed to providing a welcoming and inclusive environment for all contributors. By participating in this project, you agree to:

- Be respectful and inclusive in all interactions
- Provide constructive feedback and criticism
- Respect different viewpoints and experiences
- Focus on what is best for the community
- Show empathy towards other community members

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- A Letta Cloud account (for testing)
- Social media accounts for testing (Bluesky, X, Discord)

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/your-username/sanctum-social.git
   cd sanctum-social
   ```

3. Add the upstream repository:
   ```bash
   git remote add upstream https://github.com/actuallyrizzn/sanctum-social.git
   ```

## Development Setup

### 1. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
# Install main dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-test.txt

# Install pre-commit hooks (optional but recommended)
pip install pre-commit
pre-commit install
```

### 3. Set Up Configuration

```bash
# Copy example configuration
cp config/agent.yaml config.yaml

# Edit with your test credentials
# Note: Use test accounts, not production accounts
```

### 4. Run Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest --cov=. --cov-report=html tests/

# Run specific test categories
python -m pytest tests/unit/ -v
python -m pytest tests/integration/ -v
python -m pytest tests/e2e/ -v
```

## Contributing Guidelines

### Types of Contributions

We welcome various types of contributions:

- **Bug Fixes**: Fix issues and improve reliability
- **Feature Development**: Add new features and capabilities
- **Platform Support**: Add support for new social media platforms
- **Documentation**: Improve documentation and examples
- **Testing**: Add tests and improve test coverage
- **Performance**: Optimize performance and resource usage
- **Security**: Improve security and fix vulnerabilities

### Development Workflow

1. **Create a Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Your Changes**
   - Follow the code standards outlined below
   - Add tests for new functionality
   - Update documentation as needed

3. **Test Your Changes**
   ```bash
   # Run tests
   python -m pytest tests/ -v
   
   # Check code quality
   python -m flake8 .
   python -m black --check .
   python -m isort --check-only .
   ```

4. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

5. **Push and Create Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```

## Code Standards

### Python Style

- **PEP 8**: Follow PEP 8 style guidelines
- **Type Hints**: Use type hints for all function parameters and return values
- **Docstrings**: Include comprehensive docstrings for all functions and classes
- **Naming**: Use descriptive, clear variable and function names

### Code Formatting

We use automated formatting tools:

```bash
# Format code
python -m black .
python -m isort .

# Check formatting
python -m black --check .
python -m isort --check-only .
```

### Import Organization

- Standard library imports
- Third-party imports
- Local application imports

Example:
```python
import os
import sys
from typing import Dict, List, Optional

import requests
import yaml
from pydantic import BaseModel, Field

from core.config import get_config
from platforms.bluesky.utils import Client
```

### Error Handling

- Use specific exception types
- Include meaningful error messages
- Implement proper logging
- Handle edge cases gracefully

Example:
```python
try:
    result = api_call()
except requests.exceptions.HTTPError as e:
    logger.error(f"API call failed: {e}")
    raise Exception(f"Failed to fetch data: {str(e)}")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise
```

## Testing Requirements

### Test Coverage

- **Minimum Coverage**: 80% for new code
- **Critical Paths**: 100% coverage for core functionality
- **Platform Integration**: Comprehensive testing for platform-specific code

### Test Types

1. **Unit Tests**: Test individual functions and classes
2. **Integration Tests**: Test component interactions
3. **E2E Tests**: Test complete workflows
4. **Platform Tests**: Test platform-specific functionality

### Test Structure

```python
"""Tests for module_name."""
import pytest
from unittest.mock import patch, MagicMock
from your_module import YourClass, your_function


class TestYourClass:
    """Test the YourClass class."""
    
    def test_method_success(self):
        """Test successful method execution."""
        # Arrange
        instance = YourClass()
        
        # Act
        result = instance.method()
        
        # Assert
        assert result is not None
        assert result.expected_property == "expected_value"
    
    def test_method_error_handling(self):
        """Test error handling in method."""
        # Arrange
        instance = YourClass()
        
        # Act & Assert
        with pytest.raises(ValueError, match="Expected error message"):
            instance.method_with_error()
    
    @patch('your_module.external_dependency')
    def test_method_with_mock(self, mock_dependency):
        """Test method with mocked external dependency."""
        # Arrange
        mock_dependency.return_value = "mocked_value"
        instance = YourClass()
        
        # Act
        result = instance.method_with_dependency()
        
        # Assert
        assert result == "expected_result"
        mock_dependency.assert_called_once()
```

### Mocking Guidelines

- Mock external dependencies (APIs, file system, network)
- Use `patch` decorators for clean test isolation
- Verify mock calls and parameters
- Test both success and failure scenarios

## Documentation Standards

### Code Documentation

- **Docstrings**: Use Google-style docstrings
- **Type Hints**: Include type hints for all parameters and return values
- **Comments**: Explain complex logic and business rules

Example:
```python
def process_notification(notification: Dict[str, Any]) -> Optional[str]:
    """
    Process a social media notification and generate a response.
    
    Args:
        notification: Dictionary containing notification data with keys:
            - 'id': Unique notification identifier
            - 'text': Notification content
            - 'author': Author information
            - 'platform': Source platform ('bluesky', 'x', 'discord')
    
    Returns:
        Generated response text if processing succeeds, None otherwise.
        
    Raises:
        ValueError: If notification data is invalid.
        APIError: If external API calls fail.
    """
    # Implementation here
```

### Documentation Files

- **README.md**: Project overview and quick start
- **docs/**: Comprehensive documentation
- **API.md**: API reference
- **CONFIG.md**: Configuration guide
- **DEPLOYMENT.md**: Deployment instructions

### Documentation Style

- Use clear, concise language
- Include code examples
- Provide step-by-step instructions
- Update documentation with code changes

## Pull Request Process

### Before Submitting

1. **Ensure Tests Pass**: All tests must pass
2. **Check Coverage**: Maintain or improve test coverage
3. **Update Documentation**: Update relevant documentation
4. **Follow Style Guide**: Ensure code follows style guidelines
5. **Rebase**: Rebase on latest main branch

### Pull Request Template

```markdown
## Description
Brief description of changes.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] E2E tests added/updated
- [ ] All tests pass

## Platform Testing
- [ ] Bluesky functionality tested
- [ ] X (Twitter) functionality tested
- [ ] Discord functionality tested
- [ ] Cross-platform compatibility verified

## Documentation
- [ ] README updated
- [ ] API documentation updated
- [ ] Configuration guide updated
- [ ] Deployment guide updated

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] No breaking changes (or documented)
```

### Review Process

1. **Automated Checks**: CI/CD pipeline runs tests and checks
2. **Code Review**: Maintainers review code quality and functionality
3. **Testing**: Reviewers test functionality on their systems
4. **Approval**: At least one maintainer approval required
5. **Merge**: Maintainer merges after approval

## Issue Reporting

### Bug Reports

Use the bug report template:

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior.

**Expected behavior**
What you expected to happen.

**Environment**
- OS: [e.g., Ubuntu 20.04]
- Python version: [e.g., 3.9.7]
- Sanctum Social version: [e.g., 2.0.0]
- Platform: [e.g., Bluesky, X, Discord]

**Additional context**
Any other context about the problem.
```

### Feature Requests

Use the feature request template:

```markdown
**Is your feature request related to a problem?**
A clear description of what the problem is.

**Describe the solution you'd like**
A clear description of what you want to happen.

**Describe alternatives you've considered**
Alternative solutions or workarounds.

**Additional context**
Any other context about the feature request.
```

## Platform Development

### Adding New Platforms

To add support for a new social media platform:

1. **Create Platform Module**
   ```
   platforms/new_platform/
   ├── __init__.py
   ├── orchestrator.py
   ├── tools/
   │   ├── __init__.py
   │   ├── post.py
   │   ├── reply.py
   │   └── search.py
   └── utils.py
   ```

2. **Implement Core Interface**
   - Authentication handling
   - API client implementation
   - Error handling and retry logic
   - Rate limiting

3. **Add Platform Tools**
   - Post creation tools
   - Reply/threading tools
   - Search tools
   - User management tools

4. **Update Configuration**
   - Add platform configuration schema
   - Update configuration validation
   - Add platform-specific settings

5. **Add Tests**
   - Unit tests for all components
   - Integration tests for API interactions
   - E2E tests for complete workflows

6. **Update Documentation**
   - Platform setup guide
   - API documentation
   - Configuration examples

### Platform Requirements

Each platform must implement:

- **Authentication**: Secure credential handling
- **Rate Limiting**: Respect platform rate limits
- **Error Handling**: Robust error recovery
- **Session Management**: Proper session handling
- **Tool Registration**: Dynamic tool management
- **Monitoring**: Health checks and logging

## Memory

### Memory System Development

When working with the memory system:

1. **Understand Memory Types**
   - Core Memory: Always-available, limited-size
   - Recall Memory: Searchable conversation database
   - Archival Memory: Infinite-sized, semantic search

2. **Memory Block Management**
   - Create/update/delete memory blocks
   - Handle memory block templating
   - Implement memory cleanup

3. **Memory Search**
   - Implement semantic search
   - Handle search result ranking
   - Optimize search performance

4. **Memory Testing**
   - Test memory operations
   - Test memory search functionality
   - Test memory cleanup and maintenance

### Memory Best Practices

- Use appropriate memory types for different data
- Implement proper memory cleanup
- Handle memory errors gracefully
- Test memory operations thoroughly
- Document memory usage patterns

---

## Getting Help

- **Documentation**: Check the `docs/` directory
- **Issues**: Search existing issues on GitHub
- **Discussions**: Use GitHub Discussions for questions
- **Contact**: Reach out to maintainers for support

## Recognition

Contributors will be recognized in:
- **CONTRIBUTORS.md**: List of all contributors
- **Release Notes**: Credit in release announcements
- **Documentation**: Attribution in relevant documentation

Thank you for contributing to Sanctum Social! 🚀
