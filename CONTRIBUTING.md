# Contributing to LLM Knowledge Base

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

---

## 🎯 Ways to Contribute

1. **Bug Reports**: Found an issue? Open a GitHub issue
2. **Feature Requests**: Have an idea? Share it in issues
3. **Documentation**: Improve guides and examples
4. **Code**: Fix bugs or add features
5. **Examples**: Share your setup configuration

---

## 🐛 Reporting Bugs

**Before submitting**:
- Search existing issues to avoid duplicates
- Try the latest version from `main` branch

**Include in your report**:
- **Environment**: OS, Python version, Confluence version
- **Configuration**: Sanitized config (hide tokens!)
- **Steps to reproduce**: Clear, numbered steps
- **Expected vs Actual**: What should happen vs what did happen
- **Logs**: Relevant error messages or log excerpts

**Example**:
```markdown
**Environment**:
- OS: macOS 14.0
- Python: 3.11.5
- Confluence: Cloud (latest)

**Issue**: Sync fails with "Page not found" error

**Steps**:
1. Configure .confluence-config with root page ID
2. Run ./tools/confluence/sync-space.sh MY_SPACE
3. Error appears after 10 pages

**Expected**: All 50 pages sync successfully
**Actual**: Fails at page 11 with error

**Error Log**:
```
[paste error here]
```
```

---

## 💡 Suggesting Features

**Good feature requests include**:
- **Use Case**: Why is this needed?
- **Current Workaround**: How do you handle it now?
- **Proposed Solution**: How should it work?
- **Alternatives**: Other ways to solve it?

---

## 🔧 Contributing Code

### Setup Development Environment

```bash
# Fork the repository on GitHub
# Clone your fork
git clone https://github.com/YOUR_USERNAME/llm-knowledge-base.git
cd llm-knowledge-base

# Add upstream remote
git remote add upstream https://github.com/ggthename/llm-knowledge-base.git

# Create a branch
git checkout -b feature/your-feature-name
```

### Making Changes

1. **Follow existing code style**:
   - Python: PEP 8 (use `black` for formatting)
   - Bash: Use shellcheck
   - Keep functions small and focused

2. **Test your changes**:
   - Test with a real Confluence instance
   - Verify all sync modes (full, incremental)
   - Check edge cases (empty pages, special characters, images)

3. **Update documentation**:
   - Update README if adding features
   - Add examples if helpful
   - Update SETUP-GUIDE for new configuration options

4. **Commit messages**:
   ```
   type(scope): short description

   Longer explanation if needed.

   Fixes #123
   ```

   Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

### Submitting Pull Request

1. **Update from upstream**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

3. **Create PR on GitHub**:
   - Clear title describing the change
   - Description with context and motivation
   - Reference related issues

4. **PR Checklist**:
   - [ ] Code follows project style
   - [ ] Tests pass (if applicable)
   - [ ] Documentation updated
   - [ ] Commit messages are clear
   - [ ] No merge conflicts

---

## 📚 Documentation Contributions

Documentation improvements are always welcome!

**Areas needing help**:
- More real-world examples in `examples/`
- Common troubleshooting scenarios
- Video tutorials or blog posts (link them!)
- Non-English translations

**Guidelines**:
- Use clear, simple language
- Include code examples
- Test instructions actually work
- Use relative links for internal docs

---

## 🎨 Example Contributions

Share your configuration!

**Create**: `examples/YOUR-COMPANY-SETUP.md`

**Include**:
- Organization context (without sensitive details)
- Space/project structure
- Custom `.moe-config` patterns
- Lessons learned
- Metrics/ROI if available

**Sanitize**:
- Remove company names (or use "ACME Corp")
- Remove URLs, tokens, IDs
- Use "SPACE_A", "PROJECT_X" as placeholders

---

## 🧪 Testing Guidelines

### Manual Testing Checklist

Before submitting code changes:

- [ ] Full sync works on test space
- [ ] Incremental sync detects changes
- [ ] Images download correctly
- [ ] Links convert to `[[Obsidian]]` format
- [ ] Frontmatter generates properly
- [ ] No Python errors in logs
- [ ] Scripts are executable (`chmod +x`)

### Test Environments

We don't have automated tests yet (contributions welcome!).

Test manually with:
- **Small space**: 10-20 pages
- **Large space**: 100+ pages
- **Special characters**: Pages with `/`, `?`, Unicode
- **Nested structure**: Deep page hierarchies
- **Mixed content**: Code blocks, tables, images, diagrams

---

## 🚫 What We Don't Accept

- **Malicious code**: Obviously
- **Credentials**: Never commit tokens or passwords
- **Company-specific code**: Keep it generic
- **Breaking changes**: Without discussion first
- **Uncommented complex code**: Explain your logic

---

## 📜 Code of Conduct

Be respectful and constructive:
- **Be welcoming**: Help newcomers
- **Be respectful**: Disagree gracefully
- **Be patient**: Not everyone has the same context
- **Assume good intent**: People are trying to help

---

## 🏆 Recognition

Contributors will be:
- Listed in GitHub contributors
- Mentioned in release notes (for significant contributions)
- Thanked in the community

---

## 📞 Questions?

- **General questions**: Open a GitHub Discussion
- **Bug reports**: GitHub Issues
- **Security issues**: See SECURITY.md (to be created)
- **Feature ideas**: GitHub Issues with "enhancement" label

---

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to LLM Knowledge Base!** 🎉
