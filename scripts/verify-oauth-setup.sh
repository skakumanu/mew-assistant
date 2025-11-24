#!/bin/bash

echo "=== OAuth Setup Verification ==="
echo ""
echo "Required Redirect URIs for Google Cloud Console:"
echo "✓ https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/auth/simple/google/callback"
echo ""
echo "Steps to add in Google Cloud Console:"
echo "1. Go to: https://console.cloud.google.com/apis/credentials"
echo "2. Click on your OAuth 2.0 Client ID (321461422476-sgt4knrr7movtjk2djdpt5bom4q90qfk)"
echo "3. Under 'Authorized redirect URIs', click 'ADD URI'"
echo "4. Paste: https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/auth/simple/google/callback"
echo "5. Click 'SAVE'"
echo ""
echo "Testing OAuth endpoint..."
curl -I https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/auth/simple/login 2>&1 | head -5
echo ""
echo "Once you've added the redirect URI, test by visiting:"
echo "https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/auth/simple/login"
