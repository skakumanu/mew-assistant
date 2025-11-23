
## Bot Protection

Mew Assistant includes comprehensive bot protection to prevent automated attacks, spam, and abuse.

### Features

1. **Rate Limiting**
   - 100 requests per minute per client
   - Automatic IP blocking for 15 minutes after exceeding limit
   - Per-client fingerprinting (IP + User-Agent)

2. **Suspicious Content Detection**
   - SQL injection pattern detection
   - XSS (Cross-Site Scripting) detection
   - Command injection prevention
   - Regex-based pattern matching in:
     - URL paths
     - Query parameters
     - Request body

3. **User-Agent Validation**
   - Requires valid User-Agent header
   - Blocks known malicious bots (sqlmap, nikto, etc.)
   - Allows legitimate browsers and voice assistants

4. **IP Blocking**
   - Temporary blocks (15 minutes) for rate limit violations
   - Automatic cleanup of expired blocks
   - X-Forwarded-For and X-Real-IP support for proxies

5. **CAPTCHA Protection**
   - Simple math challenges for critical operations
   - 5-minute expiration
   - Automatic cleanup of expired challenges

### Usage

#### Rate Limiting

Rate limiting is automatic. Clients exceeding 100 requests/minute receive:

```json
{
  "error": "Rate limit exceeded. Your IP has been temporarily blocked.",
  "retry_after": 900
}
```

#### CAPTCHA for Critical Operations

For sensitive operations (registration, password reset, etc.):

```bash
# 1. Get CAPTCHA challenge
curl -X GET http://localhost:8888/auth/captcha/challenge?user_id=optional_user_id

# Response:
# {
#   "challenge_id": "abc123",
#   "question": "What is 5 + 3?",
#   "expires_in": 300
# }

# 2. Solve and verify
curl -X POST "http://localhost:8888/auth/captcha/verify?challenge_id=abc123&response=8"

# Response:
# {"verified": true}
```

### Configuration

Adjust rate limits in `app/main.py`:

```python
app.add_middleware(
    BotProtectionMiddleware,
    rate_limit=100,      # Requests per window
    window_seconds=60    # Time window in seconds
)
```

### Monitoring

Check bot protection logs:
```bash
grep "BotProtection" logs/app.log
```

### Whitelisting

To whitelist specific IPs or User-Agents, modify `app/middleware/bot_protection.py`:

```python
WHITELISTED_IPS = ["1.2.3.4", "5.6.7.8"]
WHITELISTED_AGENTS = ["MyTrustedBot/1.0"]
```

