# Federated Authentication Setup Guide

## Overview
Mew Assistant now supports OAuth 2.0 federated authentication with Google, Microsoft, and Apple accounts.

## Current Status
✅ **Deployed to Azure**: https://mew-app-gyfre9f3gtgebjh9.eastus-01.azurewebsites.net
✅ **Container Image Built**: Latest code pushed to Azure Container Registry
✅ **OAuth Endpoints Ready**: All federated auth routes configured

## Testing the OAuth Flow

### Option 1: Using the Test HTML Page
1. Open `oauth-test.html` in your browser
2. Click on any OAuth provider button
3. Complete the OAuth flow
4. Your token will be displayed and stored

### Option 2: Manual Testing via cURL

**Step 1: Get Authorization URL**
```bash
curl -s https://mew-app-gyfre9f3gtgebjh9.eastus-01.azurewebsites.net/auth/federated/google/authorize | jq
```

**Step 2: Visit the URL in your browser and authorize**

**Step 3: Copy the code from redirect URL and exchange it:**
```bash
curl -X POST https://mew-app-gyfre9f3gtgebjh9.eastus-01.azurewebsites.net/auth/federated/google/callback \
  -H "Content-Type: application/json" \
  -d '{"code": "YOUR_CODE_HERE"}' | jq
```

**Step 4: Use the token:**
```bash
TOKEN="your_token_here"
curl -H "Authorization: Bearer $TOKEN" \
  https://mew-app-gyfre9f3gtgebjh9.eastus-01.azurewebsites.net/auth/me | jq
```

## Required OAuth Credentials

To use federated authentication, you need to configure these environment variables in Azure:

### Google OAuth
- `GOOGLE_CLIENT_ID`: Your Google OAuth client ID
- `GOOGLE_CLIENT_SECRET`: Your Google OAuth client secret
- Redirect URI: `https://mew-app-gyfre9f3gtgebjh9.eastus-01.azurewebsites.net/auth/federated/google/callback`

### Microsoft OAuth
- `MICROSOFT_CLIENT_ID`: Your Azure AD app client ID
- `MICROSOFT_CLIENT_SECRET`: Your Azure AD app client secret
- Redirect URI: `https://mew-app-gyfre9f3gtgebjh9.eastus-01.azurewebsites.net/auth/federated/microsoft/callback`

### Apple OAuth
- `APPLE_CLIENT_ID`: Your Apple Service ID
- `APPLE_TEAM_ID`: Your Apple Team ID
- `APPLE_KEY_ID`: Your Apple Key ID
- `APPLE_PRIVATE_KEY`: Your Apple private key (PEM format)
- Redirect URI: `https://mew-app-gyfre9f3gtgebjh9.eastus-01.azurewebsites.net/auth/federated/apple/callback`

## Setting Up OAuth Providers

### Google Cloud Console
1. Go to https://console.cloud.google.com/
2. Create a new project or select existing
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URI
6. Copy client ID and secret to Azure Key Vault

### Microsoft Azure Portal
1. Go to https://portal.azure.com/
2. Navigate to Azure Active Directory > App registrations
3. Create new registration
4. Add redirect URI
5. Create client secret
6. Copy application (client) ID and secret to Azure Key Vault

### Apple Developer Portal
1. Go to https://developer.apple.com/
2. Create a Service ID
3. Configure Sign in with Apple
4. Create a private key
5. Add all credentials to Azure Key Vault

## Updating Azure Configuration

```bash
# Set OAuth credentials in Azure Key Vault
az keyvault secret set --vault-name mew-assistant-dev-kv \
  --name google-client-id --value "YOUR_GOOGLE_CLIENT_ID"

az keyvault secret set --vault-name mew-assistant-dev-kv \
  --name google-client-secret --value "YOUR_GOOGLE_CLIENT_SECRET"

# Repeat for Microsoft and Apple credentials
```

## Your Admin Accounts

### Superuser (God Rights)
- Email: skakumanu@gmail.com
- Provider: Google OAuth
- Role: superuser
- Permissions: Full system access

### Admin User
- Email: skakumanu@hotmail.com
- Provider: Microsoft OAuth
- Role: admin
- Permissions: Administrative access

## iPhone Siri Integration

See `SIRI_SETUP_GUIDE.md` for complete instructions on setting up Siri Shortcuts with OAuth.

## Next Steps

1. **Configure OAuth Providers**: Set up credentials in Google, Microsoft, and Apple developer consoles
2. **Update Azure Secrets**: Add all OAuth credentials to Azure Key Vault
3. **Test OAuth Flow**: Use the test page or cURL commands
4. **Set up Siri**: Follow the Siri setup guide
5. **Add Calendar Integration**: Connect Google/Apple calendars

## Support

For issues or questions, check the logs:
```bash
az containerapp logs show --name mew-app --resource-group mew-assistant-dev-rg
```
