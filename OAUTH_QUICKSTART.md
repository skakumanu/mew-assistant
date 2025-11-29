# 🔧 Google OAuth Setup - Fix "Error 403: access_denied"

## Problem
Google OAuth app is in "Testing" mode and needs test users added.

## Quick Fix (5 minutes)

### Step 1: Go to Google Cloud Console

**Open:** https://console.cloud.google.com/apis/credentials

**Make sure you're in the right project** (the one with your OAuth credentials)

---

### Step 2: Add Test Users

1. **Click on "OAuth consent screen"** (left sidebar)

2. **Scroll down to "Test users"** section

3. **Click "+ ADD USERS"**

4. **Add your email addresses:**
   - Your Gmail address
   - Any other email you want to test with
   - One email per line

5. **Click "SAVE"**

---

### Step 3: Test Again

Now go back to:
https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io

Click "Sign in with Google" → Should work now! ✅

---

## Alternative: Publish Your App (Takes Longer)

If you want ANYONE to be able to sign in (not just test users):

### Option A: Quick Publish (Good for Now)

1. **Go to:** https://console.cloud.google.com/apis/credentials/consent
2. **Click "PUBLISH APP"** button (top right)
3. **Confirm:** "Make app public"
4. **Status changes to:** "In Production"

**Warning:** Google might require verification if you request sensitive scopes. For calendar.readonly, usually fine!

### Option B: Full Verification (Needed Later)

When you're ready for public launch:
1. Go through Google's verification process
2. Provide privacy policy, terms of service
3. Explain why you need calendar access
4. Wait 3-7 days for approval

---

## What's Happening?

Your OAuth app has 3 states:

1. **Testing** (← You are here)
   - Only works for test users
   - Up to 100 test users
   - Perfect for development

2. **In Production (Unverified)**
   - Anyone can sign in
   - Shows "unverified" warning
   - Good for beta/early users

3. **In Production (Verified)**
   - Anyone can sign in
   - No warnings
   - Requires Google approval

---

## Recommended for Customer Zero Testing

### For Now: Add Test Users
- **Fast:** Takes 2 minutes
- **Safe:** Only your testers can access
- **Perfect for:** Initial testing

**Steps:**
1. Add 5-10 test user emails
2. Share the link with them
3. They can sign in immediately

### Later: Publish App
- When you have 10+ happy testers
- Click "Publish App"
- Anyone can sign in
- May show "unverified" warning (that's OK!)

---

## Quick Reference

**Add test users here:**
https://console.cloud.google.com/apis/credentials/consent

**Current OAuth redirect URL (should be configured):**
```
https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/auth/simple/google/callback
```

**Scopes you're requesting:**
- `openid` - Basic authentication
- `email` - User's email address
- `profile` - User's name and photo
- `https://www.googleapis.com/auth/calendar.readonly` - Read calendar

---

## Troubleshooting

### Still getting 403 after adding test user?
- Make sure you added the EXACT email address
- Wait 1-2 minutes for Google to sync
- Try in incognito/private window
- Make sure you're signed in with that Google account

### Want to add more than 100 test users?
- You need to publish the app (move to Production)

### Error says "redirect_uri_mismatch"?
- Go to Credentials → OAuth 2.0 Client IDs
- Click your client ID
- Add this to "Authorized redirect URIs":
  ```
  https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/auth/simple/google/callback
  ```

---

## Next Steps

1. **Add yourself as test user** (takes 2 min)
2. **Test the sign-in flow** (works now!)
3. **Add your customer zero testers** (5-10 people)
4. **After successful testing → Publish app** (1 click)

---

## Environment Variables Check

Make sure these are set in Azure Container App:

```bash
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-secret
BASE_URL=https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io
```

**Check in Azure Portal:**
Settings → Environment variables

---

**Quick fix:** Add your email as test user, then try again!

**Link:** https://console.cloud.google.com/apis/credentials/consent
