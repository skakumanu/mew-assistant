# OAuth Quick Start Guide

## For Customer Zero (You!)

### Access the App

**Production URL:** https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io

### Login with Google (Federated Authentication)

1. **Open on your iPhone:** https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/oauth/login

2. **Tap "Sign in with Google"**

3. **Authorize the app** when Google prompts you

4. **You're logged in!** Your account will be created automatically with:
   - Email: skakumanu@gmail.com
   - Role: Superuser (god rights)
   - Linked to: Google OAuth

### Alternative: Microsoft Login

1. Same URL: https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/oauth/login

2. Tap "Sign in with Microsoft"

3. This will create/link to: skakumanu@hotmail.com with Admin role

### After Login

Once logged in, you can:

1. **Connect Your Google Calendar**
   ```bash
   curl -X POST https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/calendar/connect/google \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

2. **Test Voice Commands**
   - See SIRI_SETUP_GUIDE.md for Siri integration
   - Use the shortcuts provided

3. **Make a Scheduling Request**
   ```bash
   curl -X POST https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/voice/command \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "text": "Schedule dentist appointment tomorrow at 3pm",
       "language": "en"
     }'
   ```

### Troubleshooting

**Issue:** "Not Found" error
- **Solution:** Make sure you're using `/oauth/login` (not `/auth/oauth/login`)

**Issue:** Google/Microsoft auth fails
- **Solution:** Contact admin - OAuth credentials may need verification

**Issue:** Can't connect calendar
- **Solution:** Make sure you've completed OAuth login first

### Developer Access

**API Documentation:** https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/docs

**Health Check:** https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/health

### Your Accounts

As Customer Zero, you have TWO accounts set up:

1. **Superuser Account**
   - Email: skakumanu@gmail.com
   - Provider: Google OAuth
   - Permissions: Full god rights, can do anything

2. **Admin Account**
   - Email: skakumanu@hotmail.com
   - Provider: Microsoft OAuth
   - Permissions: Administrative access

### Support

For issues or questions:
- Check logs: `az containerapp logs show --name mew-assistant-dev --resource-group mew-assistant-dev-rg`
- View docs: `/docs` endpoint
- GitHub: https://github.com/skakumanu/mew-assistant
