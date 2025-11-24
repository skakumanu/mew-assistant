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

## Apple OAuth Setup

1. Go to [Apple Developer](https://developer.apple.com/account/)
2. Create a new App ID or use existing
3. Enable "Sign in with Apple"
4. Create Service ID and configure return URLs
5. Generate private key

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
