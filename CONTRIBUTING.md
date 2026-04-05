# Contributing to jmAgent

Thank you for interest in contributing to jmAgent! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the code, not the person
- Help others learn and grow

## Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub
# Clone your fork
git clone https://github.com/yourusername/jmAgent.git
cd jmAgent

# Add upstream remote
git remote add upstream https://github.com/original/jmAgent.git
```

### 2. Create Development Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Install development tools
pip install pytest black flake8 mypy
```

### 3. Create Feature Branch

```bash
# Update from upstream
git fetch upstream
git rebase upstream/main

# Create feature branch
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

## Development Workflow

### Writing Code

1. **Follow Python Style Guide** (PEP 8)
   - Use Black for formatting: `black src/`
   - Check linting: `flake8 src/`
   - Run type checker: `mypy src/`

2. **Write Tests First** (Test-Driven Development)
   - Add tests in `tests/` directory
   - Use pytest fixtures
   - Aim for >80% coverage
   - Run: `pytest tests/ -v`

3. **Document Your Code**
   - Add docstrings to functions/classes
   - Include type hints
   - Add comments for complex logic

4. **Keep Commits Clean**
   - One logical change per commit
   - Use descriptive commit messages
   - Reference issues: "Fixes #123"

### Running Tests

```bash
# Run all tests
python3 -m pytest tests/ -v

# Run specific test file
python3 -m pytest tests/test_agent.py -v

# Run single test
python3 -m pytest tests/test_agent.py::test_agent_init -v

# Run with coverage
python3 -m pytest tests/ --cov=src --cov-report=html

# Run specific test class
python3 -m pytest tests/test_agent.py::TestJmAgent -v
```

### Code Quality Checks

```bash
# Format code
black src/

# Check linting
flake8 src/ --max-line-length=100

# Type checking
mypy src/ --ignore-missing-imports

# Combined check
black src/ && flake8 src/ && mypy src/ && pytest tests/ -v
```

## Areas for Contribution

### Bug Fixes
- Report bugs with clear reproduction steps
- Include expected vs actual behavior
- Provide environment details

### Features
- Check PLAN.md and CLAUDE.md for roadmap
- Discuss in issues before implementation
- Follow existing architecture patterns

### Documentation
- Improve README.md clarity
- Add examples to docstrings
- Create tutorials for complex features
- Update RELEASE_NOTES.md

### Tests
- Add tests for new features
- Improve test coverage
- Add edge case tests
- Performance tests

### Performance
- Profile code to identify bottlenecks
- Optimize token usage
- Reduce API calls
- Cache where appropriate

## Pull Request Process

### 1. Before Submitting

```bash
# Update from upstream
git fetch upstream
git rebase upstream/main

# Run quality checks
black src/ && flake8 src/ && mypy src/

# Run tests
pytest tests/ -v

# Ensure git is clean
git status
```

### 2. Commit and Push

```bash
# Create descriptive commits
git add src/my_change.py
git commit -m "feat: Add feature X for better Y

- Detail 1
- Detail 2
- Closes #123"

# Push to your fork
git push origin feature/your-feature-name
```

### 3. Create Pull Request

- Use descriptive title
- Reference related issues
- Include:
  - Description of changes
  - Why changes are needed
  - Testing performed
  - Breaking changes (if any)
- Request review from maintainers

### 4. Review and Feedback

- Respond to feedback promptly
- Make requested changes
- Push updates to same branch
- Resolve conversations
- Request re-review when ready

## Commit Message Guidelines

Use conventional commits:

```
type(scope): subject

body

footer
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting (no code change)
- `refactor`: Code restructuring (no feature/fix)
- `perf`: Performance improvement
- `test`: Adding or updating tests
- `chore`: Maintenance (dependencies, configs)

### Examples

```bash
git commit -m "feat(generate): Add streaming support for large outputs"
git commit -m "fix(auth): Handle IAM credential refresh properly"
git commit -m "docs: Update installation instructions"
git commit -m "test(metrics): Add cost calculation tests"
```

## Code Structure

### Project Organization

```
src/
├── agent.py              # Core agent class
├── cli.py               # CLI entry point
├── auth/                # AWS Bedrock authentication
├── models/              # Data classes
├── prompts/             # System prompts
├── actions/             # Action implementations
├── config/              # Configuration management
├── monitoring/          # Metrics and monitoring
├── audit/               # Audit logging
├── plugins/             # Plugin system
├── errors/              # Custom exceptions
└── utils/               # Utility functions

tests/
├── test_agent.py
├── test_cli.py
├── test_auth.py
└── test_integration.py
```

### Adding New Features

1. **Create Action Module** (if new action)
   - File: `src/actions/my_action.py`
   - Test: `tests/test_my_action.py`

2. **Update CLI** (if new command)
   - Add command to `src/cli.py`
   - Add test to `tests/test_cli.py`

3. **Update Prompts** (if new prompt template)
   - Add to `src/prompts/my_action.py`
   - Document in PHASE4_FEATURES.md

4. **Update Documentation**
   - Add to README.md
   - Update CLAUDE.md
   - Update RELEASE_NOTES.md

## Testing Guidelines

### Unit Tests

```python
import pytest
from src.agent import JmAgent

class TestMyFeature:
    @pytest.fixture
    def agent(self):
        return JmAgent()
    
    def test_feature_basic(self, agent):
        result = agent.feature()
        assert result is not None
    
    def test_feature_with_params(self, agent):
        result = agent.feature(param="value")
        assert result == "expected"
```

### Integration Tests

```python
@pytest.mark.integration
def test_full_workflow():
    agent = JmAgent()
    # Test complete workflow
    pass
```

### Async Tests

```python
@pytest.mark.asyncio
async def test_async_feature():
    agent = JmAgent()
    result = await agent.async_method()
    assert result is not None
```

## Documentation Standards

### Docstrings

```python
def my_function(param1: str, param2: int) -> dict:
    """
    Brief description of what function does.
    
    Longer description if needed, explaining the approach
    and any important details.
    
    Args:
        param1: Description of param1
        param2: Description of param2
    
    Returns:
        Description of return value
    
    Raises:
        ValueError: When something is invalid
    
    Examples:
        >>> result = my_function("test", 42)
        >>> print(result)
    """
    pass
```

### Comments

```python
# Use comments for "why", not "what"
# The code shows what, comments explain why

# BAD: i += 1  # increment i
# GOOD: i += 1  # skip header row in CSV
```

## Performance Considerations

1. **Token Usage** - Minimize input tokens
2. **API Calls** - Cache results where possible
3. **File I/O** - Batch operations
4. **Async** - Use async for I/O operations
5. **Memory** - Stream large files

## Security Considerations

1. **Credentials** - Never log credentials
2. **API Keys** - Use environment variables
3. **Input Validation** - Validate all inputs
4. **Path Traversal** - Validate file paths
5. **Error Messages** - Don't expose sensitive info

## Release Process

### Versioning

Uses Semantic Versioning: MAJOR.MINOR.PATCH

- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes

### Release Checklist

1. Update version in setup.py and src/__init__.py
2. Update RELEASE_NOTES.md
3. Create git tag: `git tag v1.x.x`
4. Push tag: `git push origin v1.x.x`
5. Create release on GitHub

## Questions or Need Help?

1. **Documentation** - Check README.md and docs/
2. **Issues** - Search existing issues
3. **Discussions** - Create discussion thread
4. **Email** - Contact project maintainers

## Additional Resources

- [PEP 8 Style Guide](https://www.python.org/dev/peps/pep-0008/)
- [Python Docstring Conventions](https://www.python.org/dev/peps/pep-0257/)
- [Semantic Versioning](https://semver.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Git Workflow](https://git-scm.com/book/en/v2)

## License

By contributing to jmAgent, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to jmAgent! Your help makes this project better.
