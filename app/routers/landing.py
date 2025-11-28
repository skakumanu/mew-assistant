from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def landing_page():
    # Version identifier: LANDING_PAGE_V2_DEPLOYED
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Mew Assistant - Your Family's AI Assistant</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #333; min-height: 100vh; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .card { background: white; border-radius: 20px; padding: 40px 30px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); margin-top: 60px; }
            h1 { font-size: 2.5em; color: #667eea; text-align: center; margin-bottom: 10px; }
            .subtitle { text-align: center; color: #666; margin-bottom: 30px; font-size: 1.1em; }
            .btn { display: block; width: 100%; padding: 18px; margin: 15px 0; border: none; border-radius: 12px; font-size: 1.1em; font-weight: 600; cursor: pointer; transition: all 0.3s; text-decoration: none; text-align: center; }
            .btn-google { background: #fff; color: #333; border: 2px solid #ddd; }
            .btn-google:hover { background: #f8f9fa; transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
            .btn-apple { background: #000; color: #fff; }
            .btn-apple:hover { background: #333; transform: translateY(-2px); }
            .btn-microsoft { background: #00a4ef; color: #fff; }
            .btn-microsoft:hover { background: #0078d4; transform: translateY(-2px); }
            .features { margin-top: 30px; padding-top: 30px; border-top: 2px solid #f0f0f0; }
            .feature { display: flex; align-items: center; margin: 15px 0; }
            .feature-icon { font-size: 1.5em; margin-right: 15px; }
            .footer { text-align: center; color: rgba(255,255,255,0.8); margin-top: 30px; font-size: 0.9em; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="card">
                <h1>🐱 Mew Assistant</h1>
                <p class="subtitle">Your Family's AI-Powered Scheduling Assistant</p>
                
                <div>
                    <a href="/auth/simple/google" class="btn btn-google">
                        🔐 Sign in with Google
                    </a>
                    <a href="/auth/simple/microsoft" class="btn btn-microsoft">
                        🏢 Sign in with Microsoft
                    </a>
                </div>
                
                <div class="features">
                    <div class="feature">
                        <span class="feature-icon">📅</span>
                        <span>Smart scheduling with AI</span>
                    </div>
                    <div class="feature">
                        <span class="feature-icon">🗣️</span>
                        <span>Voice commands in 100+ languages</span>
                    </div>
                    <div class="feature">
                        <span class="feature-icon">👨‍👩‍👧‍👦</span>
                        <span>Family-friendly with parental controls</span>
                    </div>
                    <div class="feature">
                        <span class="feature-icon">🔒</span>
                        <span>Secure & private</span>
                    </div>
                </div>
            </div>
            
            <div class="footer">
                <p>© 2025 Mew Assistant | For special needs families</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html_content
