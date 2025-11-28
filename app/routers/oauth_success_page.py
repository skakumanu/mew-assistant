"""Simple success page for OAuth flows"""

def get_success_page(user_name: str, user_email: str, jwt_token: str) -> str:
    """
    Returns a simple, user-friendly success page after OAuth login.
    No technical jargon - just tells users they're connected and what to do next.
    """
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>✅ You're In!</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            .container {{
                background: white;
                border-radius: 20px;
                padding: 40px 30px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                max-width: 450px;
                width: 100%;
                text-align: center;
            }}
            .icon {{ font-size: 72px; margin-bottom: 20px; animation: bounce 1s; }}
            @keyframes bounce {{
                0%, 100% {{ transform: translateY(0); }}
                50% {{ transform: translateY(-20px); }}
            }}
            h1 {{ color: #667eea; margin-bottom: 10px; font-size: 32px; }}
            .subtitle {{ color: #666; margin-bottom: 30px; font-size: 18px; line-height: 1.5; }}
            .info-box {{
                background: #f8f9fa;
                padding: 20px;
                border-radius: 12px;
                margin: 25px 0;
                font-size: 15px;
                color: #495057;
                text-align: left;
            }}
            .info-box strong {{ color: #667eea; display: block; margin-bottom: 10px; }}
            .info-box div {{ margin: 8px 0 8px 20px; }}
            .note {{ color: #999; font-size: 14px; margin-top: 25px; line-height: 1.6; }}
            .btn {{
                display: inline-block;
                background: #667eea;
                color: white;
                padding: 15px 30px;
                border-radius: 10px;
                text-decoration: none;
                font-weight: 600;
                margin: 10px 0;
                transition: all 0.3s;
            }}
            .btn:hover {{ background: #5568d3; transform: translateY(-2px); }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="icon">🎉</div>
            <h1>You're All Set!</h1>
            <p class="subtitle">
                Hi {user_name}!<br>
                Your calendar is connected.
            </p>
            
            <div class="info-box">
                <strong>✅ What you can do now:</strong>
                <div>• View your Google Calendar</div>
                <div>• Check your schedule anytime</div>
                <div>• (Coming soon: Ask Siri!)</div>
            </div>
            
            <a href="https://raw.githubusercontent.com/skakumanu/mew-assistant/feature/customerzerosetup/calendar-viewer.html" 
               class="btn" download="calendar-viewer.html">
                📅 Download Calendar Viewer
            </a>
            
            <p class="note">
                📱 <strong>How to use:</strong><br>
                1. Download the file above<br>
                2. Open it in your browser<br>
                3. Your calendar will show automatically!
            </p>
            
            <p class="note" style="margin-top: 20px; border-top: 1px solid #eee; padding-top: 20px;">
                🔐 Logged in for 30 days<br>
                Just sign in again if needed
            </p>
        </div>
        
        <script>
            // Quietly save login info for later
            localStorage.setItem('mew_token', '{jwt_token}');
            localStorage.setItem('mew_user', '{user_email}');
            localStorage.setItem('mew_name', '{user_name}');
            
            // Log success for debugging
            console.log('✅ Mew Assistant: Logged in successfully');
            
            // If user already has calendar viewer open in another tab, they can just refresh it
            console.log('💡 Tip: If you have calendar-viewer.html open, just refresh that page!');
        </script>
    </body>
    </html>
    """
