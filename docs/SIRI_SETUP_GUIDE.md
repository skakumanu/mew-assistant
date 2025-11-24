# 🎤 Siri Integration Setup Guide for Mew Assistant

## Quick Setup for iPhone (3 Minutes)

### Method 1: Manual Shortcut Creation (Recommended)

Since Apple requires shortcuts to be manually created or shared via iCloud, follow these steps:

#### Step 1: Get Your API URL
Your Mew Assistant API: `https://mew-app-gyfre9f3gtgebjh9.eastus-01.azurewebsites.net`

#### Step 2: Create "Talk to Mew" Shortcut

1. **Open Shortcuts App** on your iPhone
2. **Tap "+" to create new shortcut**
3. **Add Actions** in this order:

   a. **Ask for Input**
   - Question: "What would you like to schedule?"
   - Input Type: Text
   
   b. **Get Contents of URL**
   - URL: `https://mew-app-gyfre9f3gtgebjh9.eastus-01.azurewebsites.net/voice/siri/intent`
   - Method: POST
   - Headers:
     - `Content-Type: application/json`
   - Request Body: JSON
     ```json
     {
       "text": "[Provided Input]",
       "user_id": "YOUR_USER_ID"
     }
     ```
   
   c. **Get Dictionary from Input**
   - Input: Contents of URL
   
   d. **Get Value for "response" from Dictionary**
   
   e. **Speak Text**
   - Text: Dictionary Value

4. **Name it**: "Talk to Mew"
5. **Add to Home Screen** (optional)
6. **Enable "Show in Share Sheet"**

#### Step 3: Get Your User ID

Run this command to get your user ID after logging in:

```bash
# Login first
TOKEN=$(curl -s -X POST https://mew-app-gyfre9f3gtgebjh9.eastus-01.azurewebsites.net/auth/federated/google \
  -H "Content-Type: application/json" \
  -d '{"token": "YOUR_GOOGLE_TOKEN"}' | jq -r '.access_token')

# Get your user info
curl -X GET https://mew-app-gyfre9f3gtgebjh9.eastus-01.azurewebsites.net/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

### Method 2: Direct URL Scheme (Simple Voice Commands)

Create these shortcuts for specific commands:

#### "Schedule with Mew"
```
Shortcut Actions:
1. Ask for Input: "What do you want to schedule?"
2. Open URL: mew://schedule?text=[Provided Input]
```

#### "Check My Schedule"
```
Shortcut Actions:
1. Open URL: mew://summary
2. Get Contents of URL: https://mew-app-gyfre9f3gtgebjh9.eastus-01.azurewebsites.net/mew/summary
3. Speak Text: [Contents]
```

## Common Siri Commands

Once set up, you can say:

- **"Hey Siri, Talk to Mew"**
  - Then: "Schedule dentist appointment for Tommy next Tuesday at 3pm"
  
- **"Hey Siri, Schedule with Mew"**
  - Siri will ask what to schedule
  
- **"Hey Siri, Check My Schedule"**
  - Get today's schedule summary

## Authentication Setup

### For Federated Login (Google/Microsoft):

1. **First Time Setup via Web**:
   - Go to: `https://mew-app-gyfre9f3gtgebjh9.eastus-01.azurewebsites.net/setup`
   - Click "Sign in with Google" or "Sign in with Microsoft"
   - Authorize calendar access
   - Copy your API Token

2. **Add Token to Shortcuts**:
   - Edit your shortcut
   - In the "Get Contents of URL" action
   - Add Header: `Authorization: Bearer YOUR_TOKEN`

## Advanced: Custom Siri Phrases

You can create shortcuts for specific phrases:

### "Add Therapy Session"
```json
{
  "text": "Schedule therapy session for [Ask Each Time] on [Ask Each Time]",
  "intent": "schedule",
  "category": "therapy"
}
```

### "What's Next Today"
```json
{
  "intent": "next_event"
}
```

### "Weekly Summary"
```json
{
  "intent": "summary",
  "period": "week"
}
```

## Troubleshooting

### "Siri says 'I can't help with that'"
- Make sure you've created the shortcut first
- Say the exact shortcut name: "Talk to Mew"

### "Request Failed"
- Check your internet connection
- Verify the API URL is correct
- Make sure your token hasn't expired

### "No Response"
- The API might be starting up (cold start)
- Wait 10 seconds and try again

## iOS Shortcuts Gallery Link

I'll create a shareable link for you. For now, follow the manual setup above.

**Want a video tutorial?** Let me know and I'll create one!

## Next Steps

1. ✅ Create "Talk to Mew" shortcut
2. ✅ Test with simple command: "Schedule test event tomorrow"
3. ✅ Add more specific shortcuts for common tasks
4. ✅ Share shortcuts with family members

---

**Need Help?** Open an issue on GitHub or contact support.
