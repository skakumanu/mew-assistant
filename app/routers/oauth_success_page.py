"""Simple success page for OAuth flows"""

def get_success_page(user_name: str, user_email: str, jwt_token: str) -> str:
    """
    Returns a simple, user-friendly success page after OAuth login.
    Hides technical details, auto-redirects to simple viewer.
    """
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>✅ Connected!</title>
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
            .big-box {{
                background: #e8f5e9;
                padding: 25px;
                border-radius: 12px;
                margin: 25px 0;
                border: 2px solid #4caf50;
            }}
            .big-box .title {{ 
                font-size: 20px; 
                font-weight: bold; 
                color: #2e7d32; 
                margin-bottom: 15px; 
            }}
            .big-box .step {{ 
                background: white;
                padding: 12px;
                margin: 8px 0;
                border-radius: 6px;
                color: #333;
            }}
            .note {{ color: #999; font-size: 14px; margin-top: 25px; line-height: 1.6; }}
            .countdown {{
                color: #667eea;
                font-size: 16px;
                margin: 20px 0;
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="icon">🎉</div>
            <h1>Success!</h1>
            <p class="subtitle">
                Hi {user_name}!<br>
                Your Google Calendar is connected.
            </p>
            
            <div class="big-box">
                <div class="title">🎯 Next: View Your Calendar</div>
                <div class="step">1️⃣ Download the calendar viewer file</div>
                <div class="step">2️⃣ Open it in your browser</div>
                <div class="step">3️⃣ Click "Show My Events"</div>
            </div>
            
            <div class="countdown" id="countdown">
                Downloading calendar viewer in <span id="timer">5</span> seconds...
            </div>
            
            <p class="note">
                💡 Can't find the download?<br>
                Check your Downloads folder for<br>
                <strong>calendar-simple.html</strong>
            </p>
        </div>
        
        <script>
            // Save login info silently
            localStorage.setItem('mew_token', '{jwt_token}');
            localStorage.setItem('mew_user', '{user_email}');
            localStorage.setItem('mew_name', '{user_name}');
            
            // Auto-download the simple calendar viewer after 5 seconds
            let seconds = 5;
            const timer = setInterval(() => {{
                seconds--;
                document.getElementById('timer').textContent = seconds;
                
                if (seconds <= 0) {{
                    clearInterval(timer);
                    document.getElementById('countdown').innerHTML = '⬇️ Downloading now...';
                    
                    // Trigger download
                    const link = document.createElement('a');
                    link.href = 'https://raw.githubusercontent.com/skakumanu/mew-assistant/feature/customerzerosetup/calendar-simple.html';
                    link.download = 'calendar-simple.html';
                    link.click();
                    
                    setTimeout(() => {{
                        document.getElementById('countdown').innerHTML = '✅ Download started!<br><small style="color:#666;">Open the file from your Downloads folder</small>';
                    }}, 1000);
                }}
            }}, 1000);
        </script>
    </body>
    </html>
    """
