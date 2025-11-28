# 🌐 View Your Calendar in Browser (Super Easy!)

## Option 1: Use the Calendar Viewer (Simplest!)

### On Your Computer or Phone:

1. **Download the viewer:**
   - Go to: https://github.com/skakumanu/mew-assistant/blob/feature/customerzerosetup/calendar-viewer.html
   - Click "Raw" button
   - Save as `calendar-viewer.html`

2. **Open the file in your browser:**
   - Just double-click the file
   - Or drag it into Chrome/Safari/Firefox

3. **Click "Sign in with Google"**

4. **Click "Show My Calendar"**

Done! You'll see all your events! 📅

---

## Option 2: Use Browser Console (For Developers)

### After Signing In:

1. **Sign in first:**
   - Go to: https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io
   - Click "Sign in with Google"
   - You'll see success page

2. **Open Developer Console:**
   - Press `F12` (or `Cmd+Option+J` on Mac)
   - Click "Console" tab

3. **Paste this code:**

```javascript
// Get your token (already saved from sign-in)
const token = localStorage.getItem('mew_token');

// Fetch your calendar events
fetch('https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/simple-calendar/events?max_results=10', {
    headers: {
        'Authorization': `Bearer ${token}`
    }
})
.then(res => res.json())
.then(data => {
    console.log('✅ Your Calendar Events:');
    data.events.forEach(event => {
        console.log(`📅 ${event.summary}`);
        console.log(`   Time: ${event.start}`);
        console.log(`   Location: ${event.location || 'None'}`);
        console.log('---');
    });
})
.catch(err => console.error('❌ Error:', err));
```

4. **Press Enter**

You'll see your calendar events in the console! 🎉

---

## Option 3: Use curl (Command Line)

### If you like terminal commands:

1. **Sign in and get your token** (do this in browser first)

2. **In terminal:**

```bash
# Replace YOUR_TOKEN with the token from localStorage
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/simple-calendar/events?max_results=10"
```

---

## What You'll See

```json
{
  "success": true,
  "count": 5,
  "events": [
    {
      "id": "abc123",
      "summary": "Team Meeting",
      "start": "2025-11-28T14:00:00-08:00",
      "end": "2025-11-28T15:00:00-08:00",
      "location": "Zoom",
      "description": "Weekly sync"
    }
  ]
}
```

---

## Troubleshooting

### "401 Unauthorized"
→ Your token expired. Sign in again!

### "Google account not connected"
→ You haven't signed in with Google yet

### "No events found"
→ Your calendar is empty, or events are in the past

### Can't see the token?
→ Open console (`F12`), type: `localStorage.getItem('mew_token')`

---

## 🎯 Recommended: Use the Calendar Viewer

**Why?**
- ✅ No coding needed
- ✅ Pretty interface
- ✅ Works on any device
- ✅ One-click sign in
- ✅ Auto-formats dates

**Just open `calendar-viewer.html` in your browser!**

---

## Need Help?

**Can't find your token?**
- Sign in again (takes 30 seconds)
- It auto-saves to your browser

**Events not showing?**
- Check you approved calendar permissions
- Try signing in again

**Still stuck?**
- Use the calendar-viewer.html file
- It handles everything automatically!
