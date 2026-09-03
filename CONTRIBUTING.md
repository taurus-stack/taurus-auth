# Contributing to Taurus Auth

Thank you for your interest in contributing to Taurus Auth! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check the issue list as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

* Use a clear and descriptive title
* Describe the exact steps which reproduce the problem
* Provide specific examples to demonstrate the steps
* Describe the behavior you observed after following the steps
* Explain which behavior you expected to see instead and why
* Include logs and stack traces if possible

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

* Use a clear and descriptive title
* Provide a step-by-step description of the suggested enhancement
* Provide specific examples to demonstrate the steps
* Describe the current behavior and explain which behavior you expected to see instead
* Explain why this enhancement would be useful

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`poetry run pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Development Setup

### Prerequisites

- Python 3.10+
- Poetry
- MySQL/MariaDB
- Redis

### Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/taurus-auth.git
cd taurus-auth

# Install dependencies
poetry install

# Copy environment file
cp .env.example .env

# Edit .env with your settings

# Run migrations
poetry run python manage.py migrate

# Run tests
poetry run pytest
```

### Code Style

We use the following tools to maintain code quality:

- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking

```bash
# Format code
poetry run black .
poetry run isort .

# Run linters
poetry run flake8
poetry run mypy ticket/
```

### Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=ticket

# Run specific test
poetry run pytest test_jwt_auth.py
```

## Project Structure

```
taurus-auth/
├── taurus_auth/          # Django project configuration
│   ├── settings.py       # Project settings
│   ├── urls.py           # Main URL routing
│   ├── wsgi.py           # WSGI configuration
│   └── asgi.py           # ASGI configuration
├── ticket/               # Ticket authentication app
│   ├── models.py         # Data models
│   ├── views.py          # API views
│   ├── serializers.py    # Serializers
│   ├── services.py       # Business logic
│   ├── middleware.py     # Security middleware
│   ├── urls.py           # App URL routing
│   └── utils/            # Utilities
│       └── jwt_helper.py # JWT utilities
├── manage.py             # Django management script
├── pyproject.toml        # Poetry configuration
└── test_jwt_auth.py      # JWT tests
```

## Commit Messages

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Build process or auxiliary tool changes

Example:
```
feat(ticket): add support for custom ticket metadata
```

## License

By contributing, you agree that your contributions will be licensed under the GNU Affero General Public License v3.0.
