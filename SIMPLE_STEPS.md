# ⚡ SUPER SIMPLE - View Your Calendar

## Just 2 Steps!

### Step 1: Sign In (30 seconds)

**On your phone or computer, open:**
https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io

**Tap:** "Sign in with Google"

**Approve:** Calendar permission

✅ Done! You're connected.

---

### Step 2: View Your Calendar

**Option A: Browser Console (Fastest!)**

1. After signing in, press `F12` (or right-click → Inspect)
2. Click "Console" tab
3. Paste this and press Enter:

```javascript
fetch('https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/simple-calendar/events?max_results=20', {
    headers: { 'Authorization': 'Bearer ' + localStorage.getItem('mew_token') }
})
.then(r => r.json())
.then(d => {
    console.log(`\n📅 YOUR CALENDAR (${d.count} events):\n`);
    d.events.forEach(e => console.log(`• ${e.summary}\n  ${new Date(e.start).toLocaleString()}\n`));
});
```

**You'll see your calendar right there!** 🎉

---

**Option B: Download Viewer (Pretty UI)**

After signing in, the success page has a button:
**"Download Calendar Viewer"**

Click it → Open the file → Your calendar shows automatically!

---

## That's It!

- ✅ Sign in once
- ✅ See your calendar
- ✅ Works for 30 days

**No apps to install. No coding needed.**

---

## Troubleshooting

**Don't see your events?**
→ Make sure you approved "View your Google Calendar" permission

**Token expired?**
→ Just sign in again (takes 30 seconds)

**Console says "undefined"?**
→ You need to sign in first!

---

## What's Next?

**Coming in 2-3 weeks:**
- Add events by talking to Siri
- Edit your calendar
- Full bi-directional sync

**For now:** You can VIEW your calendar easily! ✅
