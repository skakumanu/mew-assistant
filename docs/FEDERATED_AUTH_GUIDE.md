# Federated Authentication Guide

## Overview
Mew Assistant supports federated authentication allowing users to sign in with their existing accounts from Google, Apple, or Microsoft. This provides a seamless, secure onboarding experience without creating new passwords.

## Supported Providers
- 🔵 **Google** - Sign in with Google account
- 🍎 **Apple** - Sign in with Apple ID
- 🔷 **Microsoft** - Sign in with Microsoft account

## User Onboarding Flow

### Option 1: Web Application (Recommended for First-Time Setup)

1. **Visit the Mew Assistant Web App**
   ```
   https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io
   ```

2. **Click "Sign In" or "Get Started"**

3. **Choose Your Provider**
   - Click the "Continue with Google" button
   - Click the "Continue with Apple" button
   - Click the "Continue with Microsoft" button

4. **Authorize Access**
   - You'll be redirected to your provider's login page
   - Sign in with your existing credentials
   - Grant Mew Assistant permission to access your basic profile info

5. **Complete Your Profile**
   - Select your role (Parent, Caregiver, Tutor, or Kid)
   - Add phone number (optional but recommended for SMS features)
   - Set your preferences

6. **Done!** You're now registered and can start using Mew Assistant

### Option 2: Mobile App

1. **Download the Mew Assistant App**
   - iOS: App Store (coming soon)
   - Android: Google Play (coming soon)

2. **Open the App and Tap "Sign In"**

3. **Choose Your Provider**
   - Tap "Sign in with Google"
   - Tap "Sign in with Apple" (iOS only)
   - Tap "Sign in with Microsoft"

4. **Authorize**
   - Use Face ID, Touch ID, or your provider credentials
   - Grant permissions

5. **Set Up Profile**
   - Complete your role and preferences
   - Enable notifications

### Option 3: Voice Assistant

**For Alexa:**
```
"Alexa, open Mew Assistant"
"Link my account"
[Follow voice prompts to complete linking via Alexa app]
```

**For Google Assistant:**
```
"Hey Google, talk to Mew Assistant"
"Link my account"
[Follow voice prompts to complete linking]
```

**For Siri:**
```
"Hey Siri, set up Mew Assistant"
[Opens setup page with federated auth options]
```

## What Data Is Shared?

### Google Authentication
- ✅ Email address
- ✅ Full name
- ✅ Profile picture
- ❌ We do NOT access your Gmail, Drive, or other Google services

### Apple Authentication
- ✅ Email address (or relay email if you choose)
- ✅ Full name
- ❌ Minimal data sharing (Apple's privacy-first approach)

### Microsoft Authentication
- ✅ Email address
- ✅ Full name
- ✅ Profile picture
- ❌ We do NOT access your Outlook, OneDrive, or other Microsoft services

## Security Features

### OAuth 2.0 Standard
All federated authentication uses industry-standard OAuth 2.0 protocol, ensuring:
- No password storage in Mew Assistant
- Secure token-based authentication
- Regular token refresh for security
- Instant revocation capability

### Privacy Protection
- Your provider credentials are NEVER shared with Mew Assistant
- All data transmission is encrypted (HTTPS/TLS)
- Tokens are stored securely in Azure Key Vault
- HIPAA and FERPA compliant

### Account Security
- Multi-factor authentication (if enabled with your provider)
- Automatic session timeout
- Device-specific authentication
- Suspicious activity monitoring

## Managing Your Connected Account

### View Connected Accounts
```bash
curl -X GET https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/auth/oauth/linked \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Unlink a Provider
```bash
curl -X POST https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/auth/oauth/unlink \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"provider": "google"}'
```

### Add Additional Providers
You can link multiple providers to the same Mew Assistant account for flexibility:
```bash
curl -X GET https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/auth/oauth/google/login \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Troubleshooting

### "Unable to Connect to Provider"
- Check your internet connection
- Verify the provider's service status
- Clear browser cache/cookies
- Try a different browser

### "Authorization Failed"
- Ensure you're using the correct credentials
- Check if you granted all required permissions
- Verify your email is confirmed with the provider

### "Account Already Exists"
- This email is already registered with a different method
- Use the original sign-in method
- Or contact support to merge accounts

### "Provider Connection Lost"
- Re-authenticate by clicking your profile
- Select "Reconnect Account"
- Follow the authorization flow again

## For Developers

### Integration Endpoints

**Initiate OAuth Flow:**
```
GET /auth/oauth/{provider}/login
Providers: google, apple, microsoft
```

**OAuth Callback:**
```
GET /auth/oauth/{provider}/callback
Handles the redirect after user authorization
```

**Link Additional Provider:**
```
POST /auth/oauth/{provider}/link
Requires existing authentication token
```

### Testing Locally

1. **Set up OAuth credentials:**
   ```bash
   # Google Cloud Console
   GOOGLE_CLIENT_ID=your-client-id
   GOOGLE_CLIENT_SECRET=your-client-secret
   
   # Apple Developer
   APPLE_CLIENT_ID=your-service-id
   APPLE_TEAM_ID=your-team-id
   APPLE_KEY_ID=your-key-id
   
   # Microsoft Azure AD
   MICROSOFT_CLIENT_ID=your-client-id
   MICROSOFT_CLIENT_SECRET=your-client-secret
   ```

2. **Update .env file with test credentials**

3. **Run local server:**
   ```bash
   ./podman-start.sh
   ```

4. **Test OAuth flow:**
   ```
   http://localhost:8888/auth/oauth/google/login
   ```

## Support

### Need Help?
- 📧 Email: support@mew-assistant.org (coming soon)
- 💬 Discord: Join our community (link in README)
- 📖 Documentation: https://github.com/yourusername/mew-assistant

### Privacy Concerns?
Review our Privacy Policy: [docs/PRIVACY.md](PRIVACY.md)

### Report Security Issues
Please report security vulnerabilities privately to: security@mew-assistant.org

---

**Note:** Federated authentication is the recommended way to use Mew Assistant as it provides:
- ✅ Faster onboarding (no password creation)
- ✅ Better security (provider-managed credentials)
- ✅ Seamless calendar integration
- ✅ One-click setup across all platforms
