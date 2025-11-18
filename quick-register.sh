#!/bin/bash

# Quick registration script for Mew Assistant
APP_URL="http://localhost:8888"

echo "🎯 Mew Assistant Quick Registration"
echo "===================================="
echo ""

# Register parent account
echo "📝 Registering parent account..."
curl -X POST $APP_URL/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "parent1",
    "email": "parent@example.com",
    "password": "ParentPass123!",
    "full_name": "Parent User",
    "role": "parent"
  }' | jq .

echo ""
echo "🔐 Logging in..."
TOKEN=$(curl -s -X POST $APP_URL/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "parent@example.com",
    "password": "ParentPass123!"
  }' | jq -r '.access_token // empty')

if [ -n "$TOKEN" ]; then
  echo "✅ Login successful!"
  echo "🎫 Your access token: $TOKEN"
  echo ""
  echo "📋 Save this for API calls:"
  echo "export MEW_TOKEN='$TOKEN'"
  echo ""
  echo "🧪 Test API call:"
  echo "curl -H 'Authorization: Bearer $TOKEN' $APP_URL/sessions"
else
  echo "❌ Login failed. Please check credentials."
fi
