# 🚀 Mew Assistant - Deployment Guide

**Status:** ✅ LIVE & RUNNING  
**Last Updated:** December 3, 2025  
**Branch:** feature/customerzerosetup

---

## 📍 Live Application URLs

### Main Application
- **Base URL:** https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io
- **API Docs:** https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/docs
- **Health Check:** https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/health

### OAuth Login
- **Login Page:** https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/auth/oauth/login
- **Calendar Viewer:** https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/calendar

---

## 🏗️ Azure Infrastructure

### Resources
- **Resource Group:** mew-assistant-dev-rg
- **Location:** West US 2
- **Container Registry:** mewassistantdevacr.azurecr.io
- **Container App:** mew-assistant-dev
- **Database:** PostgreSQL Flexible Server
- **Key Vault:** mew-assistant-kv-dev

### Scaling Configuration
- **Min Replicas:** 1
- **Max Replicas:** 3
- **Auto-scale:** Enabled based on HTTP requests

---

## ✅ Deployed Features

### 🔐 Authentication
- [x] Google OAuth2 (Working ✅)
- [x] Microsoft OAuth2 (Setup ready - see OAUTH_SETUP.md)
- [x] Apple Sign In (Code ready - needs credentials)
- [x] JWT tokens (30-day expiry)
- [x] Refresh token rotation
- [x] Role-Based Access Control (RBAC)

### 📅 Calendar Integration
- [x] Google Calendar read access
- [x] View upcoming events
- [x] Automatic token refresh
- [x] Browser-based calendar viewer

### 🛡️ Security
- [x] All secrets in Azure Key Vault
- [x] Managed identity for Key Vault access
- [x] HTTPS-only connections
- [x] Input validation & sanitization
- [x] Rate limiting

---

## 👥 Admin Accounts

| Email | Role | Provider | Status |
|-------|------|----------|--------|
| skakumanu@gmail.com | SUPERUSER | Google | ✅ Active |
| skakumanu@hotmail.com | ADMIN | Microsoft | ⏳ Pending OAuth setup |

---

## 🔧 Recent Fixes & Changes

### December 1, 2025 - Customer Zero Launch
- ✅ Fixed Google Calendar OAuth flow
- ✅ Fixed JWT token lookup bug (user ID vs email)
- ✅ Added auto-migration for OAuth tokens
- ✅ Fixed Calendar API 400 error (timeMin parameter)
- ✅ Enabled Google Calendar API in Cloud Console

### November 23, 2025 - Initial Deployment
- ✅ Deployed to Azure Container Apps
- ✅ PostgreSQL database provisioned
- ✅ OAuth providers configured
- ✅ Key Vault secrets stored

---

## 🧪 Testing

### Quick Health Check
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

### Test Google OAuth
1. Open: https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/auth/oauth/login
2. Click "Sign in with Google"
3. Verify redirect and token generation

---

## 📚 Related Documentation

- **OAuth Setup:** See `OAUTH_SETUP.md` for Microsoft and Apple configuration
- **User Guide:** See `USER_GUIDE.md` for end-user instructions
- **API Documentation:** Visit `/docs` endpoint for interactive API docs

---

## 🚀 Next Steps

1. **Setup Microsoft OAuth** - See `OAUTH_SETUP.md`
2. **Setup Apple Sign In** - See `OAUTH_SETUP.md`
3. **Deploy iOS Shortcuts** - See `SIRI_SETUP_GUIDE.md`
4. **Add calendar write permissions** - Currently read-only

---

## 📞 Support

**Deployment Issues:**
- Check container logs (command above)
- Verify Key Vault secrets are accessible
- Ensure managed identity has proper permissions

**OAuth Issues:**
- Verify redirect URIs match exactly
- Check provider credentials in Key Vault
- Ensure API scopes are properly configured

---

**GitHub Repository:** https://github.com/skakumanu/mew-assistant
