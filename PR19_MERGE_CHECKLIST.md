PR #19 Merge Checklist

Status: Local tests run (some failures) — fixes required before merge

Local test results (summary):
- Ran: `pytest` in project venv
- Total: 261 tests collected
- Passing: 50
- Failed: 14
- Skipped: 1
- Warnings: 28

Failing tests (high level):
- tests/performance/test_benchmarks.py (4 failures)
  - AttributeError / ModuleNotFoundError: some performance helpers not available/imported
- tests/test_api_endpoints.py (multiple failures)
  - summary endpoint returning 404/405 vs expected responses; CORS header assertions failing
- tests/test_auth.py (multiple failures)
  - passlib.exc.MissingBackendError: argon2 backend missing

Immediate local fixes to run before PR merge
1. Install test runtime dependencies (dev):
   - Ensure `argon2-cffi` is installed for Argon2 password hashing: `pip install argon2-cffi`
   - Re-run `pip install -r requirements.txt` and add any dev/test-only packages to `requirements-dev.txt` or CI config.
2. Address ModuleNotFoundError failures:
   - Inspect stack traces in failing tests to locate missing imports (some tests expect optional integrations to be available).
   - Add lightweight test fakes/mocks or guard imports to avoid importing heavy integrations during unit tests.
3. Fix API behavior regressions:
   - Run failing endpoint tests with `-k <test_name> -q --maxfail=1` to reproduce and debug.
   - Confirm `summary` endpoint handler is mounted and returns correct methods/status codes.
4. CORS headers:
   - Verify `CORS_ORIGINS` and middleware configuration in `app/middleware.py` and `app/utils/config.py`.
5. Re-run full test suite and ensure all tests pass locally.

CI & Security checks
- Wait for CodeQL and other security scans to pass on PR (branch protection may require this).
- Confirm CI runs `pytest` in a clean environment and installs required test deps.

Merge steps (when tests & checks green):
1. Approve PR on GitHub (review UI)
2. Squash and merge into `master` (use compact commit message summarizing changes)
3. Create release tag if needed
4. Deploy to staging and run smoke tests (OAuth login, dashboard, /docs)
5. Monitor CodeQL/Snyk post-merge and Azure logs for anomalies
6. Invalidate/recreate any test users per `SECURITY_INCIDENT.md`

Post-merge follow-ups
- Add `requirements-dev.txt` for CI and local dev to capture `argon2-cffi` and other test-only packages.
- Add CI step to run `pip install -r requirements-dev.txt` or include dev deps in CI environment.
- Consider adding pre-commit hooks to prevent accidental secrets and to run basic tests.

Notes & reproduction commands
 To reproduce tests locally (Windows PowerShell, from repo root):

```powershell
# use venv python from repo
$env:SECRET_KEY = "[REDACTED]"
$env:DATABASE_URL = "sqlite:///./test.db"
$env:SECRET_KEY = "[REDACTED]"
C:/Users/skaku/Projects/mew-assistant/.venv/Scripts/python.exe -m pytest -q
```

- To run a single failing test for debugging:

```powershell
C:/Users/skaku/Projects/mew-assistant/.venv/Scripts/python.exe -m pytest tests/test_auth.py::test_register_user -q -k register_user --maxfail=1
```

Contact & references
- PR: https://github.com/skakumanu/mew-assistant/pull/19
- Incident: `SECURITY_INCIDENT.md`
- Review response: `COPILOT_REVIEW_RESPONSE.md`

---
Generated: 2025-12-24
