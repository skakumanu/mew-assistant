"""
Simple debug page to test API calls
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["Debug"])


@router.get("/debug-calendar", response_class=HTMLResponse)
async def debug_calendar_page():
    """Debug page with big buttons to test the API"""

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Debug Calendar API</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: monospace;
                background: #1e1e1e;
                color: #fff;
                padding: 20px;
            }
            .container {
                max-width: 900px;
                margin: 0 auto;
            }
            h1 { color: #4CAF50; margin-bottom: 20px; }
            button {
                background: #4CAF50;
                color: white;
                border: none;
                padding: 15px 30px;
                margin: 10px 5px;
                border-radius: 5px;
                font-size: 16px;
                cursor: pointer;
                font-family: monospace;
            }
            button:hover { background: #45a049; }
            #output {
                background: #000;
                color: #0f0;
                padding: 20px;
                border-radius: 5px;
                margin-top: 20px;
                min-height: 400px;
                white-space: pre-wrap;
                font-size: 14px;
                overflow-x: auto;
            }
            .success { color: #4CAF50; }
            .error { color: #f44336; }
            .warning { color: #ff9800; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔍 Calendar API Debug Tool</h1>

            <div>
                <button onclick="checkToken()">1. Check Token</button>
                <button onclick="testAPI()">2. Test API Call</button>
                <button onclick="clearOutput()">Clear Output</button>
            </div>

            <pre id="output">Click buttons above to debug...</pre>
        </div>

        <script>
            const API = 'https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io';
            let output = document.getElementById('output');

            function log(msg, type = 'normal') {
                const timestamp = new Date().toLocaleTimeString();
                let color = '';
                if (type === 'success') color = 'success';
                if (type === 'error') color = 'error';
                if (type === 'warning') color = 'warning';

                const span = document.createElement('span');
                span.className = color;
                span.textContent = `[${timestamp}] ${msg}\n`;
                output.appendChild(span);
                output.scrollTop = output.scrollHeight;
            }

            function clearOutput() {
                output.textContent = 'Output cleared.\n\n';
            }

            function checkToken() {
                log('=== CHECKING TOKEN ===', 'success');

                const token = localStorage.getItem('mew_token');
                const name = localStorage.getItem('mew_name');
                const user = localStorage.getItem('mew_user');

                if (!token) {
                    log('❌ NO TOKEN FOUND!', 'error');
                    log('You need to sign in first at /calendar', 'warning');
                    return;
                }

                log(`✅ Token exists: ${token.substring(0, 30)}...`, 'success');
                log(`✅ Name: ${name}`, 'success');
                log(`✅ User: ${user}`, 'success');
                log(`Token length: ${token.length} characters`);

                // Try to decode the JWT (without verification)
                try {
                    const parts = token.split('.');
                    if (parts.length === 3) {
                        const payload = JSON.parse(atob(parts[1]));
                        log(`Token payload: ${JSON.stringify(payload, null, 2)}`);

                        const exp = new Date(payload.exp * 1000);
                        const now = new Date();
                        const daysLeft = Math.floor((exp - now) / (1000 * 60 * 60 * 24));

                        if (exp > now) {
                            log(`✅ Token expires: ${exp.toLocaleString()}`, 'success');
                            log(`✅ Days left: ${daysLeft}`, 'success');
                        } else {
                            log(`❌ TOKEN EXPIRED at ${exp.toLocaleString()}!`, 'error');
                        }
                    }
                } catch (e) {
                    log(`⚠️ Could not decode token: ${e.message}`, 'warning');
                }

                log('\\n');
            }

            async function testAPI() {
                log('=== TESTING API CALL ===', 'success');

                const token = localStorage.getItem('mew_token');

                if (!token) {
                    log('❌ No token found! Sign in first.', 'error');
                    return;
                }

                log('Calling: GET /simple-calendar/events?max_results=5');
                log('Authorization: Bearer ' + token.substring(0, 20) + '...');
                log('');

                try {
                    const response = await fetch(API + '/simple-calendar/events?max_results=5', {
                        headers: {
                            'Authorization': 'Bearer ' + token,
                            'Accept': 'application/json'
                        }
                    });

                    log(`Response Status: ${response.status} ${response.statusText}`,
                        response.ok ? 'success' : 'error');

                    const contentType = response.headers.get('content-type');
                    log(`Content-Type: ${contentType}`);

                    const text = await response.text();
                    log('');
                    log('Response Body:');

                    try {
                        const json = JSON.parse(text);
                        log(JSON.stringify(json, null, 2), response.ok ? 'success' : 'error');

                        if (response.ok && json.events) {
                            log('', 'success');
                            log(`✅ SUCCESS! Found ${json.count} events`, 'success');
                        }
                    } catch (e) {
                        log(text, 'error');
                    }

                } catch (error) {
                    log(`❌ Network Error: ${error.message}`, 'error');
                    log(`Error details: ${error.stack}`, 'error');
                }

                log('\\n');
            }
        </script>
    </body>
    </html>
    """

    return HTMLResponse(content=html)
