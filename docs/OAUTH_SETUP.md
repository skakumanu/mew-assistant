# OAuth Provider Setup Guide

## Overview

Mew Assistant supports OAuth login with Google, Microsoft, Apple, and Facebook. To enable these, you need to register applications with each provider.

## Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google+ API
4. Go to "Credentials" → "Create Credentials" → "OAuth client ID"
5. Configure consent screen
6. Set authorized redirect URIs:
   - `https://your-app-url.azurewebsites.net/auth/oauth/callback/google`
   - `http://localhost:8888/auth/oauth/callback/google` (for local testing)
7. Copy **Client ID** and **Client Secret**

### Add to Azure Key Vault:
```bash
az keyvault secret set --vault-name mew-keyvault --name "GOOGLE-CLIENT-ID" --value "your-client-id"
az keyvault secret set --vault-name mew-keyvault --name "GOOGLE-CLIENT-SECRET" --value "your-client-secret"
```

## Microsoft OAuth Setup

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to "App registrations" → "New registration"
3. Set redirect URIs (same pattern as Google)
4. Under "Certificates & secrets", create new client secret
5. Copy **Application (client) ID** and **Client Secret**

### Add to Azure Key Vault:
```bash
az keyvault secret set --vault-name mew-keyvault --name "MICROSOFT-CLIENT-ID" --value "your-client-id"
az keyvault secret set --vault-name mew-keyvault --name "MICROSOFT-CLIENT-SECRET" --value "your-client-secret"
```

## Apple OAuth Setup (Sign in with Apple)

Apple OAuth uses a different flow than Google/Microsoft. Here's the detailed setup:

### Step 1: Apple Developer Account Setup

1. Go to [Apple Developer](https://developer.apple.com/account/)
2. Navigate to **Certificates, Identifiers & Profiles**

### Step 2: Create App ID

1. Go to **Identifiers** → Click **+** → Select **App IDs**
2. Select **App** → Continue
3. Fill in:
   - Description: `Mew Assistant`
   - Bundle ID: `com.mewassistant.app` (or your domain)
4. Enable **Sign in with Apple** capability
5. Click **Continue** → **Register**

### Step 3: Create Services ID

1. Go to **Identifiers** → Click **+** → Select **Services IDs**
2. Fill in:
   - Description: `Mew Assistant Web`
   - Identifier: `com.mewassistant.service`
3. Enable **Sign in with Apple**
4. Click **Configure** next to Sign in with Apple:
   - **Primary App ID**: Select the App ID created above
   - **Web Domain**: Your production domain (e.g., `mew-assistant-dev.azurecontainerapps.io`)
   - **Return URLs**: 
     - `https://mew-assistant-dev.azurecontainerapps.io/auth/oauth/callback/apple`
     - `http://localhost:8888/auth/oauth/callback/apple` (for testing)
5. Click **Save** → **Continue** → **Register**

### Step 4: Create Private Key

1. Go to **Keys** → Click **+**
2. Fill in:
   - Key Name: `Mew Assistant Sign in with Apple Key`
3. Enable **Sign in with Apple**
4. Click **Configure** → Select your Primary App ID
5. Click **Save** → **Continue** → **Register**
6. **Download the .p8 key file** (you can only download this once!)
7. Note the **Key ID** shown on the page

### Step 5: Get Your Team ID

1. Go to **Membership** in the left sidebar
2. Copy your **Team ID** (10-character string)

### Step 6: Add to Azure Key Vault

```bash
# Service ID (Client ID)
az keyvault secret set --vault-name mew-keyvault --name "APPLE-CLIENT-ID" --value "com.mewassistant.service"

# Team ID
az keyvault secret set --vault-name mew-keyvault --name "APPLE-TEAM-ID" --value "YOUR_TEAM_ID"

# Key ID
az keyvault secret set --vault-name mew-keyvault --name "APPLE-KEY-ID" --value "YOUR_KEY_ID"

# Private Key (upload the .p8 file content)
az keyvault secret set --vault-name mew-keyvault --name "APPLE-PRIVATE-KEY" --file "path/to/AuthKey_KEYID.p8"
```

### Important Apple OAuth Notes

- Apple OAuth requires JWT-based authentication (not client secret)
- The private key (.p8 file) must be kept secure
- Apple requires HTTPS for production (HTTP only allowed for localhost)
- User email may be provided only on first sign-in
- Apple supports "Hide My Email" feature - handle both real and proxy emails

## Test OAuth Locally

Once configured, test with:

```bash
# Visit the OAuth test page
http://localhost:8888/auth/oauth/login

# Or use the HTML test file
open oauth-test.html
```

## Environment Variables Needed

```bash
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
MICROSOFT_CLIENT_ID=your-microsoft-client-id
MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret
APPLE_CLIENT_ID=your-apple-client-id
APPLE_TEAM_ID=your-apple-team-id
APPLE_KEY_ID=your-apple-key-id
APPLE_PRIVATE_KEY=path-to-private-key
```

## Current Status

⚠️ **Note**: OAuth providers are not yet fully configured with credentials. The endpoints are ready but require provider registration to work.

To use the app now, please use **email/password registration** at `/auth/register`.
