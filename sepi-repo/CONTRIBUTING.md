# Contributing to SEPI 2.0

We welcome contributions from the bioinformatics community! This document provides guidelines for contributing to SEPI 2.0.

## 🚀 Ways to Contribute

- **Bug Reports**: Found a bug? [Open an issue](https://github.com/yourusername/sepi/issues)
- **Feature Requests**: Have an idea? [Start a discussion](https://github.com/yourusername/sepi/discussions)
- **Code Contributions**: Want to add features or fix bugs? See below
- **Documentation**: Help improve our docs or add examples
- **Testing**: Help us test new features or edge cases

## 🛠️ Development Setup

### Prerequisites
- Python 3.8 or higher
- Git

### Setup Steps
```bash
# Clone the repository
git clone https://github.com/yourusername/sepi.git
cd sepi

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-cov

# Run tests to ensure everything works
python test_sepi_robustness.py
```

## 🧪 Testing

### Running Tests
```bash
# Run the comprehensive test suite
python test_sepi_robustness.py

# Run with pytest (if available)
pytest

# Run with coverage
pytest --cov=sepi --cov-report=html
```

### Test Coverage
We aim for high test coverage. Please ensure:
- New features include comprehensive tests
- Bug fixes include regression tests
- All tests pass before submitting PRs

## 📝 Code Style

### Python Style
- Follow [PEP 8](https://pep8.org/) guidelines
- Use type hints for function parameters and return values
- Write docstrings for all public functions and classes
- Keep line length under 88 characters (Black default)

### Commit Messages
Use clear, descriptive commit messages:
```
feat: add support for custom assembly levels
fix: resolve caching issue with NCBI objects
docs: update README with new configuration options
```

### Branch Naming
- `feature/description`: New features
- `fix/description`: Bug fixes
- `docs/description`: Documentation updates
- `test/description`: Test-related changes

## 🔄 Pull Request Process

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Make** your changes and add tests
4. **Run** the test suite: `python test_sepi_robustness.py`
5. **Commit** your changes: `git commit -m 'feat: add amazing feature'`
6. **Push** to your branch: `git push origin feature/amazing-feature`
7. **Open** a Pull Request

### PR Requirements
- [ ] Tests pass
- [ ] Code follows style guidelines
- [ ] Documentation updated if needed
- [ ] Commit messages are clear
- [ ] PR description explains the changes

## 🐛 Reporting Bugs

### Bug Report Template
```markdown
**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Run command: `python sepi.py --organism "E. coli" --proteins "AcrA"`
2. See error: `TypeError: ...`

**Expected behavior**
A clear description of what you expected to happen.

**Environment**
- OS: [e.g., Windows 11, Ubuntu 20.04]
- Python version: [e.g., 3.9.7]
- SEPI version: [e.g., 2.0.0]

**Additional context**
Add any other context about the problem here.
```

## 💡 Feature Requests

### Feature Request Template
```markdown
**Is your feature request related to a problem?**
A clear description of what the problem is.

**Describe the solution you'd like**
A clear description of what you want to happen.

**Describe alternatives you've considered**
A clear description of any alternative solutions.

**Additional context**
Add any other context or screenshots about the feature request.
```

## 📚 Documentation

### Updating Documentation
- Update README.md for user-facing changes
- Update docstrings for code changes
- Add examples for new features
- Update this CONTRIBUTING.md as needed

### Documentation Standards
- Use clear, concise language
- Include code examples where helpful
- Keep examples up-to-date with current API
- Test all code examples in documentation

## 🤝 Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help newcomers learn and contribute
- Maintain professional communication

## 📞 Getting Help

- **Issues**: For bugs and technical problems
- **Discussions**: For questions and feature ideas
- **Email**: For sensitive or detailed inquiries

## 🙏 Acknowledgments

Thank you for contributing to SEPI 2.0! Your efforts help make bioinformatics research more accessible and reproducible for everyone.

---

**SEPI 2.0** - Building the future of bioinformatics automation together 🧬