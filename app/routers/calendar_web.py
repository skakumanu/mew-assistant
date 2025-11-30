"""
Simple web page to view calendar - no downloads needed!
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["Calendar Web"])


@router.get("/calendar", response_class=HTMLResponse)
async def calendar_page(request: Request):
    """
    Simple web page to view calendar.
    No downloads, no complexity - just a webpage!
    """
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>My Calendar</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container {
                max-width: 700px;
                margin: 0 auto;
                background: white;
                border-radius: 20px;
                padding: 30px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }
            h1 { color: #667eea; font-size: 32px; margin-bottom: 10px; text-align: center; }
            .subtitle { text-align: center; color: #666; margin-bottom: 30px; }
            .big-button {
                display: block;
                width: 100%;
                background: #667eea;
                color: white;
                border: none;
                padding: 18px;
                border-radius: 12px;
                font-size: 18px;
                font-weight: bold;
                cursor: pointer;
                margin: 15px 0;
                text-decoration: none;
                text-align: center;
            }
            .big-button:hover { background: #5568d3; }
            .event {
                background: #f8f9fa;
                padding: 18px;
                border-radius: 12px;
                margin: 12px 0;
                border-left: 4px solid #667eea;
            }
            .event-title { font-weight: bold; font-size: 16px; margin-bottom: 8px; color: #333; }
            .event-time { color: #666; font-size: 14px; margin-bottom: 5px; }
            .event-location { color: #999; font-size: 13px; }
            .message {
                padding: 15px;
                border-radius: 10px;
                margin: 20px 0;
                text-align: center;
            }
            .success { background: #d4edda; color: #155724; border: 2px solid #c3e6cb; }
            .error { background: #f8d7da; color: #721c24; border: 2px solid #f5c6cb; }
            .info { background: #d1ecf1; color: #0c5460; border: 2px solid #bee5eb; }
            .loading {
                text-align: center;
                padding: 40px;
                color: #666;
                font-size: 18px;
            }
            .spinner {
                border: 4px solid #f3f3f3;
                border-top: 4px solid #667eea;
                border-radius: 50%;
                width: 50px;
                height: 50px;
                animation: spin 1s linear infinite;
                margin: 20px auto;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📅 My Calendar</h1>
            <p class="subtitle">View your Google Calendar events</p>
            
            <!-- Not signed in -->
            <div id="needSignIn" style="display:none;">
                <div class="message info">
                    <strong>👋 Welcome!</strong><br>
                    Sign in with Google to view your calendar
                </div>
                <a href="/auth/simple/google" class="big-button">
                    🔐 Sign in with Google
                </a>
            </div>
            
            <!-- Signed in -->
            <div id="signedIn" style="display:none;">
                <div class="message success" id="welcome"></div>
                <button onclick="loadCalendar()" class="big-button">
                    📅 Show My Events
                </button>
                <button onclick="signOut()" class="big-button" style="background:#6c757d; margin-top:10px;">
                    Sign Out
                </button>
            </div>
            
            <!-- Loading -->
            <div id="loading" style="display:none;">
                <div class="loading">
                    <div class="spinner"></div>
                    <p>Loading your calendar...</p>
                </div>
            </div>
            
            <!-- Messages -->
            <div id="message"></div>
            
            <!-- Events -->
            <div id="events"></div>
        </div>

        <script>
            // Check if user is signed in
            window.onload = function() {
                // Check for token in URL (from OAuth redirect)
                const urlParams = new URLSearchParams(window.location.search);
                const urlToken = urlParams.get('token');
                const userName = urlParams.get('name');
                
                if (urlToken) {
                    // Save token from URL to localStorage
                    localStorage.setItem('mew_token', urlToken);
                    if (userName) {
                        localStorage.setItem('mew_name', userName);
                    }
                    // Clean URL (remove token from address bar)
                    window.history.replaceState({}, document.title, '/calendar');
                }
                
                checkAuth();
            };
            
            function checkAuth() {
                const token = localStorage.getItem('mew_token');
                const userName = localStorage.getItem('mew_name');
                
                if (token) {
                    document.getElementById('signedIn').style.display = 'block';
                    document.getElementById('needSignIn').style.display = 'none';
                    document.getElementById('welcome').textContent = 'Welcome back, ' + (userName || 'there') + '! 👋';
                } else {
                    document.getElementById('signedIn').style.display = 'none';
                    document.getElementById('needSignIn').style.display = 'block';
                }
            }
            
            function signOut() {
                localStorage.removeItem('mew_token');
                localStorage.removeItem('mew_user');
                localStorage.removeItem('mew_name');
                location.reload();
            }
            
            function showMessage(text, type) {
                const msg = document.getElementById('message');
                msg.className = 'message ' + type;
                msg.innerHTML = text;
            }
            
            function loadCalendar() {
                const token = localStorage.getItem('mew_token');
                
                if (!token) {
                    showMessage('Please sign in first', 'error');
                    return;
                }
                
                document.getElementById('loading').style.display = 'block';
                document.getElementById('events').innerHTML = '';
                document.getElementById('message').innerHTML = '';
                
                fetch('/simple-calendar/events?max_results=25', {
                    headers: { 'Authorization': 'Bearer ' + token }
                })
                .then(response => {
                    if (!response.ok) {
                        if (response.status === 401) {
                            throw new Error('Your session expired. Please sign in again.');
                        }
                        throw new Error('Failed to load calendar');
                    }
                    return response.json();
                })
                .then(data => {
                    document.getElementById('loading').style.display = 'none';
                    
                    if (data.events && data.events.length > 0) {
                        showMessage('✅ Found ' + data.count + ' event' + (data.count !== 1 ? 's' : ''), 'success');
                        
                        const eventsDiv = document.getElementById('events');
                        data.events.forEach(event => {
                            const div = document.createElement('div');
                            div.className = 'event';
                            
                            const title = document.createElement('div');
                            title.className = 'event-title';
                            title.textContent = event.summary || 'Untitled Event';
                            
                            const time = document.createElement('div');
                            time.className = 'event-time';
                            const date = new Date(event.start);
                            time.textContent = '🕐 ' + date.toLocaleString();
                            
                            div.appendChild(title);
                            div.appendChild(time);
                            
                            if (event.location) {
                                const loc = document.createElement('div');
                                loc.className = 'event-location';
                                loc.textContent = '📍 ' + event.location;
                                div.appendChild(loc);
                            }
                            
                            eventsDiv.appendChild(div);
                        });
                    } else {
                        showMessage('📭 No events found in your calendar', 'info');
                    }
                })
                .catch(error => {
                    document.getElementById('loading').style.display = 'none';
                    showMessage('❌ ' + error.message, 'error');
                    if (error.message.includes('expired')) {
                        setTimeout(() => location.reload(), 2000);
                    }
                });
            }
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html)


@router.get("/test-token")
async def test_token():
    """Debug endpoint to test token generation"""
    from ..utils.auth import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
    
    test_data = {"sub": "test", "email": "test@test.com", "role": "user"}
    token = create_access_token(test_data)
    
    return {
        "token_length": len(token),
        "token_preview": token[:50] + "...",
        "expire_minutes_setting": ACCESS_TOKEN_EXPIRE_MINUTES,
        "expire_days": ACCESS_TOKEN_EXPIRE_MINUTES / 1440
    }
