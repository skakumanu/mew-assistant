from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
import os

router = APIRouter(prefix="/auth/oauth", tags=["OAuth Web"])

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
            <svg width="18" height="18" xmlns="http://www.w3.org/2000/svg"><path d="M9 3.48c1.69 0 2.83.73 3.48 1.34l2.54-2.48C13.46.89 11.43 0 9 0 5.48 0 2.44 2.02.96 4.96l2.91 2.26C4.6 5.05 6.62 3.48 9 3.48z" fill="#EA4335"/><path d="M17.64 9.2c0-.74-.06-1.28-.19-1.84H9v3.34h4.96c-.1.83-.64 2.08-1.84 2.92l2.84 2.2c1.7-1.57 2.68-3.88 2.68-6.62z" fill="#4285F4"/><path d="M3.88 10.78A5.54 5.54 0 0 1 3.58 9c0-.62.11-1.22.29-1.78L.96 4.96A9.008 9.008 0 0 0 0 9c0 1.45.35 2.82.96 4.04l2.92-2.26z" fill="#FBBC05"/><path d="M9 18c2.43 0 4.47-.8 5.96-2.18l-2.84-2.2c-.76.53-1.78.9-3.12.9-2.38 0-4.4-1.57-5.12-3.74L.97 13.04C2.45 15.98 5.48 18 9 18z" fill="#34A853"/></svg>
            Continue with Google
        </button>
        
        <button class="login-button apple-btn" onclick="loginWithApple()">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="white"><path d="M17.05 20.28c-.98.95-2.05.88-3.08.4-1.09-.5-2.08-.48-3.24 0-1.44.62-2.2.44-3.06-.4C2.79 15.25 3.51 7.59 9.05 7.31c1.35.07 2.29.74 3.08.8 1.18-.24 2.31-.93 3.57-.84 1.51.12 2.65.72 3.4 1.8-3.12 1.87-2.38 5.98.48 7.13-.57 1.5-1.31 2.99-2.54 4.09l.01-.01zM12.03 7.25c-.15-2.23 1.66-4.07 3.74-4.25.29 2.58-2.34 4.5-3.74 4.25z"/></svg>
            Continue with Apple
        </button>
        
        <button class="login-button microsoft-btn" onclick="loginWithMicrosoft()">
            <svg width="18" height="18" viewBox="0 0 23 23" fill="white"><path d="M0 0h11v11H0z"/><path d="M12 0h11v11H12z"/><path d="M0 12h11v11H0z"/><path d="M12 12h11v11H12z"/></svg>
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
                    body: JSON.stringify({ email, password })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    localStorage.setItem('mew_token', data.access_token);
                    localStorage.setItem('mew_user', JSON.stringify(data.user));
                    showStatus('Login successful! Redirecting...');
                    setTimeout(() => {
                        window.location.href = '/oauth/dashboard';
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
            window.location.href = `${API_URL}/auth/google/authorize`;
        }
        
        async function loginWithApple() {
            showStatus('Opening Apple Sign-In...');
            window.location.href = `${API_URL}/auth/apple/authorize`;
        }
        
        async function loginWithMicrosoft() {
            showStatus('Opening Microsoft Sign-In...');
            window.location.href = `${API_URL}/auth/microsoft/authorize`;
        }
    </script>
</body>
</html>
"""
    return HTMLResponse(content=html_content)

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """OAuth callback and dashboard"""
    return HTMLResponse(content="""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mew Assistant - Dashboard</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
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
                window.location.href = '/oauth/login';
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
                    window.location.href = '/oauth/login';
                }
            } catch (error) {
                console.error('Error loading user:', error);
                window.location.href = '/oauth/login';
            }
        }
        
        function getTokenFromURL() {
            const params = new URLSearchParams(window.location.search);
            return params.get('token');
        }
        
        function displayUserInfo(user) {
            document.getElementById('userInfo').innerHTML = `
                <h3>👤 ${user.full_name}</h3>
                <p><strong>Email:</strong> ${user.email}</p>
                <p><strong>Role:</strong> ${user.role}</p>
                ${user.federated_provider ? `<p><strong>Provider:</strong> ${user.federated_provider}</p>` : ''}
            `;
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
            window.location.href = '/oauth/login';
        }
        
        loadUserInfo();
    </script>
</body>
</html>
""")
