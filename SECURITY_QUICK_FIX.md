# Security Issues - Quick Reference Card

## 🔴 CRITICAL - MERGE BLOCKED

| # | File | Line | Issue | Quick Fix |
|---|------|------|-------|-----------|
| 1 | `init-azure-db.py` | 9 | Hardcoded password | Move to `.env`, use `os.getenv()` |
| 2 | `app/routers/oauth_web.py` | 350 | XSS via innerHTML | Use `textContent` or safe DOM API |
| 3 | `app/routers/oauth_success_page.py` | 74 | XSS in JavaScript | Use `json.dumps()` for string escaping |

**Total Time to Fix:** ~25 minutes  
**Estimated Difficulty:** Easy (3/10)

---

## 🟠 HIGH - FIX BEFORE PRODUCTION

| # | File | Line | Issue | Quick Fix |
|---|------|------|-------|-----------|
| 4 | `app/routers/calendar_web.py` | 192 | XSS via innerHTML | Use `textContent` instead |
| 5 | `app/routers/debug_page.py` | 87 | XSS via innerHTML | Use DOM `createElement()` |
| 6 | `app/routers/oauth_web.py` | 218 | Open redirect | Validate redirect_uri against whitelist |
| 7 | `app/routers/oauth_web.py` | 250 | Token in URL | Use HTTP-only cookie instead |

**Total Time to Fix:** ~40 minutes  
**Estimated Difficulty:** Medium (5/10)

---

## 🟡 MEDIUM - PRODUCTION HARDENING

| # | File | Line | Issue | Quick Fix |
|---|------|------|-------|-----------|
| 8 | `init-azure-db.py` | 28 | SQL injection pattern | Use `psycopg2.sql.Identifier()` |
| 9 | `init-federated-fix.py` | 22-24 | Arbitrary SQL | Add file validation & logging |

**Total Time to Fix:** ~25 minutes  
**Estimated Difficulty:** Easy to Medium (4/10)

---

## Code Fix Templates

### Fix #1: Remove Hardcoded Password
```python
# ❌ BEFORE
DB_PASSWORD = "MewDev2024SecurePass"

# ✅ AFTER
import os
DB_PASSWORD = os.getenv("DB_PASSWORD")
if not DB_PASSWORD:
    raise ValueError("DB_PASSWORD environment variable required")
```

### Fix #2, #4, #5: Remove innerHTML
```javascript
// ❌ BEFORE
document.getElementById('msg').innerHTML = userText;

// ✅ AFTER (Option A: textContent)
document.getElementById('msg').textContent = userText;

// ✅ AFTER (Option B: Safe DOM)
const span = document.createElement('span');
span.textContent = userText;
element.appendChild(span);
```

### Fix #3: Escape JavaScript Strings
```python
# ❌ BEFORE
return f"""<script>
    localStorage.setItem('mew_name', '{user_name}');
</script>"""

# ✅ AFTER
import json
return f"""<script>
    localStorage.setItem('mew_name', {json.dumps(user_name)});
</script>"""
```

### Fix #6: Validate Redirects
```python
# ✅ ADD THIS FUNCTION
from urllib.parse import urlparse

ALLOWED_ORIGINS = {
    'localhost:3000',
    'localhost:8000',
    'your-app.com',
}

def is_safe_redirect(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme and parsed.scheme not in ('http', 'https'):
        return False
    if parsed.netloc and parsed.netloc not in ALLOWED_ORIGINS:
        return False
    return True

# ✅ USE IT
if not is_safe_redirect(redirect_uri):
    raise HTTPException(status_code=400, detail="Invalid redirect")
```

### Fix #7: Use Cookies Instead of URL
```python
# ❌ BEFORE
dashboard_url = f"/auth/oauth/dashboard?token={result['access_token']}"
return RedirectResponse(url=dashboard_url)

# ✅ AFTER
response = RedirectResponse(url="/auth/oauth/dashboard")
response.set_cookie(
    key="mew_token",
    value=result["access_token"],
    httponly=True,      # JS cannot access
    secure=True,        # HTTPS only
    samesite="lax"      # CSRF protection
)
return response
```

### Fix #8: Parameterize SQL
```python
# ❌ BEFORE
cursor.execute(f"CREATE DATABASE {DB_NAME}")

# ✅ AFTER
import psycopg2.sql
cursor.execute(
    psycopg2.sql.SQL("CREATE DATABASE {}").format(
        psycopg2.sql.Identifier(DB_NAME)
    )
)
```

### Fix #9: Validate SQL Files
```python
# ✅ ADD VALIDATION
import hashlib

def load_sql_file(filename: str) -> str:
    if not os.path.exists(filename):
        raise FileNotFoundError(f"SQL file not found: {filename}")
    
    with open(filename, 'r') as f:
        sql = f.read()
    
    if len(sql) > 1_000_000:  # Size check
        raise ValueError(f"SQL file too large: {filename}")
    
    # Optional: Hash check
    # expected = "abc123..."
    # if hashlib.sha256(sql.encode()).hexdigest() != expected:
    #     raise ValueError("SQL file integrity check failed")
    
    return sql

# ✅ USE IT
sql = load_sql_file('fix_federated_id.sql')
cursor.execute(sql)
```

---

## Testing Checklist

After fixes, test with these payloads:

### XSS Test Payloads
```javascript
// All of these should NOT execute:
"><script>alert('XSS')</script>
'"><script>alert('XSS')</script>
<img src=x onerror="alert('XSS')">
<svg onload="alert('XSS')">
javascript:alert('XSS')
data:text/html,<script>alert('XSS')</script>
```

### Redirect Test Cases
```
/auth/oauth/login/google?redirect_uri=https://evil.com/steal
/auth/oauth/login/google?redirect_uri=javascript:alert(1)
/auth/oauth/login/google?redirect_uri=//attacker.com
```

### SQL Test Cases
```
DB_NAME = "test'; DROP TABLE users; --"
DB_NAME = "test\"; DROP TABLE users; --"
```

---

## Files to Review After Fixes

1. `init-azure-db.py` - Verify password removed
2. `app/routers/oauth_web.py` - Check both fixes applied
3. `app/routers/oauth_success_page.py` - Verify JSON encoding
4. `app/routers/calendar_web.py` - Check textContent usage
5. `app/routers/debug_page.py` - Verify safe DOM usage
6. `init-federated-fix.py` - Check validation added

---

## Merge Checklist

- [ ] All 3 CRITICAL issues fixed and tested
- [ ] All 4 HIGH issues fixed and tested
- [ ] Security review completed
- [ ] XSS payloads tested against all fixes
- [ ] Code changes peer-reviewed
- [ ] Unit tests still passing
- [ ] No new security warnings introduced

---

## Deploy Checklist (Before Production)

- [ ] All MEDIUM issues fixed
- [ ] Hardcoded password completely removed from codebase
- [ ] Environment variables configured in all environments
- [ ] HTTP-only cookies enabled in production
- [ ] HTTPS enforced
- [ ] Security headers configured
- [ ] Content Security Policy (CSP) implemented
- [ ] Debug endpoints disabled or restricted
- [ ] Sensitive logging removed from production

---

## Resources

- **Detailed Guides:** See `SECURITY_FIXES_DETAILED.md`
- **Full Analysis:** See `SECURITY_ISSUES_CODEQL.md`
- **Executive Summary:** See `SECURITY_AUDIT_SUMMARY.md`

---

**Last Updated:** December 23, 2025  
**Status:** Ready to Fix
