# Quick Start Registration Guide

## Access the Application

Your Mew Assistant is now running! Access it at:
- **API Documentation**: http://localhost:8888/docs
- **Alternative Docs**: http://localhost:8888/redoc
- **Base API**: http://localhost:8888

## Registration Steps

### Option 1: Using the Interactive API Docs (Easiest)

1. Open http://localhost:8888/docs in your browser
2. Find the **POST /auth/register** endpoint
3. Click "Try it out"
4. Fill in the JSON body:

```json
{
  "email": "your.email@example.com",
  "username": "your_username",
  "password": "YourSecurePassword123!",
  "full_name": "Your Full Name",
  "user_type": "parent"
}
```

5. Click "Execute"
6. You'll receive your user details and authentication token

### Option 2: Using cURL (Command Line)

```bash
curl -X POST "http://localhost:8888/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your.email@example.com",
    "username": "your_username",
    "password": "YourSecurePassword123!",
    "full_name": "Your Full Name",
    "user_type": "parent"
  }'
```

### Option 3: Using Python

```python
import requests

response = requests.post(
    "http://localhost:8888/auth/register",
    json={
        "email": "your.email@example.com",
        "username": "your_username",
        "password": "YourSecurePassword123!",
        "full_name": "Your Full Name",
        "user_type": "parent"
    }
)

print(response.json())
```

## User Types

- **parent**: Full access to all features (default)
- **caregiver**: Access to caregiver features, summaries
- **child**: Limited access, requires parental approval

## After Registration

1. **Save your access token** - you'll receive it in the response
2. **Login** to get a new token when needed:
   - Use `POST /auth/login` with your email and password
3. **Authorize** in Swagger UI:
   - Click the "Authorize" button at the top
   - Enter: `Bearer YOUR_ACCESS_TOKEN`
   - Now you can test all protected endpoints

## Quick Test After Registration

Once registered, try:

1. **Get your profile**:
```bash
curl -X GET "http://localhost:8888/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

2. **Create a session**:
```bash
curl -X POST "http://localhost:8888/sessions/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "web",
    "user_id": "YOUR_USER_ID"
  }'
```

3. **Send a message**:
```bash
curl -X POST "http://localhost:8888/mew/ingest" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Schedule a therapy session for tomorrow at 2pm",
    "channel": "web",
    "priority": "normal"
  }'
```

## Troubleshooting

### Blank Page on /docs
- Check browser console for errors (F12)
- Try refreshing the page
- Try /redoc instead

### Registration Fails
- Check if email/username already exists
- Ensure password meets requirements (min 8 chars)
- Verify all required fields are provided

### Connection Refused
- Ensure Podman containers are running: `podman ps`
- Check logs: `podman logs mew-app`
- Restart if needed: `./podman-start.sh`

## Next Steps

After successful registration:

1. ✅ Explore the API documentation at /docs
2. ✅ Set up your family profile
3. ✅ Configure calendar integrations
4. ✅ Test voice commands (if enabled)
5. ✅ Set up notification preferences

Need help? Check the README.md for detailed documentation.
