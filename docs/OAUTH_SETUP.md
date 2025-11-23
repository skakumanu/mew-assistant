# OAuth Federated Authentication Setup Guide

Mew Assistant supports federated authentication through multiple OAuth providers, allowing users to sign in with their existing accounts.

## Supported Providers

- **Google** - Most popular, easiest to setup
- **Microsoft** - Great for enterprise users
- **Apple** - Required for iOS/macOS users
- **Facebook** - Additional social login option

## Why Use OAuth?

✅ **Easy Onboarding** - Users don't need to create new passwords
✅ **Secure** - Providers handle authentication security
✅ **Trusted** - Users trust established providers
✅ **Email Verified** - Providers verify email addresses
✅ **Calendar Integration** - Direct access to user calendars

---

## Quick Setup (Development)

For local development, you can skip OAuth configuration. The system will gracefully handle missing OAuth providers.

```bash
# OAuth is optional - app works without it
# Just use regular email/password registration
curl -X POST http://localhost:8888/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "your-password",
    "full_name": "Your Name"
  }'
```

---

## Production Setup

### 1. Google OAuth Setup

**Best for:** Most users, easy setup, calendar integration

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google+ API and Google Calendar API
4. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**
5. Configure OAuth consent screen:
   - User Type: External
   - App name: Mew Assistant
   - Support email: your email
   - Scopes: `email`, `profile`, `openid`
6. Create OAuth Client ID:
   - Application type: Web application
   - Authorized redirect URIs:
     ```
     https://yourdomain.com/auth/oauth/callback/google
     http://localhost:8888/auth/oauth/callback/google  # for dev
     ```
7. Save **Client ID** and **Client Secret**

**Add to .env:**
```bash
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
```

### 2. Microsoft OAuth Setup

**Best for:** Enterprise users, Outlook integration

1. Go to [Azure Portal](https://portal.azure.com/)
2. Navigate to **Azure Active Directory** → **App registrations**
3. Click **New registration**:
   - Name: Mew Assistant
   - Supported account types: Multitenant
   - Redirect URI: Web - `https://yourdomain.com/auth/oauth/callback/microsoft`
4. After creation, note the **Application (client) ID**
5. Go to **Certificates & secrets** → **New client secret**
6. Copy the secret value immediately (shown only once)
7. Go to **API permissions** → **Add permission**:
   - Microsoft Graph → Delegated permissions
   - Add: `User.Read`, `email`, `openid`, `profile`
8. Grant admin consent for permissions

**Add to .env:**
```bash
MICROSOFT_CLIENT_ID=your-application-id
MICROSOFT_CLIENT_SECRET=your-client-secret
```

### 3. Apple Sign In Setup

**Best for:** iOS/macOS users (required for App Store)

1. Go to [Apple Developer Portal](https://developer.apple.com/)
2. Navigate to **Certificates, Identifiers & Profiles**
3. Create a **Services ID**:
   - Description: Mew Assistant
   - Identifier: com.mewassistant.service
4. Configure **Sign in with Apple**:
   - Enable for the Services ID
   - Domains: yourdomain.com
   - Return URLs: `https://yourdomain.com/auth/oauth/callback/apple`
5. Create a **Key** for Sign in with Apple:
   - Download and save the private key (.p8 file)
   - Note the Key ID
6. Note your Team ID from account page

**Add to .env:**
```bash
APPLE_CLIENT_ID=com.mewassistant.service
APPLE_CLIENT_SECRET=your-p8-key-contents
APPLE_TEAM_ID=your-team-id
APPLE_KEY_ID=your-key-id
```

### 4. Facebook Login Setup

**Best for:** Additional social login option

1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Create an app → Consumer
3. Add **Facebook Login** product
4. Configure OAuth Redirect URIs:
   ```
   https://yourdomain.com/auth/oauth/callback/facebook
   ```
5. Go to **Settings** → **Basic**
6. Note **App ID** and **App Secret**
7. Make app public when ready for production

**Add to .env:**
```bash
FACEBOOK_CLIENT_ID=your-app-id
FACEBOOK_CLIENT_SECRET=your-app-secret
```

---

## Environment Configuration

Update your `.env` file with all configured providers:

```bash
# OAuth Configuration
OAUTH_REDIRECT_URL=https://yourdomain.com

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-secret

# Microsoft OAuth
MICROSOFT_CLIENT_ID=your-microsoft-client-id
MICROSOFT_CLIENT_SECRET=your-microsoft-secret

# Apple OAuth
APPLE_CLIENT_ID=your-apple-client-id
APPLE_CLIENT_SECRET=your-apple-secret

# Facebook OAuth
FACEBOOK_CLIENT_ID=your-facebook-app-id
FACEBOOK_CLIENT_SECRET=your-facebook-secret
```

---

## User Flow

### 1. New User Registration via OAuth

```bash
# Step 1: Get authorization URL
GET /auth/oauth/providers
# Returns list of available providers

# Step 2: Redirect user to provider
GET /auth/oauth/login/google
# Redirects to Google login

# Step 3: Provider redirects back with code
GET /auth/oauth/callback/google?code=xxx
# Returns: { access_token, user_info }
```

### 2. Link OAuth to Existing Account

```bash
# User already logged in, wants to link Google
POST /auth/oauth/link
{
  "provider": "google",
  "code": "authorization-code",
  "redirect_uri": "https://yourdomain.com/auth/oauth/callback/google"
}
```

### 3. View Linked Providers

```bash
GET /auth/oauth/linked
Authorization: Bearer your-jwt-token

# Returns:
{
  "linked_providers": [
    {
      "provider": "google",
      "linked_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-15T10:30:00"
    }
  ]
}
```

### 4. Unlink Provider

```bash
DELETE /auth/oauth/unlink/google
Authorization: Bearer your-jwt-token
```

---

## Testing OAuth Locally

### Using ngrok for Local Testing

OAuth providers require HTTPS callbacks. Use ngrok for local development:

```bash
# Start ngrok
ngrok http 8888

# Note the HTTPS URL (e.g., https://abc123.ngrok.io)
# Update OAuth redirect URIs in provider console to:
https://abc123.ngrok.io/auth/oauth/callback/google

# Update .env
OAUTH_REDIRECT_URL=https://abc123.ngrok.io

# Start app
python -m uvicorn app.main:app --port 8888
```

### Test Flow

1. Open browser: `https://abc123.ngrok.io/auth/oauth/login/google`
2. Complete Google sign-in
3. You'll be redirected back with token

---

## Security Best Practices

### 1. Secure Token Storage

```python
# Never log or expose tokens
# Store encrypted in database
# Use Azure Key Vault in production
```

### 2. Token Refresh

```python
# OAuth tokens expire - implement refresh
# Check token_expires_at before using
# Use refresh_token to get new access_token
```

### 3. Scope Minimization

```python
# Only request necessary scopes
# Google: openid, email, profile (+ calendar if needed)
# Microsoft: User.Read, email
# Apple: name, email
```

### 4. State Parameter

```python
# Use state parameter to prevent CSRF
# Validate state on callback
# Include in authorization URL
```

---

## Frontend Integration

### React Example

```javascript
// OAuth Login Button
const handleGoogleLogin = () => {
  window.location.href = 'https://api.yourdomain.com/auth/oauth/login/google';
};

// Handle Callback
useEffect(() => {
  const params = new URLSearchParams(window.location.search);
  const token = params.get('access_token');
  if (token) {
    localStorage.setItem('auth_token', token);
    // Redirect to dashboard
  }
}, []);
```

### Mobile Apps

#### iOS (Swift)

```swift
import AuthenticationServices

// Sign in with Apple
let provider = ASAuthorizationAppleIDProvider()
let request = provider.createRequest()
request.requestedScopes = [.fullName, .email]

// Handle callback
func authorizationController(controller: ASAuthorizationController, 
                            didCompleteWithAuthorization authorization: ASAuthorization) {
    // Send code to backend
    let code = credential.authorizationCode
    // POST to /auth/oauth/callback/apple
}
```

#### Android (Kotlin)

```kotlin
// Google Sign-In
val gso = GoogleSignInOptions.Builder(GoogleSignInOptions.DEFAULT_SIGN_IN)
    .requestEmail()
    .requestIdToken(getString(R.string.google_client_id))
    .build()

val googleSignInClient = GoogleSignIn.getClient(this, gso)

// Handle callback
val idToken = account.idToken
// Send to backend: POST /auth/oauth/callback/google
```

---

## Troubleshooting

### Common Issues

**1. "Invalid redirect URI"**
- Verify redirect URI in provider console matches exactly
- Include protocol (https://)
- No trailing slashes unless in code

**2. "Invalid client"**
- Check CLIENT_ID and CLIENT_SECRET in .env
- Ensure no extra spaces or quotes

**3. "Email not provided"**
- Ensure email scope is requested
- Some providers (Apple) allow users to hide email
- Handle gracefully with error message

**4. "Token expired"**
- Implement token refresh logic
- Check token_expires_at before using
- Use refresh_token to get new access_token

### Debug Mode

```bash
# Enable debug logging
LOG_LEVEL=DEBUG

# Check OAuth flow
tail -f app.log | grep oauth
```

---

## Calendar Integration Benefits

When users authenticate via OAuth, you can automatically access their calendars:

- **Google Calendar** - Full read/write access
- **Microsoft Outlook** - Full calendar integration
- **Apple Calendar** - Via CalDAV with OAuth tokens

This enables Mew Assistant to:
- Read existing appointments
- Detect scheduling conflicts
- Add new events automatically
- Send calendar invitations
- Sync across all devices

---

## Migration from Password Auth

Existing password users can link OAuth providers:

```bash
# User logs in with password
POST /auth/login
{ "email": "user@example.com", "password": "xxx" }

# Link Google account
POST /auth/oauth/link
{ "provider": "google", "code": "..." }

# User can now login with either method
```

---

## Monitoring

Track OAuth usage in your analytics:

```python
# Log successful OAuth logins
logger.info(f"OAuth login: provider={provider}, user_id={user.id}")

# Monitor conversion rates
# Track which providers users prefer
# Measure registration completion rate
```

---

## Support

For OAuth-specific issues:
- Check provider status pages
- Review provider documentation
- Test with OAuth playground tools
- Enable debug logging

Remember: OAuth is optional. Users can always use email/password registration.
