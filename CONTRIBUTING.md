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

### Prerequisites

- Python 3.8+
- [uv](https://github.com/astral-sh/uv) (Python package manager)
- Git

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd cloud-cert-renewer

# Install dependencies
uv sync --extra dev

# Install pre-commit hooks
uv run pre-commit install
```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 2. Make Changes

- Follow the code style guidelines (see below)
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

```
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

```
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

### Python Code

- Follow PEP 8 style guide
- Use `ruff` for linting and formatting
- Maximum line length: 88 characters (Black default)
- Use type hints where appropriate

```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check .
```

### YAML Files

- Use `yamllint` for YAML file checking
- Follow consistent indentation (2 spaces)
- Use quotes for strings when needed

```bash
# Check YAML files
uv run yamllint .
```

## Testing

- Write tests for all new features
- Ensure all existing tests pass
- Aim for good test coverage

```bash
# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=cloud_cert_renewer --cov-report=html
```

## Pull Request Checklist

Before submitting a pull request, ensure:

- [ ] All code follows the English language policy
- [ ] All comments and docstrings are in English
- [ ] All commit messages are in English
- [ ] Code is properly formatted (`ruff format .`)
- [ ] Code passes linting (`ruff check .`)
- [ ] All tests pass (`pytest`)
- [ ] Documentation is updated if needed
- [ ] Pre-commit hooks pass (`pre-commit run --all-files`)
- [ ] Changes are backward compatible (or migration guide is provided)

## Code Review Process

1. All pull requests require at least one approval
2. Code reviews will verify:
   - Code quality and style
   - Test coverage
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
