# Siri Setup Guide for Mew Assistant

## 🎯 Quick Start for iOS/macOS

Your Mew Assistant is now live at:
**https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io**

## Step 1: Set Up Siri Shortcuts

### On iPhone/iPad:
1. Open the **Shortcuts** app
2. Tap the **+** button to create a new shortcut
3. Search for "Get Contents of URL"
4. Configure each shortcut below

### On Mac:
1. Open **Shortcuts** app (in Applications or via Spotlight)
2. Follow the same process as iOS

## Step 2: Create Mew Assistant Shortcuts

### Shortcut 1: "Mew, Connect my Calendar"
**Purpose:** Link your Google Calendar to Mew Assistant

1. Add action: "Get Contents of URL"
   - URL: `https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/api/v1/calendar/google/auth`
   - Method: GET
   - Headers: Add `Authorization: Bearer YOUR_TOKEN`

2. Add action: "Open URLs"
   - URL: Get Contents of URL

3. Name the shortcut: "Mew Connect Calendar"
4. Add to Siri: "Hey Siri, Mew connect my calendar"

### Shortcut 2: "Mew, What's my schedule?"
**Purpose:** Get today's schedule

1. Add action: "Get Contents of URL"
   - URL: `https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/mew/summary`
   - Method: GET
   - Headers: Add `Authorization: Bearer YOUR_TOKEN`

2. Add action: "Get Dictionary Value"
   - Key: summary
   - Dictionary: Get Contents of URL

3. Add action: "Speak Text"
   - Text: Dictionary Value

4. Name: "Mew Schedule"
5. Add to Siri: "Hey Siri, Mew what's my schedule?"

### Shortcut 3: "Mew, Add [Event] to Calendar"
**Purpose:** Quick event creation via voice

1. Add action: "Ask for Input"
   - Prompt: "What event would you like to add?"
   
2. Add action: "Get Contents of URL"
   - URL: `https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/mew/ingest`
   - Method: POST
   - Headers: 
     - `Authorization: Bearer YOUR_TOKEN`
     - `Content-Type: application/json`
   - Request Body: JSON
     ```json
     {
       "message": "Provided Input",
       "channel": "siri",
       "priority": "normal"
     }
     ```

3. Add action: "Show Result"
   - Result: Get Contents of URL

4. Name: "Mew Add Event"
5. Add to Siri: "Hey Siri, Mew add to calendar"

### Shortcut 4: "Mew, Login"
**Purpose:** Get your authentication token

1. Add action: "Ask for Input"
   - Prompt: "Email?"
   
2. Save to variable: email

3. Add action: "Ask for Input"
   - Prompt: "Password?" (with "Hide Text" enabled)
   
4. Save to variable: password

5. Add action: "Get Contents of URL"
   - URL: `https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/auth/login`
   - Method: POST
   - Headers: `Content-Type: application/json`
   - Request Body:
     ```json
     {
       "email": "email",
       "password": "password"
     }
     ```

6. Add action: "Get Dictionary Value"
   - Key: access_token

7. Add action: "Copy to Clipboard"
   - Text: Dictionary Value

8. Add action: "Show Alert"
   - Message: "Token copied to clipboard! Use it in other Mew shortcuts."

9. Name: "Mew Login"
10. Add to Siri: "Hey Siri, Mew login"

## Step 3: First Time Setup

### A. Get Your Authentication Token

**Option 1: Using Siri**
1. Say: "Hey Siri, Mew login"
2. Provide your email: `skakumanu@hotmail.com`
3. Provide your password
4. Token will be copied to clipboard

**Option 2: Using Browser**
1. Go to: https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/docs
2. Click "Authorize" button
3. Use federated login with Microsoft account
4. Copy the access token

### B. Add Token to Shortcuts
1. Open each shortcut you created
2. Find the "Authorization" header
3. Replace `YOUR_TOKEN` with your actual token
4. Save the shortcut

## Step 4: Connect Your Calendar

Say: **"Hey Siri, Mew connect my calendar"**

This will:
1. Open your browser
2. Ask you to log in to Google
3. Request calendar permissions
4. Redirect you back to Mew

## Step 5: Test Your Setup

Try these commands:

1. **"Hey Siri, Mew what's my schedule?"**
   - Siri will read your today's schedule

2. **"Hey Siri, Mew add to calendar"**
   - Siri will ask what event to add
   - Say: "Dentist appointment tomorrow at 2 PM"

3. **"Hey Siri, Mew confirm"**
   - Get pending confirmations/approvals

## 🎤 Natural Language Examples

Once set up, you can say things like:

- "Hey Siri, Mew add soccer practice Wednesday 4 PM"
- "Hey Siri, Mew schedule therapy session next Tuesday"
- "Hey Siri, Mew what do I have tomorrow?"
- "Hey Siri, Mew cancel my 3 PM meeting"

## 📱 Advanced: Automation Rules

### Auto-Morning Briefing
1. Open Shortcuts app
2. Go to "Automation" tab
3. Create "Time of Day" automation
4. Set time: 7:00 AM
5. Add action: Run Shortcut "Mew Schedule"
6. Disable "Ask Before Running"

### Auto-Evening Summary
Same as above but:
- Time: 8:00 PM
- Run: "Mew Daily Summary" shortcut

## 🔐 Security Notes

1. **Token Storage**: Tokens are stored securely in iOS Keychain
2. **Token Expiry**: Tokens expire after 7 days - re-run "Mew Login" when needed
3. **Permissions**: Only grant calendar access you're comfortable with
4. **Privacy**: All data is encrypted in transit and at rest

## 🆘 Troubleshooting

### "Cannot connect to server"
- Check your internet connection
- Verify the URL is correct

### "Unauthorized" error
- Run "Hey Siri, Mew login" to get a fresh token
- Update the token in all shortcuts

### "Token expired"
- Tokens last 7 days
- Run "Mew Login" again

### Siri doesn't understand
- Speak clearly and slowly
- Use the exact phrase you set up
- Check Siri settings: Settings > Siri & Search

## 📞 Support

For issues or questions:
- Email: skakumanu@gmail.com
- GitHub: https://github.com/skakumanu/mew-assistant

## 🎉 You're All Set!

Your Mew Assistant is ready to help manage your family's schedule via Siri. 
Start with simple commands and explore more features as you get comfortable!

---

**Pro Tip:** Create a "Morning Routine" automation that:
1. Reads your schedule
2. Checks weather
3. Reminds you of any pending approvals
4. All with one "Hey Siri, Good Morning"
