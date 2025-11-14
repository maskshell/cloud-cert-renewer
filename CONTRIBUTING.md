# Contributing to Cloud Certificate Renewer

Thank you for your interest in contributing to this project! This document provides guidelines and instructions for contributing.

## Language Policy

**All project content must be in English:**

- All code comments and docstrings must be written in English
- All documentation files (README.md, CHANGELOG.md, etc.) must be in English
- All commit messages must be in English
- All configuration file comments must be in English
- All error messages and log messages should be in English
- All variable names, function names, and class names should use English words (following Python naming conventions)

**Exceptions:**

- Proper nouns (brand names, product names, company names) should use their official/standard names (e.g., "Alibaba Cloud" is the official English brand name, not "阿里云")
- Test data or example values that are intentionally in other languages for testing purposes
- Strings that are explicitly designated as non-English content (e.g., translation files, language-specific prompts, multilingual content) should be preserved as-is, even if they contain mixed languages

**Guidelines for Contributors:**

- If you're not a native English speaker, don't worry - clear and simple English is preferred over complex grammar
- Use tools like spell checkers and grammar checkers if needed
- When in doubt, ask for review or use translation tools, but always have a native speaker or experienced contributor review the final text
- Focus on clarity and correctness over perfect grammar - the goal is effective communication

## Development Setup

For detailed environment setup, installation, and development tools, see [DEVELOPMENT.md](DEVELOPMENT.md).

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 2. Make Changes

- Follow the code style guidelines (see [DEVELOPMENT.md](DEVELOPMENT.md) for details)
- Write tests for new features
- Update documentation as needed
- Ensure all code follows the English language policy

### 3. Test Your Changes

```bash
# Run tests
uv run pytest

# Run linting
uv run ruff check .

# Run formatting check
uv run ruff format --check .

# Run pre-commit hooks
uv run pre-commit run --all-files
```

### 4. Commit Your Changes

Follow the commit message convention:

```text
type(scope): description

- List any breaking changes
- List environment variables or configuration items that need to be set
- Explain backward compatibility if applicable
```

**Commit types:**

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Test additions or changes
- `chore`: Maintenance tasks

**Example:**

```text
feat(auth): add STS credential provider support

- Add STSCredentialProvider class
- Support CLOUD_SECURITY_TOKEN environment variable
- Backward compatible with existing access_key method
```

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

## Code Style

For detailed code formatting, linting, and style guidelines, see [DEVELOPMENT.md](DEVELOPMENT.md).

## Testing

**All tests must follow the testing design principles defined in `testing-design-principles.mdc`.**

### Test Organization

Tests must be organized by design patterns, not by implementation details:

- Each design pattern should have its own dedicated test file
- Test files should mirror the design pattern structure of the codebase
- Tests should focus on testing the design pattern layer, not the underlying implementation

**Test File Naming Convention:**

- Factory Pattern: `test_*_factory.py`
- Strategy Pattern: `test_*_strategy.py`
- Template Method Pattern: `test_*_base.py`
- Adapter Pattern: `test_*_adapter.py`
- Integration tests: `test_integration.py`
- Utility tests: `test_utils.py`
- Client implementation tests: `test_clients.py`
- Configuration tests: `test_config.py`

### Test Coverage Requirements

**Minimum coverage requirements:**

- Design pattern layer: **100% coverage**
- Core business logic: **80%+ coverage**
- Utility functions: **80%+ coverage**
- Client implementations: **80%+ coverage**

### Mandatory Test Updates

**When making code changes, tests MUST be updated accordingly:**

1. **Adding New Design Pattern Implementation:**
   - Create corresponding test file following naming convention
   - Test all design pattern contracts and behaviors
   - Add integration tests if applicable

2. **Modifying Existing Design Pattern:**
   - Update corresponding test file
   - Ensure all existing tests still pass
   - Add new tests for new behaviors

3. **Test Update Checklist:**
   - [ ] All existing tests pass
   - [ ] New functionality has corresponding tests
   - [ ] Tests follow design pattern organization
   - [ ] Tests use appropriate mocks at design pattern boundaries
   - [ ] Test names are descriptive and follow conventions
   - [ ] Integration tests cover new workflows
   - [ ] Test coverage meets minimum requirements

### Running Tests

For detailed test execution commands and examples, see [DEVELOPMENT.md](DEVELOPMENT.md).

### Mock Usage Guidelines

- Mock external dependencies (cloud APIs, file system, network)
- Mock at design pattern boundaries, not at implementation details
- Use correct import paths for mocking (e.g., `cloud_cert_renewer.clients.alibaba.CdnCertRenewer`)

**See `testing-design-principles.mdc` for complete testing guidelines.**

## Pull Request Checklist

Before submitting a pull request, ensure:

- [ ] All code follows the English language policy
- [ ] All comments and docstrings are in English
- [ ] All commit messages are in English
- [ ] Code is properly formatted (`ruff format .`)
- [ ] Code passes linting (`ruff check .`)
- [ ] All tests pass (`pytest`)
- [ ] **Tests follow design pattern organization** (see Testing section)
- [ ] **Test coverage meets minimum requirements** (100% for design patterns, 80%+ for core logic)
- [ ] **New functionality has corresponding tests**
- [ ] **Tests use appropriate mocks at design pattern boundaries**
- [ ] Documentation is updated if needed
- [ ] Pre-commit hooks pass (`pre-commit run --all-files`)
- [ ] Changes are backward compatible (or migration guide is provided)

## Code Review Process

1. All pull requests require at least one approval
2. Code reviews will verify:
   - Code quality and style
   - **Test organization follows design patterns** (see `testing-design-principles.mdc`)
   - **Test coverage meets requirements** (100% for design patterns, 80%+ for core logic)
   - **Tests align with code changes** (mandatory test updates)
   - Documentation completeness
   - **Language policy compliance** (all content in English)
3. Address review comments promptly
4. Keep pull requests focused and reasonably sized

## Questions?

If you have questions or need help, please:

- Open an issue for discussion
- Check existing documentation
- Ask in pull request comments

Thank you for contributing!
