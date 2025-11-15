# CI/CD Pipeline Documentation

## Overview

Mew Assistant uses a comprehensive CI/CD pipeline built on GitHub Actions to ensure code quality, security, and reliable deployments.

## Pipeline Workflows

### 1. **Continuous Integration (ci.yml)**

Runs on every push and pull request to main branches.

**Jobs:**
- **Linting**: Code formatting checks (Black, isort, Flake8, Pylint)
- **Security Scanning**: Bandit (security linter) and Safety (dependency vulnerabilities)
- **Test Suite**: Multi-version Python testing (3.9, 3.10, 3.11, 3.12) with PostgreSQL
- **Integration Tests**: Full integration testing with Redis and PostgreSQL
- **Build**: Docker image build validation
- **Compliance**: COPPA, HIPAA, and GDPR compliance tests

**Coverage:** Automatically uploads to Codecov

### 2. **Continuous Deployment (cd.yml)**

Triggered on tags (v*) for production, and main branch for staging.

**Environments:**
- **Staging**: Auto-deploys from main branch
- **Production**: Deploys from version tags (v1.0.0, v2.0.0, etc.)

**Features:**
- Azure Container Apps deployment
- Database backup before production deploy
- Health checks after deployment
- Automatic rollback on failure

### 3. **Security Scanning (security-scan.yml)**

Runs on push, PR, and weekly schedule.

**Scanners:**
- **CodeQL**: Static analysis for security vulnerabilities
- **Trivy**: Container and filesystem vulnerability scanning
- **Snyk**: Dependency vulnerability analysis
- **Gitleaks**: Secret scanning in git history

### 4. **Docker Publishing (docker-publish.yml)**

Builds and publishes multi-platform Docker images to GitHub Container Registry.

**Features:**
- Multi-architecture support (amd64, arm64)
- Automatic tagging based on git refs
- Build caching for faster builds

### 5. **Performance Testing (performance-test.yml)**

Load testing and benchmarking on main branch and weekly schedule.

**Tools:**
- **Locust**: Load testing with 100 concurrent users
- **pytest-benchmark**: API endpoint benchmarking

### 6. **Dependency Updates (dependency-update.yml)**

Automated weekly dependency updates.

**Features:**
- Weekly Python dependency updates
- Auto-merge for patch/minor Dependabot PRs
- Automated pull request creation

### 7. **Changelog Generation (changelog.yml)**

Automatically generates changelog for releases.

## Required GitHub Secrets

Set these in your repository settings:

```
AZURE_CREDENTIALS       # Azure service principal credentials
ACR_NAME               # Azure Container Registry name
RESOURCE_GROUP         # Azure resource group name
POSTGRES_SERVER        # Azure PostgreSQL server name
SNYK_TOKEN            # Snyk API token (optional)
```

## Badges

Add these to your README.md:

```markdown
![CI](https://github.com/skakumanu/mew-assistant/workflows/Continuous%20Integration/badge.svg)
![Security](https://github.com/skakumanu/mew-assistant/workflows/Security%20Scanning/badge.svg)
![codecov](https://codecov.io/gh/skakumanu/mew-assistant/branch/main/graph/badge.svg)
```

## Local Testing

Test workflows locally using [act](https://github.com/nektos/act):

```bash
# Install act
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Run CI workflow
act push -W .github/workflows/ci.yml

# Run specific job
act push -j test -W .github/workflows/ci.yml
```

## Deployment Process

### Staging Deployment
1. Merge PR to main branch
2. CI pipeline runs automatically
3. If tests pass, auto-deploys to staging
4. Smoke tests verify deployment

### Production Deployment
1. Create a release tag: `git tag v1.0.0 && git push origin v1.0.0`
2. CD pipeline triggers automatically
3. Database backup is created
4. Deployment to production
5. Health checks run
6. GitHub release is created with notes

### Rollback
If deployment fails, automatic rollback activates the previous revision.

Manual rollback:
```bash
az containerapp revision list --name mew-assistant-prod -g <RESOURCE_GROUP>
az containerapp revision activate --revision <REVISION_NAME> -g <RESOURCE_GROUP>
```

## Performance Benchmarks

Load testing targets:
- **Users**: 100 concurrent
- **Duration**: 2 minutes
- **Response Time**: <500ms for 95th percentile
- **Error Rate**: <1%

## Security Standards

All code must pass:
- ✅ CodeQL security analysis
- ✅ Trivy vulnerability scan (no HIGH/CRITICAL)
- ✅ No secrets in code (Gitleaks)
- ✅ Dependency vulnerabilities resolved

## Compliance Testing

Automated tests ensure:
- ✅ COPPA compliance (child privacy)
- ✅ HIPAA compliance (health data protection)
- ✅ GDPR compliance (data privacy rights)

## Monitoring

Post-deployment monitoring:
- Application Insights for Azure
- Health endpoint checks every 5 minutes
- Automated alerts for failures
- Performance metrics tracking

## Troubleshooting

### CI Failures
```bash
# View logs
gh run view <RUN_ID>

# Re-run failed jobs
gh run rerun <RUN_ID>
```

### Deployment Issues
```bash
# Check container logs
az containerapp logs show --name mew-assistant-prod -g <RESOURCE_GROUP>

# Check revisions
az containerapp revision list --name mew-assistant-prod -g <RESOURCE_GROUP>
```

## Best Practices

1. **Always create a PR** - Never push directly to main
2. **Wait for CI** - Ensure all checks pass before merging
3. **Test locally first** - Run tests and linting before pushing
4. **Tag releases** - Use semantic versioning (v1.0.0)
5. **Monitor deployments** - Check health endpoints after deploy
6. **Review security scans** - Address vulnerabilities promptly

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for development workflow and guidelines.
