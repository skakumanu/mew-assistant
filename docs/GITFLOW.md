# Git Flow Workflow Guide

## Overview
This project follows the **GitFlow** branching model for organized development and releases.

## Branch Structure

### Main Branches
- **`main`** - Production-ready code. Protected branch.
- **`develop`** - Integration branch for features. Protected branch.

### Supporting Branches
- **`feature/*`** - New features (branch from `develop`, merge back to `develop`)
- **`release/*`** - Release preparation (branch from `develop`, merge to `main` and `develop`)
- **`hotfix/*`** - Production fixes (branch from `main`, merge to `main` and `develop`)

## Quick Start (Without git-flow tool)

### Starting a New Feature
```bash
# Create and switch to feature branch
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name

# Work on your feature...
git add .
git commit -m "feat: add your feature"

# Push to remote
git push -u origin feature/your-feature-name

# Create Pull Request to develop branch on GitHub
```

### Finishing a Feature
```bash
# Update develop
git checkout develop
git pull origin develop

# Merge feature (via GitHub PR is preferred)
# Or manually:
git merge --no-ff feature/your-feature-name
git push origin develop

# Delete feature branch
git branch -d feature/your-feature-name
git push origin --delete feature/your-feature-name
```

### Starting a Release
```bash
# Create release branch from develop
git checkout develop
git pull origin develop
git checkout -b release/1.2.0

# Update version numbers, changelog, etc.
git add .
git commit -m "chore: prepare release 1.2.0"
git push -u origin release/1.2.0
```

### Finishing a Release
```bash
# Merge to main
git checkout main
git pull origin main
git merge --no-ff release/1.2.0
git tag -a v1.2.0 -m "Release version 1.2.0"
git push origin main --tags

# Merge back to develop
git checkout develop
git pull origin develop
git merge --no-ff release/1.2.0
git push origin develop

# Delete release branch
git branch -d release/1.2.0
git push origin --delete release/1.2.0
```

### Creating a Hotfix
```bash
# Create hotfix branch from main
git checkout main
git pull origin main
git checkout -b hotfix/1.2.1

# Fix the bug
git add .
git commit -m "fix: critical bug in production"
git push -u origin hotfix/1.2.1
```

### Finishing a Hotfix
```bash
# Merge to main
git checkout main
git merge --no-ff hotfix/1.2.1
git tag -a v1.2.1 -m "Hotfix version 1.2.1"
git push origin main --tags

# Merge to develop
git checkout develop
git merge --no-ff hotfix/1.2.1
git push origin develop

# Delete hotfix branch
git branch -d hotfix/1.2.1
git push origin --delete hotfix/1.2.1
```

## Branch Naming Conventions

- `feature/user-authentication` ✅
- `feature/add-calendar-sync` ✅
- `release/1.2.0` ✅
- `hotfix/fix-login-bug` ✅
- `bugfix/something` ❌ (use feature/ or hotfix/)
- `my-feature` ❌ (missing prefix)

## Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks
- `perf:` - Performance improvements
- `ci:` - CI/CD changes

### Examples:
```bash
git commit -m "feat(auth): add JWT authentication"
git commit -m "fix(calendar): resolve timezone issue"
git commit -m "docs: update API documentation"
git commit -m "chore: update dependencies"
```

## Pull Request Workflow

1. **Create feature branch** from `develop`
2. **Make changes** and commit
3. **Push** to remote
4. **Create Pull Request** on GitHub
5. **Wait for CI/CD** checks to pass
6. **Request review** from team members
7. **Address feedback** if needed
8. **Merge** when approved

## Protected Branches

Both `main` and `develop` are protected:
- Require pull request reviews
- Require status checks to pass
- No force pushes
- No deletions

## Version Numbering

Follow [Semantic Versioning](https://semver.org/):
- **MAJOR.MINOR.PATCH** (e.g., 1.2.3)
- **MAJOR**: Breaking changes
- **MINOR**: New features (backwards compatible)
- **PATCH**: Bug fixes (backwards compatible)

## GitHub Actions Integration

Our GitFlow workflow automatically:
- ✅ Validates branch naming conventions
- ✅ Runs tests on all branches
- ✅ Enforces code quality checks
- ✅ Prevents invalid branch names

## Common Workflows

### Daily Development
```bash
# Start your day
git checkout develop
git pull origin develop

# Create feature
git checkout -b feature/my-feature

# Work...
git add .
git commit -m "feat: implement feature"
git push -u origin feature/my-feature

# Create PR on GitHub to develop
```

### Before Release
```bash
# Create release branch
git checkout -b release/1.2.0 develop

# Update version, changelog
# Test thoroughly
# Fix any issues

# Merge to main and develop (via PRs)
```

### Emergency Production Fix
```bash
# Create hotfix from main
git checkout -b hotfix/1.2.1 main

# Fix bug
git add .
git commit -m "fix: critical production issue"

# Merge to both main and develop (via PRs)
```

## Best Practices

1. **Always branch from the correct source**
   - Features: from `develop`
   - Releases: from `develop`
   - Hotfixes: from `main`

2. **Keep branches short-lived**
   - Features: 1-5 days
   - Releases: 1-3 days
   - Hotfixes: Hours

3. **Use meaningful names**
   - ✅ `feature/add-voice-commands`
   - ❌ `feature/stuff`

4. **Write good commit messages**
   - Clear, concise, conventional format

5. **Update regularly**
   - Pull from develop daily
   - Rebase if needed

6. **Test before merging**
   - All tests must pass
   - Code review approved

## Resources

- [Git Flow Original Article](https://nvie.com/posts/a-successful-git-branching-model/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [GitHub Flow vs Git Flow](https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow)

## Current Project Status

- **Production Branch**: `main`
- **Development Branch**: `develop` (to be created)
- **Current Version**: Check `main` branch tags
- **Active Features**: Check open PRs with `feature/*` branches

## Questions?

Refer to this guide or ask in team discussions. Happy coding! 🚀
