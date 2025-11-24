#!/bin/bash

# Mew Assistant - Federated Authentication Test
# This script helps test OAuth flows locally

echo "🔐 Mew Assistant - Federated Auth Tester"
echo "=========================================="
echo ""

# Use the Azure deployment URL
BASE_URL="https://mew-app-gyfre9f3gtgebjh9.eastus-01.azurewebsites.net"

echo "1. Testing OAuth Authorization URLs..."
echo ""

# Test Google OAuth
echo "📱 Google OAuth URL:"
curl -s "$BASE_URL/auth/federated/google/authorize" | jq -r '.authorization_url' || echo "Error getting Google auth URL"
echo ""

# Test Microsoft OAuth  
echo "📱 Microsoft OAuth URL:"
curl -s "$BASE_URL/auth/federated/microsoft/authorize" | jq -r '.authorization_url' || echo "Error getting Microsoft auth URL"
echo ""

# Test Apple OAuth
echo "📱 Apple OAuth URL:"
curl -s "$BASE_URL/auth/federated/apple/authorize" | jq -r '.authorization_url' || echo "Error getting Apple auth URL"
echo ""

echo "✅ Copy one of the URLs above and open in your browser"
echo "   After authorizing, you'll get a code in the redirect URL"
echo ""
echo "2. Then exchange the code for a token:"
echo "   curl -X POST $BASE_URL/auth/federated/google/callback \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"code\": \"YOUR_CODE_FROM_REDIRECT\"}'"

chmod +x test-federated-auth.sh
