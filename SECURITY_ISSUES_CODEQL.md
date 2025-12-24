# CodeQL Security Issues - Merge Blocking

## Critical Issues Found

### 1. **CRITICAL: Hardcoded Database Password**
**Severity:** 🔴 CRITICAL - Exposed credentials in source code
**File:** [init-azure-db.py](init-azure-db.py#L9)
**Line:** 9

```python
DB_PASSWORD = "MewDev2024SecurePass"
```

**Issue:** Database password is hardcoded in Python source code. This will be exposed in:
- Git repository history
- Docker images
- Source code repositories
- Version control systems

**Fix:** Remove hardcoded password and use environment variables or Azure Key Vault (already correctly done in `init-federated-fix.py`).

---

### 2. **CRITICAL: Reflected XSS Vulnerability in User Data**
**Severity:** 🔴 CRITICAL - Unescaped user data in HTML
**File:** [app/routers/oauth_web.py](app/routers/oauth_web.py#L350)
**Line:** 350

```javascript
document.getElementById('userInfo').innerHTML = `
    <h3>👤 ${user.full_name}</h3>
    <p><strong>Email:</strong> ${user.email}</p>
    <p><strong>Role:</strong> ${user.role}</p>
    ${user.federated_provider ? `<p><strong>Provider:</strong> ${user.federated_provider}</p>` : ''}
`;
```

**Issue:** User-supplied data (`user.full_name`, `user.email`, `user.role`, `user.federated_provider`) is directly injected into HTML via `innerHTML`. An attacker can inject malicious JavaScript:
- Add `<script>` tags in their full_name during registration
- Payload example: `"><script>alert('XSS')</script>` or `" onload="alert(1)`
- Can steal tokens from localStorage
- Can perform actions on behalf of the user

**Fix:** Use `textContent` instead of `innerHTML`, or sanitize user input before inserting.

---

### 3. **CRITICAL: Reflected XSS in OAuth Success Page**
**Severity:** 🔴 CRITICAL - Unsanitized string interpolation in HTML
**File:** [app/routers/oauth_success_page.py](app/routers/oauth_success_page.py#L74)
**Line:** 74

```python
def get_success_page(user_name: str, user_email: str, jwt_token: str) -> str:
    return f"""
    ...
    <p class="subtitle">
        Hi {user_name}!<br>
        Your Google Calendar is connected.
    </p>
    ...
    <script>
        localStorage.setItem('mew_token', '{jwt_token}');
        localStorage.setItem('mew_user', '{user_email}');
        localStorage.setItem('mew_name', '{user_name}');
    </script>
    """
```

**Issue:** User-supplied strings (`user_name`, `user_email`, `jwt_token`) are directly embedded in HTML/JavaScript without escaping. An attacker can:
1. Inject JavaScript via `user_name`: `'; alert('XSS'); //`
2. Break out of localStorage statements in JavaScript
3. Steal tokens or perform malicious actions

**Fix:** HTML-escape these values and properly escape JavaScript strings. Use JSON encoding for JavaScript variables.

---

### 4. **HIGH: XSS via innerHTML in Calendar Page**
**Severity:** 🔴 HIGH - Unescaped error messages
**File:** [app/routers/calendar_web.py](app/routers/calendar_web.py#L192)
**Line:** 192

```javascript
function showMessage(text, type) {
    const msg = document.getElementById('message');
    msg.className = 'message ' + type;
    msg.innerHTML = text;  // Direct HTML insertion
}
```

**Issue:** Error messages and user feedback are inserted via `innerHTML`. While currently only used with hardcoded strings, API error responses are shown directly:
```javascript
showMessage('❌ ' + error.message, 'error');
```

If the API returns error messages from untrusted sources, they can contain XSS payloads.

**Fix:** Use `textContent` for text-only content or properly sanitize HTML before insertion.

---

### 5. **HIGH: XSS in Debug Page**
**Severity:** 🔴 HIGH - Unescaped dynamic content
**File:** [app/routers/debug_page.py](app/routers/debug_page.py#L87)
**Line:** 87

```javascript
output.innerHTML += `<span class="${color}">[${timestamp}] ${msg}</span>\n`;
```

**Issue:** Log messages and debug output are inserted via `innerHTML`. An attacker with control over API responses can inject malicious HTML/JavaScript.

**Fix:** Use `textContent` or create DOM elements with `createElement` and `textContent`.

---

### 6. **HIGH: Unvalidated Redirect in OAuth Flow**
**Severity:** 🟠 HIGH - Open redirect vulnerability
**File:** [app/routers/oauth_web.py](app/routers/oauth_web.py#L218)
**Line:** 218

```python
@router.get("/login/{provider}")
async def oauth_provider_login(provider: str, redirect_uri: str, db: Session = Depends(get_db)):
    """Initiate OAuth flow for a provider"""
    try:
        auth_url = await OAuthService.get_authorization_url(provider, redirect_uri)
        return RedirectResponse(url=auth_url)
```

**Issue:** The `redirect_uri` parameter is passed directly to `OAuthService.get_authorization_url()` without validation. While OAuth providers validate their own redirect URIs, an attacker could craft a malicious authorization URL that appears to be from your app but redirects to attacker-controlled domain.

**Fix:** Validate `redirect_uri` against a whitelist of allowed origins before using it in OAuth flow.

---

### 7. **HIGH: Token Exposed in URL Query Parameter**
**Severity:** 🟠 HIGH - Token in URL can be leaked
**File:** [app/routers/oauth_web.py](app/routers/oauth_web.py#L250)
**Line:** 250

```python
dashboard_url = f"/auth/oauth/dashboard?token={result['access_token']}"
response = RedirectResponse(url=dashboard_url)
```

**Issue:** JWT access token is passed as a URL query parameter which:
1. Gets logged in server logs and access logs
2. Gets stored in browser history
3. Gets included in Referer headers sent to other sites
4. Gets cached by proxies and CDNs

**Fix:** Use HTTP-only cookies or POST the token, not query parameters. Or remove from URL immediately after redirect.

---

### 8. **HIGH: SQL Injection in Database Initialization**
**Severity:** 🟠 HIGH - Unparameterized SQL string formatting
**File:** [init-azure-db.py](init-azure-db.py#L28)
**Line:** 28

```python
cursor.execute(f"CREATE DATABASE {DB_NAME}")
```

**Issue:** While `DB_NAME` is hardcoded in this script, the pattern is dangerous. If this ever becomes user-configurable, it's a direct SQL injection. The preceding line correctly uses parameterized queries:

```python
cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
```

**Fix:** Use SQL identifier quoting or parameterized queries (PostgreSQL: `psycopg2.sql.Identifier`).

---

### 9. **MEDIUM: Insecure SQL File Execution**
**Severity:** 🟡 MEDIUM - Arbitrary SQL from file without validation
**File:** [init-federated-fix.py](init-federated-fix.py#L22-24)
**Line:** 22-24

```python
# Read and execute SQL
with open('fix_federated_id.sql', 'r') as f:
    sql = f.read()
    cursor.execute(sql)
```

**Issue:** SQL is read from a file without any validation or parsing. If an attacker can modify `fix_federated_id.sql`, they can execute arbitrary SQL commands (DROP TABLE, DELETE, etc.).

**Fix:** 
1. Validate SQL file contents
2. Use parameterized queries
3. Restrict file permissions
4. Consider checking file integrity (checksums)

---

## Summary Table

| ID | File | Line | Type | Severity | Status |
|---|---|---|---|---|---|
| 1 | init-azure-db.py | 9 | Hardcoded Credentials | 🔴 CRITICAL | Must Fix |
| 2 | oauth_web.py | 350 | XSS - innerHTML | 🔴 CRITICAL | Must Fix |
| 3 | oauth_success_page.py | 74 | XSS - String Interpolation | 🔴 CRITICAL | Must Fix |
| 4 | calendar_web.py | 192 | XSS - innerHTML | 🟠 HIGH | Must Fix |
| 5 | debug_page.py | 87 | XSS - innerHTML | 🟠 HIGH | Must Fix |
| 6 | oauth_web.py | 218 | Unvalidated Redirect | 🟠 HIGH | Must Fix |
| 7 | oauth_web.py | 250 | Token in URL | 🟠 HIGH | Must Fix |
| 8 | init-azure-db.py | 28 | SQL Injection Pattern | 🟠 HIGH | Consider Fix |
| 9 | init-federated-fix.py | 22-24 | Arbitrary SQL Execution | 🟡 MEDIUM | Consider Fix |

## Additional Observations

### ✅ Good Security Practices Found
- CSRF protection middleware implemented ([app/middleware/security.py](app/middleware/security.py))
- HTTP-only, Secure, SameSite cookies set for authentication
- Password hashing with Argon2
- Bearer token authentication for APIs
- Input sanitization for HTML in security middleware
- SQL parameterization in most database queries

### ⚠️ Potential Areas of Concern
- Long-lived JWT tokens (30 days) - consider implementing token rotation
- Test files contain hardcoded test passwords (acceptable for tests)
- Debug pages should be disabled in production

## Recommendations

### Before Merge
1. **MUST FIX** all 3 critical XSS issues (#2, #3)
2. **MUST FIX** hardcoded password (#1)
3. **MUST FIX** XSS issues in calendar and debug pages (#4, #5)
4. **MUST FIX** token exposure in URL and redirect validation (#6, #7)

### Before Production Deployment
1. Fix SQL injection patterns (#8, #9)
2. Disable or restrict debug_page route
3. Remove hardcoded API endpoints from debug_page
4. Implement token rotation for long-lived sessions
5. Add Content Security Policy (CSP) headers
6. Consider rate limiting on OAuth endpoints
