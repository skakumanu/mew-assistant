#!/bin/bash
AZURE_URL="https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io"

echo "🚀 Testing Mew Assistant Azure Deployment"
echo "=========================================="
echo ""

# 1. Register a test user
echo "1️⃣ Registering test user..."
REGISTER_RESPONSE=$(curl -s -X POST "$AZURE_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "azure-test@example.com",
    "password": "TestPass123!",
    "full_name": "Azure Test User",
    "role": "parent"
  }')
echo "$REGISTER_RESPONSE" | python3 -m json.tool
echo ""

# 2. Login
echo "2️⃣ Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST "$AZURE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "azure-test@example.com",
    "password": "TestPass123!"
  }')
echo "$LOGIN_RESPONSE" | python3 -m json.tool
TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)
echo "Token: ${TOKEN:0:50}..."
echo ""

# 3. Test /mew/confirm
echo "3️⃣ Testing /mew/confirm..."
curl -s -X GET "$AZURE_URL/mew/confirm" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo ""

# 4. Test /mew/summary
echo "4️⃣ Testing /mew/summary..."
curl -s -X POST "$AZURE_URL/mew/summary" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "azure-test@example.com", "days": 7}' | python3 -m json.tool
echo ""

# 5. Test /mew/ingest
echo "5️⃣ Testing /mew/ingest..."
curl -s -X POST "$AZURE_URL/mew/ingest" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Schedule dentist appointment for Johnny tomorrow at 3pm",
    "source": "sms",
    "metadata": {"phone": "+1234567890"}
  }' | python3 -m json.tool
echo ""

echo "✅ Azure deployment test complete!"
