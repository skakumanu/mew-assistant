#!/bin/bash

# Let's manually test the ACTUAL flow
echo "=== Testing the complete flow ==="

# Step 1: Create a test token
echo -e "\n1. Testing token creation..."
TOKEN=$(curl -s "https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io/test-token" | jq -r '.token_preview')
echo "Token preview: $TOKEN"

# Step 2: Test if we can access the protected endpoint
echo -e "\n2. Testing API with fresh token..."
# We need a REAL token from sign-in, not the test one

echo -e "\n3. What error do you see exactly?"
echo "Please share the exact error message from browser console"
echo "Press F12 -> Console tab -> Click 'Show My Events' -> Copy error"
