# 🎯 SIMPLEST SOLUTION - Use Siri Shortcuts (No Files!)

## The Problem
Downloaded HTML files don't work well. Too complicated.

## THE ACTUAL SIMPLE SOLUTION

Skip all the file downloads. Use your iPhone's Shortcuts app directly!

---

## ⚡ 3 Steps to View Your Calendar

### Step 1: Add Yourself as Test User (Required First!)

1. Go to: https://console.cloud.google.com/apis/credentials/consent
2. Scroll to "Test users"
3. Click "+ ADD USERS"
4. Add your email
5. Click "SAVE"

---

### Step 2: Sign In & Get Your Token

1. **On iPhone Safari, go to:**
   https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/auth/simple/google

2. **Sign in with Google** → Allow calendar permission

3. **You'll see a success page with text like:**
   ```
   Success! Hi [Your Name]!
   Your Google Calendar is connected.
   ```

4. **Open Safari Console** (if on computer):
   - Press F12 → Console tab
   - Type: `localStorage.getItem('mew_token')`
   - Copy the token (long text in quotes)

   **OR on iPhone - easier way below!**

---

### Step 3: Create iPhone Shortcut

**On your iPhone:**

1. Open **Shortcuts** app
2. Tap **+** (create new)
3. Tap **Add Action**
4. Search for **"Get Contents of URL"**
5. Fill in:
   - **URL:** `https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/simple-calendar/events?max_results=10`
   - **Method:** GET
   - Tap "Show More"
   - **Headers:** Add Header
     - Name: `Authorization`
     - Value: `Bearer ` (paste your token after "Bearer ")

6. Add another action: **"Show Result"**

7. **Name it:** "My Calendar"

8. **Run it!** → See your calendar! 🎉

---

## 💡 Even Easier: Use Safari Bookmark

Actually, the SIMPLEST way:

### After Step 2 (signing in), just bookmark this page:

**Bookmark this URL after signing in:**
```
https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io
```

Then whenever you need your calendar:
1. Open the bookmark
2. You're already signed in (stays for 30 days)
3. We'll add a calendar page there!

---

## 🚀 ACTUAL SIMPLEST: I'll Create a Web Page

Let me create a simple web page where:
1. You sign in once
2. Click "Show Calendar"
3. Done!

**No downloads. No shortcuts. Just a webpage.**

Would that work better?

---

## Summary

Current options (from simplest to complex):

1. **Web page** (I'll build this now) ← BEST
   - Go to URL
   - Click "Show Calendar"
   - Done!

2. **Safari bookmark** ← SIMPLE
   - Sign in once
   - Bookmark page
   - Come back anytime

3. **iPhone Shortcut** ← OK
   - Works offline
   - Need to copy token

4. **Download HTML file** ← TOO COMPLEX
   - Doesn't work well
   - Skip this!

**Let me build option #1 now - a simple web page!**
