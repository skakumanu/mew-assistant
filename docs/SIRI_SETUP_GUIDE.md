# Siri Commands for Mew Assistant Setup
## Step-by-Step Voice Commands for Admin Parent Account

### Prerequisites
- iOS device with Siri enabled
- Mew Assistant app installed or web access configured
- Siri Shortcuts app installed

---

## Phase 1: Initial Authentication (Federated Login)

### Command 1: Open Mew Assistant
**Say to Siri:**
```
"Hey Siri, open Mew Assistant"
```
or
```
"Hey Siri, go to mew-assistant-app.azurewebsites.net"
```

### Command 2: Login with Microsoft Account
**Say to Siri:**
```
"Hey Siri, login to Mew with my Microsoft account"
```

**This will:**
- Open the federated authentication flow
- Redirect to Microsoft OAuth login
- Authenticate you as skakumanu@hotmail.com (Admin role)
- Return with authentication token

---

## Phase 2: Calendar Integration Setup

### Command 3: Connect Google Calendar
**Say to Siri:**
```
"Hey Siri, connect my Google Calendar to Mew"
```

**This triggers:**
- OAuth flow for Google Calendar API
- Requests calendar read/write permissions
- Links your Google Calendar to Mew Assistant

### Command 4: Grant Calendar Permissions
**Say to Siri:**
```
"Hey Siri, allow Mew to access my calendar"
```

**Permissions granted:**
- Read calendar events
- Create new events
- Update existing events
- Delete events
- Access calendar metadata

---

## Phase 3: Voice Command Configuration

### Command 5: Enable Voice Scheduling
**Say to Siri:**
```
"Hey Siri, enable voice commands for Mew scheduling"
```

### Command 6: Set Default Calendar
**Say to Siri:**
```
"Hey Siri, set my Google Calendar as default for Mew"
```

---

## Phase 4: Test Voice Commands

### Test Command 1: Create an Event
**Say to Siri:**
```
"Hey Siri, tell Mew to schedule therapy session for tomorrow at 3 PM"
```

**Expected Response:**
```
"I've scheduled a therapy session for tomorrow at 3:00 PM. 
The event has been added to your Google Calendar. 
Would you like me to send a confirmation notification?"
```

### Test Command 2: Check Schedule
**Say to Siri:**
```
"Hey Siri, ask Mew what's on my schedule today"
```

**Expected Response:**
```
"You have 3 events today:
1. Speech therapy at 9:00 AM
2. Lunch break at 12:00 PM  
3. Occupational therapy at 2:30 PM
Would you like more details?"
```

### Test Command 3: Reschedule an Event
**Say to Siri:**
```
"Hey Siri, tell Mew to move therapy from 3 PM to 4 PM"
```

**Expected Response:**
```
"I found your therapy session at 3:00 PM. 
I'll reschedule it to 4:00 PM. 
Checking for conflicts... No conflicts found.
Event updated successfully!"
```

---

## Complete Setup Commands (In Order)

### Quick Setup Script
Execute these commands in sequence for complete setup:

```
1. "Hey Siri, open Mew Assistant"
2. "Hey Siri, login to Mew with my Microsoft account"
   [Complete authentication in browser]
3. "Hey Siri, connect my Google Calendar to Mew"
   [Grant calendar permissions]
4. "Hey Siri, enable voice commands for Mew"
5. "Hey Siri, set Google Calendar as default"
6. "Hey Siri, tell Mew my timezone is [Your Timezone]"
7. "Hey Siri, ask Mew to confirm setup"
```

---

## Alternative: iOS Shortcuts Setup

### Create Custom Siri Shortcut

#### Shortcut 1: "Setup Mew Calendar"
```
1. Open Shortcuts app
2. Create New Shortcut
3. Add actions:
   - URL: https://mew-assistant-app.azurewebsites.net/oauth/federated/microsoft
   - Get Contents of URL (Method: GET)
   - URL: https://mew-assistant-app.azurewebsites.net/calendar/connect
   - Get Contents of URL (Method: POST with auth token)
4. Name: "Setup Mew Calendar"
5. Add to Siri: "Setup my Mew calendar"
```

#### Shortcut 2: "Mew Quick Schedule"
```
1. Open Shortcuts app
2. Create New Shortcut
3. Add actions:
   - Ask for Input: "What would you like to schedule?"
   - Set Variable: eventDetails
   - URL: https://mew-assistant-app.azurewebsites.net/voice/command
   - Get Contents of URL (Method: POST)
     Body: {"text": [eventDetails], "channel": "siri"}
   - Show Result
4. Name: "Mew Quick Schedule"
5. Add to Siri: "Schedule with Mew"
```

---

## Troubleshooting Voice Commands

### If Siri Doesn't Recognize "Mew"
Try these alternatives:
- "Mew Assistant"
- "My scheduling assistant"
- "My family calendar app"

### If Authentication Fails
```
"Hey Siri, reset Mew authentication"
```
Then retry login flow.

### If Calendar Sync Fails
```
"Hey Siri, reconnect Mew to Google Calendar"
```

---

## Advanced Voice Commands

### Family Management
```
"Hey Siri, tell Mew to add my daughter Sarah to my family"
"Hey Siri, ask Mew to show Sarah's schedule"
"Hey Siri, tell Mew to share my calendar with my spouse"
```

### Smart Scheduling
```
"Hey Siri, ask Mew to find time for therapy next week"
"Hey Siri, tell Mew to avoid scheduling during lunch hours"
"Hey Siri, ask Mew to suggest optimal therapy times"
```

### Conflict Management
```
"Hey Siri, ask Mew if I have any scheduling conflicts"
"Hey Siri, tell Mew to resolve my calendar conflicts"
"Hey Siri, ask Mew to prioritize therapy appointments"
```

---

## Security & Privacy

### Voice Authentication
For sensitive operations, Siri will request additional verification:
```
"Hey Siri, delete all my Mew calendar events"
Response: "For security, please confirm by saying 'I authorize this action'"
```

### Data Access Control
```
"Hey Siri, show me what data Mew has access to"
"Hey Siri, revoke Mew's calendar access"
"Hey Siri, review Mew's privacy settings"
```

---

## Next Steps After Setup

1. **Test Basic Commands**: Try creating, viewing, and modifying events
2. **Set Up Family Members**: Add children and caregivers to your account
3. **Configure Notifications**: Set up reminders for events
4. **Explore AI Features**: Let Mew learn your scheduling patterns
5. **Invite Family**: Share access with spouse or caregivers

---

## Support

If you encounter issues:
```
"Hey Siri, ask Mew for help"
"Hey Siri, contact Mew support"
```

Or visit: https://mew-assistant-app.azurewebsites.net/docs

---

## Quick Reference Card

| Task | Siri Command |
|------|--------------|
| Login | "Hey Siri, login to Mew with Microsoft" |
| Connect Calendar | "Hey Siri, connect Google Calendar to Mew" |
| Create Event | "Hey Siri, tell Mew to schedule [event]" |
| Check Schedule | "Hey Siri, ask Mew what's on my schedule" |
| Reschedule | "Hey Siri, tell Mew to move [event]" |
| Get Help | "Hey Siri, ask Mew for help" |

---

**Pro Tip**: You can chain commands together:
```
"Hey Siri, tell Mew to schedule therapy tomorrow at 3 PM 
and send a reminder 30 minutes before"
```

Mew will handle multi-step requests intelligently!
