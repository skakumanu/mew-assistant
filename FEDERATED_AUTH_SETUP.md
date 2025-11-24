# Federated Authentication Setup Guide

## ✅ Completed Steps (2025-11-24)

1. **Azure Key Vault Configuration**
   - ✅ Stored Google OAuth Client ID in Key Vault
   - ✅ Stored Google OAuth Client Secret in Key Vault
   - ✅ Enabled system-assigned managed identity on Container App
   - ✅ Granted Key Vault access to Container App identity

2. **Container App Configuration**
   - ✅ OAuth secrets linked from Key Vault  
   - ✅ Environment variables configured
   - ✅ Redirect URI configured: `https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/auth/oauth/callback`

## 🚀 Your App URLs

- **OAuth Login Page**: https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/auth/oauth/login
- **API Documentation**: https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/docs
- **Health Check**: https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/health

## 🔧 REQUIRED: Update Google Cloud Console

Before OAuth will work, you MUST add the redirect URI to your Google OAuth client:

### Step-by-Step Instructions

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/
   - Select your project

2. **Navigate to OAuth Settings**
   - Go to **APIs & Services** → **Credentials**
   - Find client ID: `321461422476-sgt4knrr7movtjk2djdpt5bom4q90qfk.apps.googleusercontent.com`

3. **Add Redirect URI**
   - Click **Edit** on your OAuth 2.0 Client
   - Under **Authorized redirect URIs**, add:
   ```
   https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/auth/oauth/callback
   ```
   - Click **Save**

4. **Test OAuth Login**
   - Open: https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/auth/oauth/login
   - Click "Sign in with Google"
   - Complete the sign-in process

## 📱 Using from iPhone

### Browser Method (Simplest)
1. Open Safari on your iPhone
2. Go to: https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/auth/oauth/login
3. Tap "Sign in with Google"
4. Authorize the app
5. You'll receive your auth token

### Siri Shortcut (After OAuth is Working)
We'll create an iOS Shortcut once OAuth is confirmed working.

## 🔍 Troubleshooting

### Check if App is Running
```bash
curl https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/health
```

### View Container Logs
```bash
az containerapp logs show \
  --name mew-assistant-dev \
  --resource-group mew-assistant-dev-rg \
  --tail 100 \
  --follow
```

### Verify Environment Variables
```bash
az containerapp show \
  --name mew-assistant-dev \
  --resource-group mew-assistant-dev-rg \
  --query "properties.template.containers[0].env" \
  --output table
```

### Common Issues

**"redirect_uri_mismatch" error**
- The redirect URI in Google Console doesn't match exactly
- Make sure it's: `https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/auth/oauth/callback`
- No trailing slash, exact match required

**"Not Found" error**
- Container App may still be deploying
- Wait 1-2 minutes and try again
- Check logs with command above

**"Invalid credentials" error**  
- Secrets may not have loaded from Key Vault
- Restart the container app:
```bash
az containerapp revision restart \
  --name mew-assistant-dev \
  --resource-group mew-assistant-dev-rg
```

## 📋 Next Steps

After Google OAuth is working:

1. **Set up Microsoft OAuth**
   - Create app in Azure AD / Microsoft Entra
   - Add client ID/secret to Key Vault
   - Update container app configuration

2. **Set up Apple Sign In**
   - Register with Apple Developer
   - Configure App ID and Services ID
   - Add credentials to Key Vault

3. **Create iOS Shortcuts**
   - Build Siri voice commands
   - Generate QR codes for easy installation
   - Test "Hey Siri, check my Mew schedule"

4. **Configure Google Calendar Access**
   - Enable Google Calendar API
   - Request calendar scopes during OAuth
   - Sync events with Mew Assistant

## 🔐 Security Notes

- ✅ All OAuth secrets stored in Azure Key Vault (never in code)
- ✅ Container App uses managed identity for Key Vault access
- ✅ All traffic encrypted with HTTPS
- ✅ JWT tokens expire after configured duration
- ✅ Refresh tokens rotated on each use

## 📞 Get Help

If you need assistance:
1. Check the troubleshooting section above
2. Review container logs for error messages
3. Verify Google Cloud Console settings match exactly
4. Ensure OAuth client is enabled and active

## 📚 Additional Resources

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Azure Key Vault Best Practices](https://learn.microsoft.com/en-us/azure/key-vault/general/best-practices)
- [Azure Container Apps Documentation](https://learn.microsoft.com/en-us/azure/container-apps/)
