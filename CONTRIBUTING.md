# Contributing to md-nugget-notifier

Thank you for your interest in contributing to `md-nugget-notifier`! We welcome contributions of all kinds: bug fixes, documentation improvements, new features, and feedback.

---

## 🤝 Code of Conduct

We are committed to providing a friendly, safe, and welcoming environment for everyone, regardless of experience level, gender, identity, sexual orientation, disability, personal appearance, race, ethnicity, or religion.

### Expected Behavior
- **Be respectful and empathetic**: Treat all contributors and users with kindness and patience.
- **Use welcoming and inclusive language**: Be mindful of your words and tone in issues, discussions, and pull requests.
- **Give and accept constructive feedback gracefully**: Focus on what is best for the project and community.
- **Show appreciation**: Value the time and effort of other contributors and maintainers.

### Unacceptable Behavior
- Harassment, trolling, derogatory comments, or personal/political attacks.
- Publishing others' private information without explicit permission.
- Any conduct that could reasonably be considered inappropriate in a professional setting.

---

## 🛠️ Development Setup

### 1. Clone the repository
```bash
git clone https://github.com/hector6872/md-nugget-notifier.git
cd md-nugget-notifier
```

### 2. Create and activate a virtual environment (optional but recommended)
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install in editable mode
```bash
pip install -e .
```

---

## 🧪 Running Tests

Before submitting any changes, ensure the entire test suite passes:

```bash
python3 -m unittest discover tests -v
```

When adding new features or fixing bugs, please include corresponding unit tests in the `tests/` directory.

---

## 📋 Pull Request Guidelines

1. **Fork & Branch**: Create a feature branch off `main` (e.g., `feat/my-feature` or `fix/my-bugfix`).
2. **Zero Mandatory Dependencies**: Keep core functionality dependency-free (standard library only for core notification dispatching and parsing).
3. **Cross-Platform Compatibility**: Test or consider behavior across macOS, Linux, and Windows.
4. **Clean Commits**: Use clear, concise commit messages following [Conventional Commits](https://www.conventionalcommits.org/) (e.g., `feat: ...`, `fix: ...`, `docs: ...`, `test: ...`, `refactor: ...`).
5. **Open a Pull Request**: Submit your PR targeting the `main` branch with a description of the changes and motivation.

---

## 🐛 Reporting Issues & Feature Requests

- **Bug Reports**: Include your OS version, Python version, notification daemon used (e.g., `terminal-notifier`, `notify-send`), reproduction steps, and error logs/output.
- **Feature Requests**: Describe the use case and how the proposed change helps users.

---

## 📄 License
By contributing to `md-nugget-notifier`, you agree that your contributions will be licensed under the project's [MIT License](LICENSE).
