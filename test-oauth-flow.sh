#!/bin/bash

# Test OAuth Flow
APP_URL="https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io"

echo "=== Testing OAuth Endpoints ==="
echo ""

echo "1. Testing /auth/oauth/login endpoint..."
curl -s -o /dev/null -w "Status: %{http_code}\n" "$APP_URL/auth/oauth/login"
echo ""

echo "2. Testing Google authorize URL..."
curl -s -o /dev/null -w "Status: %{http_code}\n" "$APP_URL/auth/google/authorize"
echo ""

echo "3. Getting app info..."
curl -s "$APP_URL/docs" | head -20
echo ""

echo "=== Check these URLs in your browser ==="
echo "Login page: $APP_URL/auth/oauth/login"
echo "Google OAuth: $APP_URL/auth/google/authorize"
