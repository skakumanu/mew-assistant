# iPhone Google Sign-In & Calendar Test Guide

## 🎯 Complete Flow (5 minutes total)

### Step 1: Sign In with Google (2 minutes)

1. **Open Safari on iPhone**
   
2. **Go to:**
   ```
   https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io
   ```

3. **Tap "🔐 Sign in with Google"**

4. **Sign in and approve permissions:**
   - ✅ Email
   - ✅ Profile
   - ✅ **View your Google Calendar** (NEW!)

5. **Copy Your Token**
   - Success page shows your JWT token
   - Tap and hold to select
   - Copy the entire token (starts with "eyJ...")
   - Paste in Notes app for later

---

## Step 2: Test Calendar Access (3 minutes)

### Option A: Quick Test in Safari

Open this URL in Safari (paste your token after Bearer):
```
https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/simple-calendar/events?max_results=5
```

**Problem:** Safari can't easily set Authorization header 😞

### Option B: Use iPhone Shortcuts App (RECOMMENDED) ✅

#### Create "My Calendar Events" Shortcut:

1. **Open Shortcuts app**

2. **Create new shortcut** (tap +)

3. **Add these 3 actions:**

   **🔹 Action 1: Text**
   - Add a Text action
   - Paste your JWT token here (the one from Step 1)
   - Or keep it empty to be asked each time

   **🔹 Action 2: Get Contents of URL**
   - URL: `https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/simple-calendar/events?max_results=10`
   - Method: **GET**
   - Headers: **Add Header**
     - Key: `Authorization`
     - Value: `Bearer [Text from Action 1]`
   
   **🔹 Action 3: Show Result**
   - Show: [Contents of URL output]
   - Format: **JSON** (optional - makes it prettier)

4. **Name your shortcut** "My Calendar Events"

5. **Run it!** 🎉

---

## 📱 What You'll See

### Success Response:
```json
{
  "success": true,
  "count": 5,
  "events": [
    {
      "id": "abc123",
      "summary": "Team Meeting",
      "start": "2025-11-28T10:00:00-08:00",
      "end": "2025-11-28T11:00:00-08:00",
      "description": "Weekly sync",
      "location": "Zoom",
      "link": "https://calendar.google.com/..."
    }
  ]
}
```

### If Token Expired:
```json
{
  "detail": "Google token expired. Please sign in again."
}
```
**Solution:** Just go back to Step 1 and sign in again!

---

## 🎬 Complete Example Shortcut

**Name:** "Show My Calendar"

**Actions:**
1. **Ask for Input**
   - Question: "Paste your Mew token (or leave empty if saved)"
   - Input Type: Text
   - Default: (your saved token)

2. **Get Contents of URL**
   - URL: `https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/simple-calendar/events?max_results=20`
   - Method: GET
   - Headers:
     - Authorization: `Bearer [Provided Input]`

3. **Get Dictionary from Input**
   - Input: [Contents of URL]

4. **Get Value for Key**
   - Key: `events`
   - Dictionary: [Dictionary]

5. **Repeat with Each** item in [events]
   - **Get Dictionary Value** for `summary`
   - **Get Dictionary Value** for `start`
   - **Text:** "[summary] at [start]"
   - **Add to Variable** "eventList"

6. **Show Result**
   - Show combined text of all events

---

## 🚀 Even Simpler: Voice Command

Add Siri trigger to your shortcut:
1. Tap shortcut name
2. Add to Siri
3. Say: **"Show my calendar"**

Now just say "Hey Siri, show my calendar" and you're done! 🎤

---

## 🔧 API Endpoint Details

### Get Calendar Events

**Endpoint:**
```
GET /simple-calendar/events
```

**Parameters:**
- `max_results` (optional): Number of events (default: 10, max: 100)

**Headers:**
```
Authorization: Bearer YOUR_MEW_JWT_TOKEN
```

**Example:**
```bash
curl -H "Authorization: Bearer eyJ..." \
  "https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/simple-calendar/events?max_results=5"
```

---

## ✅ What's Working Now

1. ✅ Sign in with Google from iPhone
2. ✅ Request Calendar permission
3. ✅ Store Google OAuth tokens securely
4. ✅ Get JWT token for Mew API
5. ✅ Fetch calendar events with JWT token
6. ✅ Simple JSON response

## 🎯 Benefits

- **One token:** Just use your Mew JWT token
- **No complex OAuth:** We handle Google tokens for you
- **Works everywhere:** iPhone, iPad, Mac, any device
- **Secure:** Tokens stored in database, not exposed

---

## 🆘 Troubleshooting

### "Google account not connected"
→ Sign in with Google first (Step 1)

### "No Google access token"  
→ Sign in again (maybe you signed in before calendar scope was added)

### "Token expired"
→ Sign in again to refresh

### "Invalid token"
→ Make sure you copied the entire JWT token (it's long!)

---

## 📞 Need Help?

The token is valid for 30 days. After that, just sign in again!
