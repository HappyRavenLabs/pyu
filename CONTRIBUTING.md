# Contributing to pyu

Thank you for considering contributing to the pyu project!

## Branch Naming Strategy

- **Feature branches:** `f-<number>` (e.g., `f-101`)
- **Bugfix branches:** `b-<number>` (e.g., `b-202`)

Please use the appropriate prefix and a unique number for your branch name.

## Pre-commit Hooks

We use [pre-commit](https://pre-commit.com/) to maintain code quality. All contributors must install and configure pre-commit hooks before making commits.

### Installation

1. Install pre-commit (requires Python):
   ```bash
   pip install pre-commit
   ```
2. Install the hooks:
   ```bash
   pre-commit install
   ```
3. (Optional) Run hooks on all files:
   ```bash
   pre-commit run --all-files
   ```

### Configuration

The configuration file is `.pre-commit-config.yaml` in the project root. Hooks will run automatically on `git commit`.

## Contribution Steps

1. Fork the repository and clone your fork.
2. Create a new branch using the naming strategy above.
3. Install and configure pre-commit hooks.
4. Make your changes and commit (hooks will run automatically).
5. Push your branch and open a pull request.

## Code Style & Guidelines

- Follow existing code style and conventions.
- Write clear commit messages.
- Add tests for new features or bug fixes.

## Need Help?

Open an issue or contact the maintainers for assistance.

---
Happy contributing!
