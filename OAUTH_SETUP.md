# 🔐 OAuth Providers Setup Guide

**Last Updated:** December 3, 2025  
**Status:** Google ✅ | Microsoft ⏳ | Apple ⏳

---

## 📊 Current Status

| Provider | Status | Account | Notes |
|----------|--------|---------|-------|
| Google | ✅ Working | skakumanu@gmail.com | Fully functional |
| Microsoft | ⏳ Ready | skakumanu@hotmail.com | Needs Azure AD setup |
| Apple | ⏳ Ready | N/A | Needs Apple Developer setup |

---

## ✅ Google OAuth (COMPLETE)

### Configuration
- **Client ID:** Stored in Key Vault
- **Client Secret:** Stored in Key Vault
- **Redirect URI:** `https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/auth/oauth/callback/google`
- **Scopes:** openid, email, profile, calendar (read-only)

### Setup Location
- Google Cloud Console: https://console.cloud.google.com/
- Project: Your GCP project
- Credentials configured ✅
- Calendar API enabled ✅

### Test URL
https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/auth/oauth/login

---

## 🔷 Microsoft OAuth Setup

### Step 1: Register App in Azure Portal (5 mins)

1. **Go to Azure Portal**
   - Visit: https://portal.azure.com
   - Navigate to **Microsoft Entra ID** (formerly Azure Active Directory)

2. **Create App Registration**
   - Click **App registrations** → **+ New registration**
   - **Name:** `Mew Assistant - Production`
   - **Account types:** "Accounts in any organizational directory (Multitenant) and personal Microsoft accounts"
   - **Redirect URI:**
     - Platform: **Web**
     - URI: `https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/auth/oauth/callback/microsoft`
   - Click **Register**

3. **Copy Application (client) ID**
   - This is your `MICROSOFT_CLIENT_ID`

### Step 2: Create Client Secret (2 mins)

1. **Navigate to Certificates & secrets**
   - Click **+ New client secret**
   - **Description:** `Mew Assistant Production`
   - **Expires:** 24 months
   - Click **Add**

2. **Copy Secret Value**
   - ⚠️ Copy the **Value** immediately (shown only once!)
   - This is your `MICROSOFT_CLIENT_SECRET`

### Step 3: Configure API Permissions (2 mins)

1. **Click API permissions**
2. **Add a permission** → **Microsoft Graph** → **Delegated permissions**
3. **Add these permissions:**
   - User.Read (already added)
   - openid
   - email
   - profile
4. Click **Add permissions**

### Step 4: Deploy to Azure (1 min)

Run the automated setup script:

```bash
cd /home/srinu/mew-assistant
export MICROSOFT_CLIENT_ID='your-client-id'
export MICROSOFT_CLIENT_SECRET='your-secret-value'
./scripts/setup-microsoft-oauth.sh
```

The script will:
- Store secrets in Key Vault
- Link secrets to Container App
- Update environment variables
- Restart the app

### Step 5: Test (1 min)

1. Open: https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/auth/oauth/login
2. Click "Sign in with Microsoft"
3. Sign in with: `skakumanu@hotmail.com`
4. Grant permissions
5. Verify success ✅

---

## 🍎 Apple Sign In Setup

### Prerequisites
- Apple Developer Account ($99/year)
- Bundle ID for your app

### Step 1: Configure App ID (5 mins)

1. **Go to Apple Developer Portal**
   - Visit: https://developer.apple.com/account/resources/identifiers/list
   
2. **Create App ID**
   - Click **+** to add new identifier
   - Select **App IDs** → Continue
   - **Description:** `Mew Assistant`
   - **Bundle ID:** `com.mewassistant.app` (explicit)
   - **Capabilities:** Check "Sign in with Apple"
   - Click **Continue** → **Register**

### Step 2: Create Services ID (5 mins)

1. **Create Services ID**
   - Click **+** again
   - Select **Services IDs** → Continue
   - **Description:** `Mew Assistant Web`
   - **Identifier:** `com.mewassistant.web`
   - Click **Continue** → **Register**

2. **Configure Services ID**
   - Click on your Services ID
   - Check **"Sign in with Apple"**
   - Click **Configure**
   - **Primary App ID:** Select your App ID created above
   - **Domains and Subdomains:** `mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io`
   - **Return URLs:** `https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/auth/oauth/callback/apple`
   - Click **Save** → **Continue** → **Register**

### Step 3: Create Private Key (5 mins)

1. **Go to Keys section**
   - Visit: https://developer.apple.com/account/resources/authkeys/list
   - Click **+** to create new key

2. **Configure Key**
   - **Key Name:** `Mew Assistant Sign In`
   - Check **"Sign in with Apple"**
   - Click **Configure** → Select your Primary App ID
   - Click **Save** → **Continue** → **Register**

3. **Download Key**
   - Click **Download** (only shown once!)
   - Save the `.p8` file securely
   - Note the **Key ID** (shown on the page)

### Step 4: Deploy to Azure (5 mins)

Prepare your credentials:

```bash
export APPLE_CLIENT_ID='com.mewassistant.web'  # Your Services ID
export APPLE_TEAM_ID='YOUR_TEAM_ID'  # Found in top-right of Apple Developer Portal
export APPLE_KEY_ID='YOUR_KEY_ID'  # From Step 3
# Do NOT paste your private key directly into the repository or docs.
# Store the .p8 file securely and set the environment variable from the file:
# Note: Do NOT paste your private key into files or the repository.
# Save the downloaded `.p8` file securely and load it into your environment or Key Vault.
# Example (local, only for initial testing):
# export APPLE_PRIVATE_KEY="[REDACTED_PRIVATE_KEY_CONTENT]"  # DO NOT COMMIT THIS  load from secure storage or Key Vault
```

Store in Key Vault:

```bash
az keyvault secret set --vault-name mew-assistant-kv-dev --name APPLE-CLIENT-ID --value "$APPLE_CLIENT_ID"
az keyvault secret set --vault-name mew-assistant-kv-dev --name APPLE-TEAM-ID --value "$APPLE_TEAM_ID"
az keyvault secret set --vault-name mew-assistant-kv-dev --name APPLE-KEY-ID --value "$APPLE_KEY_ID"
az keyvault secret set --vault-name mew-assistant-kv-dev --name APPLE-PRIVATE-KEY --value "[REDACTED_PRIVATE_KEY_CONTENT]"  # use secure secret value source
```

Update Container App:

```bash
# Get subscription and identity
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
IDENTITY_ID="/subscriptions/${SUBSCRIPTION_ID}/resourcegroups/mew-assistant-dev-rg/providers/Microsoft.ManagedIdentity/userAssignedIdentities/mew-assistant-dev-identity"

# Link secrets
az containerapp secret set \
  --name mew-assistant-dev \
  --resource-group mew-assistant-dev-rg \
  --secrets \
    apple-client-id=keyvaultref:https://mew-assistant-kv-dev.vault.azure.net/secrets/APPLE-CLIENT-ID,identityref:${IDENTITY_ID} \
    apple-team-id=keyvaultref:https://mew-assistant-kv-dev.vault.azure.net/secrets/APPLE-TEAM-ID,identityref:${IDENTITY_ID} \
    apple-key-id=keyvaultref:https://mew-assistant-kv-dev.vault.azure.net/secrets/APPLE-KEY-ID,identityref:${IDENTITY_ID} \
    apple-private-key=keyvaultref:https://mew-assistant-kv-dev.vault.azure.net/secrets/APPLE-PRIVATE-KEY,identityref:${IDENTITY_ID}

# Update environment variables
az containerapp update \
  --name mew-assistant-dev \
  --resource-group mew-assistant-dev-rg \
  --set-env-vars \
    APPLE_CLIENT_ID=secretref:apple-client-id \
    APPLE_TEAM_ID=secretref:apple-team-id \
    APPLE_KEY_ID=secretref:apple-key-id \
    APPLE_PRIVATE_KEY=secretref:apple-private-key
```

### Step 5: Test (1 min)

1. Open: https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/auth/oauth/login
2. Click "Sign in with Apple"
3. Sign in with your Apple ID
4. Verify success ✅

---

## 🔍 Troubleshooting

### Common Issues

**"redirect_uri_mismatch" error**
- Verify redirect URI matches exactly (no trailing slash)
- Check provider console settings
- Must use correct provider path (/google, /microsoft, /apple)

**"Invalid credentials" error**
- Secrets may not have loaded from Key Vault
- Restart container app
- Check Key Vault access permissions

**"Access denied" error**
- For Google: Add test user in OAuth consent screen
- For Microsoft: Grant admin consent for permissions
- For Apple: Verify Services ID is properly configured

### Check Container Logs
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

---

## 📚 Resources

### Google OAuth
- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Google Cloud Console](https://console.cloud.google.com/)

### Microsoft OAuth
- [Microsoft identity platform documentation](https://learn.microsoft.com/en-us/azure/active-directory/develop/)
- [Azure Portal](https://portal.azure.com)

### Apple Sign In
- [Sign in with Apple Documentation](https://developer.apple.com/sign-in-with-apple/)
- [Apple Developer Portal](https://developer.apple.com/account/)

---

## ✅ Success Checklist

After setup, verify:
- [ ] Login button appears on OAuth page
- [ ] Clicking button redirects to provider
- [ ] After sign-in, redirects back successfully
- [ ] User profile displays correctly
- [ ] JWT token is generated
- [ ] Can access protected endpoints

