from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from urllib.parse import urlparse

from app.database.connection import get_db
from app.services.oauth_service import OAuthService
from app.utils.log_sanitizer import sanitize_for_log

router = APIRouter(prefix="/auth/oauth", tags=["OAuth Web"])


def is_safe_redirect_uri(uri: str) -> bool:
    """
    Validate redirect URI to prevent open redirect vulnerabilities.
    Only allow relative paths or same-origin redirects.
    """
    if not uri:
        return False
    
    # Allow relative paths
    if uri.startswith('/'):
        return True
    
    # For absolute URLs, check if they're from allowed origins
    try:
        parsed = urlparse(uri)
        # Only allow localhost and no scheme (relative)
        if parsed.netloc in ['localhost', '127.0.0.1', ''] or parsed.netloc.startswith('localhost:'):
            return True
    except Exception:
        return False
    
    return False



@router.get("/login", response_class=HTMLResponse)
async def oauth_login_page(request: Request):
    """Serve OAuth login page for mobile devices"""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mew Assistant - Login</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }
        h1 {
            color: #667eea;
            text-align: center;
            margin-bottom: 30px;
        }
        .login-button {
            width: 100%;
            padding: 15px;
            margin: 10px 0;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }
        .login-button:active {
            transform: scale(0.98);
        }
        .google-btn {
            background: #4285f4;
            color: white;
        }
        .apple-btn {
            background: #000;
            color: white;
        }
        .microsoft-btn {
            background: #00a4ef;
            color: white;
        }
        .traditional-btn {
            background: #667eea;
            color: white;
        }
        .status {
            margin-top: 20px;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            display: none;
        }
        .status.success {
            background: #d4edda;
            color: #155724;
        }
        .status.error {
            background: #f8d7da;
            color: #721c24;
        }
        .traditional-form {
            display: none;
            margin-top: 20px;
        }
        input {
            width: 100%;
            padding: 12px;
            margin: 8px 0;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
            box-sizing: border-box;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🐱 Mew Assistant</h1>
        <p style="text-align: center; color: #666; margin-bottom: 30px;">
            Choose your preferred login method
        </p>

        <button class="login-button google-btn" onclick="loginWithGoogle()">
            <svg width="18" height="18" xmlns="http://www.w3.org/2000/svg">
                <path
                    d="M9 3.48c1.69 0 2.83.73 3.48 1.34l2.54-2.48
                       C13.46.89 11.43 0 9 0 5.48 0 2.44 2.02.96 4.96l2.91 2.26
                       C4.6 5.05 6.62 3.48 9 3.48z"
                    fill="#EA4335"
                />
                <path
                    d="M17.64 9.2c0-.74-.06-1.28-.19-1.84H9v3.34h4.96
                       c-.10.83-.64 2.08-1.84 2.92l2.84 2.2c1.7-1.57 2.68-3.88 2.68-6.62z"
                    fill="#4285F4"
                />
                <path
                    d="M3.88 10.78A5.54 5.54 0 0 1 3.58 9c0-.62.11-1.22.29-1.78L.96 4.96
                       A9.008 9.008 0 0 0 0 9c0 1.45.35 2.82.96 4.04l2.92-2.26z"
                    fill="#FBBC05"
                />
                <path
                    d="M9 18c2.43 0 4.47-.8 5.96-2.18l-2.84-2.2c-.76.53-1.78.9-3.12.9
                       -2.38 0-4.4-1.57-5.12-3.74L.97 13.04C2.45 15.98 5.48 18 9 18z"
                    fill="#34A853"
                />
            </svg>
            Continue with Google
        </button>

        <button class="login-button apple-btn" onclick="loginWithApple()">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="white">
                <path
                    d="M17.05 20.28c-.98.95-2.05.88-3.08.4-1.09-.5-2.08-.48-3.24 0
                       -1.44.62-2.2.44-3.06-.4C2.79 15.25 3.51 7.59 9.05 7.31c1.35.07 2.29.74
                       3.08.8 1.18-.24 2.31-.93 3.57-.84 1.51.12 2.65.72 3.4 1.8-3.12 1.87-2.38 5.98
                       .48 7.13-.57 1.5-1.31 2.99-2.54 4.09l.01-.01zM12.03 7.25c-.15-2.23 1.66-4.07
                       3.74-4.25.29 2.58-2.34 4.5-3.74 4.25z"
                />
            </svg>
            Continue with Apple
        </button>

        <button class="login-button microsoft-btn" onclick="loginWithMicrosoft()">
            <svg width="18" height="18" viewBox="0 0 23 23" fill="white">
                <path d="M0 0h11v11H0z"/>
                <path d="M12 0h11v11H12z"/>
                <path d="M0 12h11v11H0z"/>
                <path d="M12 12h11v11H12z"/>
            </svg>
            Continue with Microsoft
        </button>

        <div style="text-align: center; margin: 20px 0; color: #999;">OR</div>

        <button class="login-button traditional-btn" onclick="toggleTraditionalForm()">
            📧 Login with Email
        </button>

        <div id="traditionalForm" class="traditional-form">
            <input type="email" id="email" placeholder="Email" />
            <input type="password" id="password" placeholder="Password" />
            <button class="login-button traditional-btn" onclick="loginTraditional()">
                Login
            </button>
        </div>

        <div id="status" class="status"></div>
    </div>

    <script>
        const API_URL = window.location.origin;

        function showStatus(message, isError = false) {
            const status = document.getElementById('status');
            status.textContent = message;
            status.className = 'status ' + (isError ? 'error' : 'success');
            status.style.display = 'block';
        }

        function toggleTraditionalForm() {
            const form = document.getElementById('traditionalForm');
            form.style.display = form.style.display === 'none' ? 'block' : 'none';
        }

        async function loginTraditional() {
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;

            if (!email || !password) {
                showStatus('Please enter email and password', true);
                return;
            }

            try {
                const response = await fetch(`${API_URL}/auth/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password }),
                });

                const data = await response.json();

                if (response.ok) {
                    localStorage.setItem('mew_token', data.access_token);
                    localStorage.setItem('mew_user', JSON.stringify(data.user));
                    showStatus('Login successful! Redirecting...');
                    setTimeout(() => {
                        window.location.href = '/auth/oauth/dashboard';
                    }, 1500);
                } else {
                    showStatus(data.detail || 'Login failed', true);
                }
            } catch (error) {
                showStatus('Connection error: ' + error.message, true);
            }
        }

        async function loginWithGoogle() {
            showStatus('Opening Google Sign-In...');
            const redirectUri = `${API_URL}/auth/oauth/callback/google`;
            const googleUrl = `${API_URL}/auth/oauth/login/google?redirect_uri=${encodeURIComponent(
                redirectUri
            )}`;
            window.location.href = googleUrl;
        }

        async function loginWithApple() {
            showStatus('Opening Apple Sign-In...');
            const redirectUri = `${API_URL}/auth/oauth/callback/apple`;
            const appleUrl = `${API_URL}/auth/oauth/login/apple?redirect_uri=${encodeURIComponent(
                redirectUri
            )}`;
            window.location.href = appleUrl;
        }

        async function loginWithMicrosoft() {
            showStatus('Opening Microsoft Sign-In...');
            const redirectUri = `${API_URL}/auth/oauth/callback/microsoft`;
            const msUrl = `${API_URL}/auth/oauth/login/microsoft?redirect_uri=${encodeURIComponent(
                redirectUri
            )}`;
            window.location.href = msUrl;
        }
    </script>
</body>
</html>
"""
    return HTMLResponse(content=html_content)


# OAuth Provider Login Endpoints
@router.get("/login/{provider}")
async def oauth_provider_login(provider: str, redirect_uri: str, db: Session = Depends(get_db)):
    """Initiate OAuth flow for a provider"""
    try:
        # Validate redirect URI to prevent open redirect attacks
        if not is_safe_redirect_uri(redirect_uri):
            raise HTTPException(status_code=400, detail="Invalid redirect URI")
        
        auth_url = await OAuthService.get_authorization_url(provider, redirect_uri)
        # Strict validation: auth URL must be HTTPS and from known OAuth provider domains
        from urllib.parse import urlparse
        parsed = urlparse(auth_url)
        allowed_domains = ['accounts.google.com', 'login.microsoftonline.com']
        # Require HTTPS for production OAuth providers (allow localhost for dev)
        if parsed.hostname in allowed_domains:
            if parsed.scheme != 'https':
                raise HTTPException(status_code=400, detail="OAuth URL must use HTTPS")
        elif parsed.hostname not in ['localhost', '127.0.0.1']:
            raise HTTPException(status_code=400, detail="Invalid authorization URL")
        
        # Additional safety check: only redirect if domain is explicitly allowed
        if parsed.hostname not in allowed_domains + ['localhost', '127.0.0.1']:
            raise HTTPException(status_code=400, detail="Unauthorized redirect destination")
        
        return RedirectResponse(url=auth_url)
    except Exception:
        # Don't expose internal error details
        raise HTTPException(status_code=400, detail="OAuth authentication failed")


@router.get("/callback/{provider}")
async def oauth_callback(
    request: Request,
    provider: str,
    code: str,
    state: str = None,
    db: Session = Depends(get_db),
):
    """Handle OAuth callback from provider"""
    try:
        # Reconstruct the redirect_uri that was used in the authorization request
        # Azure load balancer terminates SSL, so check X-Forwarded-Proto header
        scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
        host = request.headers.get("host") or request.url.netloc
        
        # Validate scheme to prevent open redirect
        if scheme not in ["http", "https"]:
            raise HTTPException(status_code=400, detail="Invalid redirect scheme")
        
        redirect_uri = f"{scheme}://{host}/auth/oauth/callback/{provider}"

        print(
            f"[OAuth Callback] Provider: {sanitize_for_log(provider)}, redirect_uri: {sanitize_for_log(redirect_uri)}"
        )
        xfwd = sanitize_for_log(request.headers.get("x-forwarded-proto"))
        scheme_s = sanitize_for_log(request.url.scheme)
        print(f"[OAuth Callback] Headers - X-Forwarded-Proto: {xfwd}, scheme: {scheme_s}")

        result = await OAuthService.handle_callback(provider, code, redirect_uri, db)

        # Redirect to dashboard with token in URL so JavaScript can access it
        # The dashboard will save it to localStorage
        # Use hardcoded relative path to prevent open redirect attacks
        # Token is validated but we construct the URL safely
        token_value = result['access_token']
        # Validate token format before using
        if not all(c.isalnum() or c in '._-' for c in token_value):
            raise HTTPException(status_code=500, detail="Invalid token format")
        # Construct URL with string concatenation to avoid injection
        dashboard_url = "/auth/oauth/dashboard?token=" + token_value
        response = RedirectResponse(url=dashboard_url)
        
        # Sanitize cookie value to prevent injection (tokens are already base64-encoded JWT)
        # Additional validation: ensure token contains only safe characters
        token_value = result["access_token"]
        if not all(c.isalnum() or c in '._-' for c in token_value):
            raise HTTPException(status_code=500, detail="Invalid token format")
        
        response.set_cookie(
            key="mew_token",
            value=token_value,
            httponly=True,
            secure=True,
            samesite="lax",
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"OAuth authentication failed: {str(e)}")


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """OAuth callback and dashboard"""
    return HTMLResponse(
        content="""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mew Assistant - Dashboard</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont,
                'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }
        .user-info {
            background: #f7f9fc;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }
        .action-button {
            background: #667eea;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            margin: 10px 5px;
            cursor: pointer;
            font-size: 16px;
        }
        .logout-btn {
            background: #dc3545;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🐱 Welcome to Mew Assistant</h1>
        <div class="user-info" id="userInfo">
            <p>Loading user information...</p>
        </div>

        <h2>Quick Actions</h2>
        <button class="action-button" onclick="connectCalendar()">📅 Connect Calendar</button>
        <button class="action-button" onclick="viewSchedule()">📋 View Schedule</button>
        <button class="action-button logout-btn" onclick="logout()">🚪 Logout</button>
    </div>

    <script>
        const API_URL = window.location.origin;

        async function loadUserInfo() {
            const token = localStorage.getItem('mew_token') || getTokenFromURL();

            if (!token) {
                window.location.href = '/auth/oauth/login';
                return;
            }

            try {
                const response = await fetch(`${API_URL}/auth/me`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });

                if (response.ok) {
                    const user = await response.json();
                    localStorage.setItem('mew_token', token);
                    localStorage.setItem('mew_user', JSON.stringify(user));
                    displayUserInfo(user);
                } else {
                    window.location.href = '/auth/oauth/login';
                }
            } catch (error) {
                console.error('Error loading user:', error);
                window.location.href = '/auth/oauth/login';
            }
        }

        function getTokenFromURL() {
            const params = new URLSearchParams(window.location.search);
            return params.get('token');
        }

        function displayUserInfo(user) {
            // Use textContent to prevent XSS attacks from user-supplied data
            const userInfoDiv = document.getElementById('userInfo');
            userInfoDiv.innerHTML = '';

            // Create and safely append name
            const nameEl = document.createElement('h3');
            nameEl.textContent = '👤 ' + (user.full_name || 'User');
            userInfoDiv.appendChild(nameEl);

            // Create and safely append email
            const emailP = document.createElement('p');
            emailP.innerHTML = '<strong>Email:</strong> <span id="emailValue"></span>';
            document.getElementById('emailValue').textContent = user.email || 'N/A';
            userInfoDiv.appendChild(emailP);

            // Create and safely append role
            const roleP = document.createElement('p');
            roleP.innerHTML = '<strong>Role:</strong> <span id="roleValue"></span>';
            document.getElementById('roleValue').textContent = user.role || 'N/A';
            userInfoDiv.appendChild(roleP);

            // Add provider if present
            if (user.federated_provider) {
                const providerP = document.createElement('p');
                providerP.innerHTML = '<strong>Provider:</strong> <span id="providerValue"></span>';
                document.getElementById('providerValue').textContent = user.federated_provider;
                userInfoDiv.appendChild(providerP);
            }
        }

        function connectCalendar() {
            alert('Calendar connection coming soon!');
        }

        function viewSchedule() {
            alert('Schedule view coming soon!');
        }

        function logout() {
            localStorage.removeItem('mew_token');
            localStorage.removeItem('mew_user');
            window.location.href = '/auth/oauth/login';
        }

        loadUserInfo();
    </script>
</body>
</html>
"""
    )
