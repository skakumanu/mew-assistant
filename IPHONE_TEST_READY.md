# ✅ iPhone OAuth & Calendar - Ready to Test!

## 🚀 What's Live Now

**Production URL:** https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io

### ✅ Working Features:
1. **Google Sign-In** from iPhone Safari
2. **Calendar Permission** - users grant calendar access during sign-in
3. **Token Storage** - Google OAuth tokens saved securely
4. **Calendar API** - fetch events with simple endpoint

---

## 📱 Quick Test on iPhone (2 minutes)

### 1. Sign In
- Open Safari
- Go to: https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io
- Tap "Sign in with Google"
- Approve calendar permission
- **Copy the JWT token shown**

### 2. Get Your Calendar Events

**Create this Shortcut:**

**Shortcut Name:** "My Calendar"

**Actions:**
1. **Text** → Paste your JWT token
2. **Get Contents of URL**
   - URL: `https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/simple-calendar/events?max_results=10`
   - Method: GET
   - Headers: `Authorization: Bearer [Text]`
3. **Show Result**

**Run it** → You'll see your calendar events! 🎉

---

## 📖 Full Guide

See **IPHONE_OAUTH_TEST.md** for:
- Detailed shortcut instructions
- Siri integration
- Troubleshooting
- API documentation

---

## 🔑 Key Endpoints

### Sign In
```
GET /auth/simple/google
```
Redirects to Google OAuth → Returns JWT token

### Get Calendar Events
```
GET /simple-calendar/events?max_results=10
Authorization: Bearer YOUR_JWT_TOKEN
```

Returns:
```json
{
  "success": true,
  "count": 5,
  "events": [
    {
      "summary": "Team Meeting",
      "start": "2025-11-28T10:00:00-08:00",
      "end": "2025-11-28T11:00:00-08:00",
      "location": "Zoom"
    }
  ]
}
```

---

## 🎯 Simple = Better

- ✅ **One token** for everything (JWT)
- ✅ **No OAuth complexity** for users
- ✅ **Works on any device** (iPhone, Android, web)
- ✅ **Secure** (tokens in database, not exposed)

---

## 🔒 What Happens Behind the Scenes

1. User signs in → Google OAuth flow
2. We get Google access_token + refresh_token
3. Store tokens in database (linked to user)
4. Return JWT token to user
5. User uses JWT for all API calls
6. We use stored Google token to fetch calendar

**User only needs to remember one token!**

---

## 🧪 Test Checklist

- [ ] Sign in with Google on iPhone
- [ ] See calendar permission request
- [ ] Get JWT token
- [ ] Create iPhone Shortcut
- [ ] Fetch calendar events successfully
- [ ] Add Siri trigger (optional)
- [ ] Test token expiration (sign in again)

---

## 🆘 Common Issues

**"Google account not connected"**
→ Sign in first

**"No Google access token"**  
→ You signed in before calendar scope was added - sign in again

**"Token expired"**
→ Just sign in again (takes 30 seconds)

---

## 📊 Status

**Deployment:** ✅ Live in production  
**Sign-In:** ✅ Working  
**Calendar Scope:** ✅ Added  
**Token Storage:** ✅ Working  
**Calendar API:** ✅ Working  
**iPhone Compatible:** ✅ Yes  
**Documentation:** ✅ Complete  

**Ready for testing!** 🎉
