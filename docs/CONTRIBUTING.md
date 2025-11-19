# Contributing to Mew Assistant

Thank you for your interest in contributing to Mew Assistant! 🎉

This document provides guidelines for contributing to the project.

---

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Code Style](#code-style)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Feature Requests](#feature-requests)

---

## 🤝 Code of Conduct

Be respectful, inclusive, and professional. We're building this for special needs families and caregivers.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- Podman or Docker
- Git
- PostgreSQL (via Podman) or SQLite

---

## 🛠️ Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/mew-assistant.git
cd mew-assistant
```

### 2. Create Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install all dependencies including dev tools
pip install -r requirements.txt

# Install pre-commit hooks
pip install pre-commit
pre-commit install
```

### 4. Set Up Database

```bash
# Copy environment template
cp .env.example .env

# Start PostgreSQL with Podman
./podman-start.sh

# Or use SQLite (for development)
# Edit .env and set: DATABASE_URL=sqlite:///./mew_assistant.db
```

### 5. Run the Application

```bash
uvicorn app.main:app --reload
```

Visit http://localhost:8000/docs for API documentation.

---

## 💡 How to Contribute

### Types of Contributions

We welcome:

- 🐛 Bug fixes
- ✨ New features
- 📚 Documentation improvements
- 🧪 Test coverage improvements
- 🎨 UI/UX enhancements
- 🌐 Translations
- ♿ Accessibility improvements

### Contribution Workflow

1. **Create an issue** (if one doesn't exist)
2. **Fork the repository**
3. **Create a feature branch**: `git checkout -b feature/your-feature-name`
4. **Make your changes**
5. **Write/update tests**
6. **Run tests**: `pytest`
7. **Commit with clear messages**: `git commit -m "feat: add new feature"`
8. **Push to your fork**: `git push origin feature/your-feature-name`
9. **Open a Pull Request**

---

## 🎨 Code Style

We use automated tools to maintain code quality:

### Python Style Guide

- **Formatter**: Black (line length: 100)
- **Import Sorter**: isort (Black-compatible profile)
- **Linter**: Flake8
- **Type Checker**: MyPy

### Pre-commit Hooks

Pre-commit hooks run automatically on every commit:

```bash
# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

### Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new session type
fix: resolve cooldown calculation bug
docs: update API documentation
test: add tests for message service
chore: update dependencies
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding/updating tests
- `chore`: Maintenance tasks
- `refactor`: Code refactoring
- `perf`: Performance improvements

---

## 🧪 Testing

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_sessions.py

# Run specific test
pytest tests/test_sessions.py::test_create_session
```

### Writing Tests

- Place tests in `tests/` directory
- Name test files: `test_*.py`
- Name test functions: `test_*`
- Use fixtures from `conftest.py`
- Aim for >80% code coverage

Example:

```python
def test_create_session(client):
    """Test creating a new session"""
    response = client.post(
        "/mew/session",
        json={
            "user_id": "test_user",
            "session_type": "tutoring",
            "title": "Math Homework",
            "priority": "normal"
        }
    )
    assert response.status_code == 201
    assert response.json()["status"] == "pending"
```

---

## 📥 Pull Request Process

### Before Submitting

1. ✅ Update tests
2. ✅ Run `pytest` - all tests pass
3. ✅ Run `pre-commit run --all-files` - no errors
4. ✅ Update documentation if needed
5. ✅ Update CHANGELOG.md

### PR Template

When opening a PR, include:

- **Description**: What does this PR do?
- **Issue**: Fixes #123 (if applicable)
- **Type**: Bug fix / Feature / Documentation
- **Testing**: How was this tested?
- **Screenshots**: (if UI changes)
- **Checklist**: Did you run tests, linting, etc.?

### Review Process

1. Automated checks run (GitHub Actions)
2. Maintainers review code
3. Address feedback
4. PR is merged

---

## 🐛 Reporting Bugs

### Before Reporting

- Search existing issues
- Try the latest version
- Gather reproduction steps

### Bug Report Should Include

- **Description**: Clear summary
- **Steps to Reproduce**: Numbered steps
- **Expected Behavior**: What should happen
- **Actual Behavior**: What actually happens
- **Environment**: OS, Python version, etc.
- **Logs**: Relevant error messages

Use the bug report template in `.github/ISSUE_TEMPLATE/`

---

## ✨ Feature Requests

We love new ideas! When requesting a feature:

- **Use Case**: Describe the problem
- **Proposed Solution**: How should it work?
- **Alternatives**: Other approaches considered?
- **Additional Context**: Screenshots, examples, etc.

Use the feature request template in `.github/ISSUE_TEMPLATE/`

---

## 📞 Questions?

- **GitHub Discussions**: For general questions
- **GitHub Issues**: For bugs and features
- **Email**: [Project email if available]

---

## 🙏 Thank You!

Your contributions help families and caregivers. Every bug fix, feature, and documentation improvement makes a difference!

---

**Built with ❤️ for special needs families**
