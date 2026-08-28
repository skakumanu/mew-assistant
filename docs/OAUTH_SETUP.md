# Sign-in and Calendar OAuth Setup Guide

Mew Assistant has two, deliberately separate, OAuth-shaped concerns:

1. **Sign-in** - who a parent is. Handled entirely by
   [WorkOS AuthKit](https://workos.com/docs/authkit) (hosted UI, no
   per-provider code in this app). Covers email/password, Google,
   Microsoft, Apple, and passwordless magic-code sign-in.
2. **Google Calendar access** - a parent granting Mew read access to a
   provider's calendar, once already signed in. Handled by its own,
   unrelated Google Cloud OAuth client
   (`app/routers/calendar_oauth.py`).

Do not conflate the two: WorkOS manages its own OAuth app registrations
with Google/Microsoft/Apple internally for sign-in. The Google Cloud
client described in part 2 below is a completely separate app
registration, used only for calendar reads, and must keep existing even
if WorkOS's own Google connection is reconfigured.

---

## 1. Sign-in — WorkOS AuthKit

### Step 1: Create a WorkOS account and project

1. Go to [workos.com](https://workos.com) and sign up.
2. Create a project. WorkOS's free tier covers up to 1M monthly active
   users - far beyond this app's scale.

### Step 2: Enable AuthKit and the sign-in methods you want

1. In the WorkOS dashboard, go to **User Management → AuthKit**.
2. Enable it, and turn on whichever sign-in methods you want available:
   email/password, Magic Auth (passwordless email code), and Social Auth
   (Google, Microsoft, Apple, GitHub). Each social provider has its own
   short setup step inside the WorkOS dashboard - WorkOS walks you through
   registering its own OAuth app with that provider; you don't do this in
   Google/Microsoft/Apple's own consoles directly.

### Step 3: Register the callback URL

In the WorkOS dashboard's redirect URI settings, add:

```
https://mew-assistant.fly.dev/auth/workos/callback
http://localhost:8888/auth/workos/callback   # for local development
```

### Step 4: Get your API key and client ID

From the WorkOS dashboard, copy the **API Key** and **Client ID**, then
set them as Fly secrets:

```bash
flyctl secrets set WORKOS_API_KEY="sk_..." WORKOS_CLIENT_ID="client_..." --app mew-assistant
```

For local development, set the same two as environment variables (or in
`.env`).

### Testing sign-in

1. Visit `/app/sign-in` - it redirects straight to WorkOS's hosted UI.
2. Complete sign-in with whichever method you enabled.
3. You should land on `/app/setup` (new account, no child on file yet) or
   `/app/parent` (an existing account).

---

## 2. Google Calendar access — a separate concern

This lets a parent connect a specific provider's Google Calendar so Mew
can pull sessions from it (`app/routers/calendar_oauth.py`,
`app/services/calendar_sync_service.py`). It has nothing to do with
sign-in and uses its own Google Cloud OAuth client.

### Step 1: Create a Google Cloud OAuth client

1. Go to [Google Cloud Console](https://console.cloud.google.com/) →
   **APIs & Services → Credentials**.
2. Create an **OAuth client ID** (Web application).
3. Add this authorized redirect URI:
   ```
   https://mew-assistant.fly.dev/calendar-sync/google/callback
   ```
4. Copy the Client ID and Client Secret.

### Step 2: Set the Fly secrets

```bash
flyctl secrets set GOOGLE_CLIENT_ID="..." GOOGLE_CLIENT_SECRET="..." --app mew-assistant
```

`BASE_URL` must also be set correctly (`https://mew-assistant.fly.dev` in
production) - both this flow and WorkOS's callback derive their redirect
URIs from it.

### Testing calendar connect

From `/app/parent`'s "Providers" tab, click "Connect Google Calendar" for
a provider you've added. You should be sent to Google's consent screen,
then back to `/app/parent?tab=providers` with the calendar connected.

---

## Troubleshooting

### "redirect_uri_mismatch"

The callback URL registered in WorkOS (part 1) or Google Cloud Console
(part 2) doesn't exactly match what the app is sending - check for a
missing/extra trailing slash, or `http` vs `https`. These are two
independent registrations; a mismatch in one never affects the other.

### Sign-in bounces back to `/app/sign-in?error=1`

Check the app logs for the actual WorkOS error (`flyctl logs`) - this
page deliberately doesn't show provider-specific detail to the browser.
Common causes: `WORKOS_API_KEY`/`WORKOS_CLIENT_ID` not set, or the
callback URL isn't registered in the WorkOS dashboard yet.

### Calendar connect fails, but sign-in works fine

These are unrelated OAuth clients - confirm `GOOGLE_CLIENT_ID`/
`GOOGLE_CLIENT_SECRET` (part 2) are set and that
`/calendar-sync/google/callback` is registered in Google Cloud Console,
not just WorkOS's own Google connection.
