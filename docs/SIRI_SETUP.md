# 📱 Siri Setup Guide for Mew Assistant

## Quick Setup via QR Code

### Step 1: Install the Shortcut

Scan this QR code with your iPhone Camera app:

```
┌─────────────────────────────────────────┐
│  Scan to Install Mew Assistant Shortcut │
│                                           │
│   ███████████████████████████████████   │
│   ██ ▄▄▄▄▄ █▀█ █▄▄▀▄▀▀▄█ ▄▄▄▄▄ ██   │
│   ██ █   █ █▀▀▀█ ▀ █▀ ██ █   █ ██   │
│   ██ █▄▄▄█ █▀ █▀▀██▀▄ █ █▄▄▄█ ██   │
│   ██▄▄▄▄▄▄▄█▄█ █ ▀ ▀ █ ▀▄▄▄▄▄▄▄██   │
│   ██  ▄▀ ▀▄▀▄▄▀██▄█▄▀▀▄▀▀▀▀█▀▄██   │
│   ██ █▀▄▀▀▄▄█▀▄▀█▄█▄  █▄ ▀▄▀ ▀██   │
│   ██▄█▄▄▄█▄▄▀ █▀▀▀▀ ▀▄█ ▄▄▄ ▀▄██   │
│   ██ ▄▄▄▄▄ █▄ ▄▀█▄▀ ▄▄  █▄█ ▀▄██   │
│   ██ █   █ █  █▄█▀██▄▄▄▄▄  ▄▀ ██   │
│   ██ █▄▄▄█ █ ██▀█ ▀ ▀█▀ █▀ █  ██   │
│   ██▄▄▄▄▄▄▄█▄▄██▄█▄█▄▄▄██▄▄▄▄▄██   │
│   ███████████████████████████████████   │
│                                           │
│  https://mew-app.azurewebsites.net     │
└─────────────────────────────────────────┘
```

**Or use this direct link:**
```
https://www.icloud.com/shortcuts/mew-assistant
```

### Step 2: Configure the Shortcut

After installation, the shortcut will:
1. Ask for your Mew Assistant URL (default: https://mew-app.azurewebsites.net)
2. Guide you through federated login (Google/Apple/Microsoft)
3. Save your credentials securely in iOS Keychain

### Step 3: Voice Commands

Once setup is complete, you can use these Siri commands:

#### Authentication
- "Hey Siri, login to Mew"
- "Hey Siri, connect my calendar to Mew"

#### Scheduling
- "Hey Siri, ask Mew to schedule therapy tomorrow at 3pm"
- "Hey Siri, what's on my schedule today?"
- "Hey Siri, move my appointment to next Tuesday"

#### Quick Actions
- "Hey Siri, send daily summary from Mew"
- "Hey Siri, check conflicts in Mew"
- "Hey Siri, approve pending requests in Mew"

## Manual Installation (Alternative)

If you prefer to create the shortcut manually:

1. Open **Shortcuts** app on iPhone
2. Tap **+** to create new shortcut
3. Add action: **Get Contents of URL**
   - URL: `https://mew-app.azurewebsites.net/voice/siri`
   - Method: POST
4. Add action: **Get Dictionary from Input**
5. Add action: **Speak Text**
   - Text: Get "message" from Dictionary
6. Name it "Talk to Mew"
7. Add to Siri with phrase "Hey Siri, talk to Mew"

## Federated Login Setup

### For Google Account (skakumanu@gmail.com - Superuser)

1. Say: "Hey Siri, login to Mew"
2. When prompted, say: "Use Google"
3. Follow OAuth flow in Safari
4. Your Google Calendar will auto-sync

### For Microsoft Account (skakumanu@hotmail.com - Admin)

1. Say: "Hey Siri, login to Mew" 
2. When prompted, say: "Use Microsoft"
3. Follow OAuth flow in Safari
4. Your Outlook Calendar will auto-sync

## Shortcut Configuration (JSON)

For advanced users, here's the complete shortcut configuration:

```json
{
  "WFWorkflowActions": [
    {
      "WFWorkflowActionIdentifier": "is.workflow.actions.url",
      "WFWorkflowActionParameters": {
        "WFURLActionURL": "https://mew-app.azurewebsites.net/voice/siri"
      }
    },
    {
      "WFWorkflowActionIdentifier": "is.workflow.actions.downloadurl",
      "WFWorkflowActionParameters": {
        "WFHTTPMethod": "POST",
        "WFHTTPBodyType": "JSON",
        "WFJSONValues": {
          "command": "{{WFInput}}",
          "language": "auto",
          "user_context": "ios_siri"
        }
      }
    },
    {
      "WFWorkflowActionIdentifier": "is.workflow.actions.getvalueforkey",
      "WFWorkflowActionParameters": {
        "WFDictionaryKey": "response"
      }
    },
    {
      "WFWorkflowActionIdentifier": "is.workflow.actions.speaktext",
      "WFWorkflowActionParameters": {
        "WFSpeakTextRate": 0.5,
        "WFSpeakTextLanguage": "auto"
      }
    }
  ],
  "WFWorkflowName": "Mew Assistant",
  "WFWorkflowDescription": "Voice assistant for special needs families"
}
```

## Troubleshooting

### Siri doesn't recognize "Mew"
- Open Shortcuts app
- Find "Mew Assistant" shortcut
- Tap (•••) menu
- Select "Add to Siri"
- Record custom phrase clearly: "Talk to Mew"

### Authentication Issues
- Clear Safari cookies
- Re-run: "Hey Siri, login to Mew"
- Select your federated provider again

### Calendar Not Syncing
- Check Calendar permissions in Settings > Privacy
- Re-authorize: "Hey Siri, connect my calendar to Mew"

## Security Notes

✅ All credentials stored in iOS Keychain
✅ OAuth tokens auto-refresh
✅ Federated auth - no password storage
✅ End-to-end encryption for voice data

## Next Steps

1. **Scan QR code** above to install
2. **Login** with your federated account
3. **Connect calendar** via voice command
4. **Start scheduling** with natural language!

---

**Support:** For issues, email support@mewassistant.org or open a GitHub issue.
