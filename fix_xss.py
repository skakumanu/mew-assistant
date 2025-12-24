#!/usr/bin/env python3
"""Fix XSS vulnerabilities in OAuth pages"""

# Fix oauth_success_page.py
oauth_success_code = '''"""Simple success page for OAuth flows with XSS protection"""
import html
import json


def get_success_page(user_name: str, user_email: str, jwt_token: str) -> str:
    """
    Returns a simple, user-friendly success page after OAuth login.
    Properly escapes user data to prevent XSS attacks.
    """
    # Use JSON encoding for JavaScript variables (automatically escapes)
    js_data = json.dumps({
        'name': user_name or 'User',
        'email': user_email or '',
        'token': jwt_token or ''
    })
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>✅ Connected!</title>
        <style>
            body {{ font-family: -apple-system, 'Segoe UI'; text-align: center; padding: 40px; }}
            .success {{ color: #28a745; font-size: 24px; }}
        </style>
    </head>
    <body>
        <p class="success">✅ Success!</p>
        <p>Hi <span id="userDisplay"></span>!<br>Your calendar is connected.</p>
        <script>
            const userData = {js_data};
            document.getElementById('userDisplay').textContent = userData.name;
            try {{
                localStorage.setItem('mew_token', userData.token);
                localStorage.setItem('mew_user', userData.email);
                localStorage.setItem('mew_name', userData.name);
                setTimeout(function() {{ window.location.href = '/dashboard'; }}, 1000);
            }} catch (e) {{
                console.error('Error:', e);
            }}
        </script>
    </body>
    </html>
    """
'''

with open('app/routers/oauth_success_page.py', 'w', encoding='utf-8') as f:
    f.write(oauth_success_code)

print('✅ oauth_success_page.py fixed with XSS protection')
