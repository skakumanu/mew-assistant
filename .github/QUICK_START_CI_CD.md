# CI/CD Quick Start Guide

## 🚀 Quick Commands

### Development Workflow

```bash
# 1. Create feature branch
git checkout -b feature/my-feature

# 2. Make changes and test locally
pytest tests/
black app/ tests/
isort app/ tests/

# 3. Commit and push
git add .
git commit -m "feat: add new feature"
git push origin feature/my-feature

# 4. Create PR on GitHub
# CI will automatically run all checks
```

### Deployment Workflow

```bash
# Deploy to Staging (automatic)
git checkout main
git merge feature/my-feature
git push origin main
# ✅ Auto-deploys to staging

# Deploy to Production
git tag v1.0.0
git push origin v1.0.0
# ✅ Auto-deploys to production with backup & rollback
```

---

## 📊 Pipeline Status

Check pipeline status:
- GitHub Actions tab
- PR checks
- Branch protection status

Add badges to README:
```markdown
![CI](https://github.com/skakumanu/mew-assistant/workflows/Continuous%20Integration/badge.svg)
![Security](https://github.com/skakumanu/mew-assistant/workflows/Security%20Scanning/badge.svg)
```

---

## 🔧 Local Testing

### Run tests locally:
```bash
# Unit tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=app --cov-report=term

# Specific test
pytest tests/test_auth.py -v

# Integration tests
pytest tests/integration/ -v
```

### Linting:
```bash
# Auto-fix formatting
black app/ tests/
isort app/ tests/

# Check without fixing
black --check app/ tests/
flake8 app/ tests/ --max-line-length=120
pylint app/ --max-line-length=120
```

### Security scanning:
```bash
# Check for vulnerabilities
bandit -r app/
safety check

# Check for secrets
pip install gitleaks
gitleaks detect --source . --verbose
```

---

## 🐳 Docker Testing

```bash
# Build image
podman build -t mew-assistant:test .

# Run container
podman run -p 8000:8000 mew-assistant:test

# Test endpoints
curl http://localhost:8000/health
```

---

## 🔑 Required Secrets

Configure in GitHub Settings → Secrets and variables → Actions:

```
AZURE_CREDENTIALS       # {"clientId": "...", "clientSecret": "...", ...}
ACR_NAME               # your-registry-name
RESOURCE_GROUP         # your-resource-group
POSTGRES_SERVER        # your-postgres-server
SNYK_TOKEN            # (optional) your-snyk-token
```

---

## 📝 Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new feature
fix: resolve bug
docs: update documentation
test: add test cases
chore: update dependencies
ci: modify pipeline
refactor: code restructuring
perf: performance improvement
```

---

## 🚨 Common Issues

### CI Failing?

**1. Test failures:**
```bash
# Run tests locally first
pytest tests/ -v
```

**2. Linting errors:**
```bash
# Auto-fix most issues
black app/ tests/
isort app/ tests/
```

**3. Security vulnerabilities:**
```bash
# Update dependencies
pip install --upgrade -r requirements.txt
pip-audit
```

### Deployment Issues?

**1. Check logs:**
```bash
# GitHub Actions
gh run view <RUN_ID> --log

# Azure Container Apps
az containerapp logs show --name mew-assistant-prod -g <RG>
```

**2. Manual rollback:**
```bash
az containerapp revision list --name mew-assistant-prod -g <RG>
az containerapp revision activate --revision <PREV_REVISION> -g <RG>
```

---

## 🎯 Best Practices

1. ✅ **Always create a PR** - Don't push directly to main
2. ✅ **Test locally first** - Ensure tests pass before pushing
3. ✅ **Keep PRs small** - Easier to review and merge
4. ✅ **Write tests** - Maintain >80% coverage
5. ✅ **Review security scans** - Address vulnerabilities promptly
6. ✅ **Use semantic versioning** - v1.0.0, v1.1.0, v2.0.0
7. ✅ **Monitor deployments** - Check health endpoints after deploy

---

## 📚 More Information

- **Full Documentation:** `.github/CI_CD_DOCUMENTATION.md`
- **Implementation Summary:** `CI_CD_IMPLEMENTATION_SUMMARY.md`
- **Contributing Guide:** `CONTRIBUTING.md`

---

## 🆘 Getting Help

1. Check the logs in GitHub Actions
2. Review the documentation
3. Create a GitHub issue
4. Ask in GitHub Discussions
