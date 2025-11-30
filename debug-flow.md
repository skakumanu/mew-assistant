# Debug: Token Flow Issue

Let me trace exactly what's happening:

1. User signs in with Google
2. OAuth callback creates JWT token
3. Redirects to /calendar?token=xxx
4. Calendar page should save token to localStorage
5. User clicks "Show My Events"
6. API call with token fails

Let's check each step...
