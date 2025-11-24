# OAuth Provider Setup Guide

## Overview

Mew Assistant supports OAuth login with **Google**, **Microsoft**, **Apple**, and **Facebook**. Each provider has different setup requirements.

## Quick Start Summary

| Provider | Difficulty | Setup Time | Key Requirements |
|----------|-----------|------------|------------------|
| Google | Easy | 10 min | Google Cloud Project |
| Microsoft | Easy | 10 min | Azure App Registration |
| Apple | Medium | 20 min | Apple Developer Account ($99/year), Private Key |
| Facebook | Easy | 10 min | Facebook Developer Account |

---

## 1. Google OAuth Setup

### Step 1: Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **Select a project** → **New Project**
3. Name: `Mew Assistant` → Click **Create**

### Step 2: Enable Google+ API
1. In the left sidebar, go to **APIs & Services** → **Library**
2. Search for "Google+ API"
3. Click **Enable**

### Step 3: Create OAuth Credentials
1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth client ID**
3. If prompted, configure consent screen:
   - User Type: **External**
   - App name: `Mew Assistant`
   - User support email: Your email
   - Developer contact: Your email
   - Click **Save and Continue** through all steps

4. Create OAuth Client ID:
   - Application type: **Web application**
   - Name: `Mew Assistant Web`
   - Authorized redirect URIs:
     ```
     https://your-production-url.azurecontainerapps.io/auth/oauth/callback/google
     http://localhost:8888/auth/oauth/callback/google
     ```
   - Click **Create**

5. **Copy Client ID and Client Secret**

### Step 4: Store in Azure Key Vault
```bash
az keyvault secret set --vault-name mew-keyvault --name "GOOGLE-CLIENT-ID" --value "YOUR_CLIENT_ID"
az keyvault secret set --vault-name mew-keyvault --name "GOOGLE-CLIENT-SECRET" --value "YOUR_CLIENT_SECRET"
```

---

## 2. Microsoft OAuth Setup

### Step 1: Register Application
1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **App registrations** → **New registration**
3. Name: `Mew Assistant`
4. Supported account types: **Accounts in any organizational directory and personal Microsoft accounts**
5. Redirect URI:
   - Platform: **Web**
   - URI: `https://your-production-url.azurecontainerapps.io/auth/oauth/callback/microsoft`
6. Click **Register**

### Step 2: Add Redirect URIs
1. Go to **Authentication** in left sidebar
2. Under **Web** → **Redirect URIs**, add:
   ```
   http://localhost:8888/auth/oauth/callback/microsoft
   ```
3. Click **Save**

### Step 3: Create Client Secret
1. Go to **Certificates & secrets** → **New client secret**
2. Description: `Mew Assistant OAuth`
3. Expires: **24 months** (or your preference)
4. Click **Add**
5. **Copy the secret Value immediately** (you can't see it again!)

### Step 4: Copy Application ID
1. Go to **Overview**
2. Copy **Application (client) ID**

### Step 5: Store in Azure Key Vault
```bash
az keyvault secret set --vault-name mew-keyvault --name "MICROSOFT-CLIENT-ID" --value "YOUR_CLIENT_ID"
az keyvault secret set --vault-name mew-keyvault --name "MICROSOFT-CLIENT-SECRET" --value "YOUR_CLIENT_SECRET"
```

---

## 3. Apple OAuth Setup (Sign in with Apple)

⚠️ **Requirements**: 
- Apple Developer Account ($99/year)
- Understanding of JWT and private keys

### Step 1: Create App ID
1. Go to [Apple Developer](https://developer.apple.com/account/)
2. Navigate to **Certificates, Identifiers & Profiles**
3. Click **Identifiers** → **+** → **App IDs** → **App**
4. Fill in:
   - Description: `Mew Assistant`
   - Bundle ID: `com.mewassistant.app` (or your reverse domain)
5. Enable **Sign in with Apple** capability
6. Click **Continue** → **Register**

### Step 2: Create Services ID
1. Go to **Identifiers** → **+** → **Services IDs**
2. Fill in:
   - Description: `Mew Assistant Web`
   - Identifier: `com.mewassistant.service`
3. Enable **Sign in with Apple**
4. Click **Configure** next to Sign in with Apple:
   - **Primary App ID**: Select the App ID created above
   - **Web Domain**: `your-production-domain.azurecontainerapps.io` (no https://)
   - **Return URLs**: 
     ```
     https://your-production-domain.azurecontainerapps.io/auth/oauth/callback/apple
     http://localhost:8888/auth/oauth/callback/apple
     ```
5. Click **Save** → **Continue** → **Register**

### Step 3: Create Private Key
1. Go to **Keys** → **+**
2. Key Name: `Mew Assistant Sign in with Apple Key`
3. Enable **Sign in with Apple**
4. Click **Configure** → Select your Primary App ID
5. Click **Save** → **Continue** → **Register**
6. **Download the .p8 key file** (⚠️ You can only download this once!)
7. **Note the Key ID** shown on the page

### Step 4: Get Team ID
1. Go to **Membership** in left sidebar
2. Copy your **Team ID** (10-character alphanumeric)

### Step 5: Store in Azure Key Vault
```bash
# Service ID (this is your Client ID)
az keyvault secret set --vault-name mew-keyvault --name "APPLE-CLIENT-ID" --value "com.mewassistant.service"

# Team ID
az keyvault secret set --vault-name mew-keyvault --name "APPLE-TEAM-ID" --value "YOUR_TEAM_ID"

# Key ID
az keyvault secret set --vault-name mew-keyvault --name "APPLE-KEY-ID" --value "YOUR_KEY_ID"

# Private Key (upload the .p8 file)
az keyvault secret set --vault-name mew-keyvault --name "APPLE-PRIVATE-KEY" --file "path/to/AuthKey_KEYID.p8"
```

### Apple OAuth Notes
- Apple uses JWT-based authentication (not traditional client secret)
- Private key must be kept secure and never committed to git
- Apple requires HTTPS in production
- User email may only be provided on first sign-in
- Supports "Hide My Email" - handle proxy emails gracefully

---

## 4. Facebook OAuth Setup

### Step 1: Create Facebook App
1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Click **My Apps** → **Create App**
3. Use case: **Consumer** → **Next**
4. App name: `Mew Assistant`
5. App contact email: Your email
6. Click **Create App**

### Step 2: Add Facebook Login
1. In dashboard, find **Facebook Login** → **Set Up**
2. Choose **Web**
3. Site URL: `https://your-production-url.azurecontainerapps.io`
4. Click **Save** → **Continue**

### Step 3: Configure OAuth Redirect URIs
1. Go to **Facebook Login** → **Settings**
2. **Valid OAuth Redirect URIs**:
   ```
   https://your-production-url.azurecontainerapps.io/auth/oauth/callback/facebook
   http://localhost:8888/auth/oauth/callback/facebook
   ```
3. Click **Save Changes**

### Step 4: Get App Credentials
1. Go to **Settings** → **Basic**
2. Copy **App ID** and **App Secret**

### Step 5: Store in Azure Key Vault
```bash
az keyvault secret set --vault-name mew-keyvault --name "FACEBOOK-CLIENT-ID" --value "YOUR_APP_ID"
az keyvault secret set --vault-name mew-keyvault --name "FACEBOOK-CLIENT-SECRET" --value "YOUR_APP_SECRET"
```

---

## Testing OAuth Integration

### Local Testing

1. Start the app:
```bash
./podman-start.sh
```

2. Visit the OAuth test page:
```
http://localhost:8888/auth/oauth/login
```

3. Test each provider by clicking the respective button

### Production Testing

1. Update your production environment variables:
```bash
./scripts/deploy-azure.sh
```

2. Visit:
```
https://your-app.azurecontainerapps.io/auth/oauth/login
```

---

## Environment Variables Summary

After setting up all providers, these environment variables will be loaded from Azure Key Vault:

```bash
# Google
GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET

# Microsoft
MICROSOFT_CLIENT_ID
MICROSOFT_CLIENT_SECRET

# Apple
APPLE_CLIENT_ID
APPLE_TEAM_ID
APPLE_KEY_ID
APPLE_PRIVATE_KEY

# Facebook
FACEBOOK_CLIENT_ID
FACEBOOK_CLIENT_SECRET
```

---

## Troubleshooting

### "redirect_uri_mismatch" Error
- Double-check redirect URIs match exactly in provider console
- Ensure you're using the correct protocol (http vs https)
- Check for trailing slashes

### Apple "invalid_client" Error
- Verify your Team ID, Key ID, and Client ID are correct
- Ensure private key (.p8) is valid and properly formatted
- Check that Key ID matches the key you downloaded

### "access_denied" Error
- User may have declined authorization
- Check OAuth scopes are correctly configured
- Verify app is not in sandbox/test mode blocking real users

### Database Errors
- Ensure database is running and migrations are applied
- Check that OAuthProvider table exists

---

## Security Best Practices

1. ⚠️ **Never commit secrets to git**
   - Use `.gitignore` for sensitive files
   - Store all secrets in Azure Key Vault

2. 🔒 **Use HTTPS in production**
   - OAuth providers require HTTPS
   - Azure Container Apps provides automatic HTTPS

3. 🔑 **Rotate secrets regularly**
   - Set expiration dates on client secrets
   - Regenerate and update before expiration

4. 📝 **Audit OAuth access**
   - Monitor failed login attempts
   - Log OAuth provider usage

5. 🛡️ **Validate redirect URIs**
   - Only whitelist your own domains
   - Never use wildcards in production

---

## Next Steps

Once OAuth is configured:
1. [Set up Siri Shortcuts](SIRI_SETUP.md) for voice commands
2. [Connect your calendar](GETTING_STARTED.md#calendar-integration)
3. [Configure mobile app](GETTING_STARTED.md#mobile-setup)

Need help? Check [GETTING_STARTED.md](GETTING_STARTED.md) or open an issue on GitHub.
