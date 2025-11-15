#!/bin/bash
# Test script for Mew Assistant Authentication API

echo "🧪 Testing Mew Assistant Authentication API"
echo "=========================================="
echo ""

BASE_URL="http://localhost:8000"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test 1: Health Check
echo "1️⃣  Testing Health Check..."
response=$(curl -s -w "\n%{http_code}" "$BASE_URL/health")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" == "200" ]; then
    echo -e "${GREEN}✓${NC} Health check passed"
    echo "$body" | python -m json.tool
else
    echo -e "${RED}✗${NC} Health check failed (HTTP $http_code)"
fi
echo ""

# Test 2: Register User
echo "2️⃣  Testing User Registration..."
register_response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/auth/register" \
    -H "Content-Type: application/json" \
    -d '{
        "username": "test_user_'$(date +%s)'",
        "email": "test'$(date +%s)'@example.com",
        "password": "TestPass123!",
        "full_name": "Test User",
        "role": "parent"
    }')

http_code=$(echo "$register_response" | tail -n1)
body=$(echo "$register_response" | head -n-1)

if [ "$http_code" == "201" ]; then
    echo -e "${GREEN}✓${NC} User registration successful"
    echo "$body" | python -m json.tool
    TEST_EMAIL=$(echo "$body" | python -c "import sys, json; print(json.load(sys.stdin)['email'])")
    TEST_USERNAME=$(echo "$body" | python -c "import sys, json; print(json.load(sys.stdin)['username'])")
else
    echo -e "${RED}✗${NC} User registration failed (HTTP $http_code)"
    echo "$body"
    exit 1
fi
echo ""

# Test 3: Login
echo "3️⃣  Testing User Login..."
login_response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/auth/login" \
    -H "Content-Type: application/json" \
    -d "{
        \"email\": \"$TEST_EMAIL\",
        \"password\": \"TestPass123!\"
    }")

http_code=$(echo "$login_response" | tail -n1)
body=$(echo "$login_response" | head -n-1)

if [ "$http_code" == "200" ]; then
    echo -e "${GREEN}✓${NC} Login successful"
    ACCESS_TOKEN=$(echo "$body" | python -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
    REFRESH_TOKEN=$(echo "$body" | python -c "import sys, json; print(json.load(sys.stdin)['refresh_token'])")
    echo "Access Token: ${ACCESS_TOKEN:0:20}..."
    echo "Refresh Token: ${REFRESH_TOKEN:0:20}..."
else
    echo -e "${RED}✗${NC} Login failed (HTTP $http_code)"
    echo "$body"
    exit 1
fi
echo ""

# Test 4: Get Current User
echo "4️⃣  Testing Get Current User..."
me_response=$(curl -s -w "\n%{http_code}" "$BASE_URL/auth/me" \
    -H "Authorization: Bearer $ACCESS_TOKEN")

http_code=$(echo "$me_response" | tail -n1)
body=$(echo "$me_response" | head -n-1)

if [ "$http_code" == "200" ]; then
    echo -e "${GREEN}✓${NC} Get current user successful"
    echo "$body" | python -m json.tool
else
    echo -e "${RED}✗${NC} Get current user failed (HTTP $http_code)"
    echo "$body"
fi
echo ""

# Test 5: Create API Key
echo "5️⃣  Testing API Key Creation..."
api_key_response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/auth/api-keys" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "key_name": "test_key",
        "expires_in_days": 30,
        "scopes": ["read", "write"]
    }')

http_code=$(echo "$api_key_response" | tail -n1)
body=$(echo "$api_key_response" | head -n-1)

if [ "$http_code" == "200" ]; then
    echo -e "${GREEN}✓${NC} API key creation successful"
    API_KEY=$(echo "$body" | python -c "import sys, json; print(json.load(sys.stdin)['api_key'])")
    echo "API Key: ${API_KEY:0:20}..."
else
    echo -e "${RED}✗${NC} API key creation failed (HTTP $http_code)"
    echo "$body"
fi
echo ""

# Test 6: Use API Key
if [ ! -z "$API_KEY" ]; then
    echo "6️⃣  Testing API Key Authentication..."
    api_auth_response=$(curl -s -w "\n%{http_code}" "$BASE_URL/auth/me" \
        -H "Authorization: Bearer $API_KEY")

    http_code=$(echo "$api_auth_response" | tail -n1)
    body=$(echo "$api_auth_response" | head -n-1)

    if [ "$http_code" == "200" ]; then
        echo -e "${GREEN}✓${NC} API key authentication successful"
        echo "$body" | python -m json.tool
    else
        echo -e "${RED}✗${NC} API key authentication failed (HTTP $http_code)"
        echo "$body"
    fi
    echo ""
fi

# Test 7: Token Refresh
echo "7️⃣  Testing Token Refresh..."
refresh_response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/auth/refresh" \
    -H "Content-Type: application/json" \
    -d "{
        \"refresh_token\": \"$REFRESH_TOKEN\"
    }")

http_code=$(echo "$refresh_response" | tail -n1)
body=$(echo "$refresh_response" | head -n-1)

if [ "$http_code" == "200" ]; then
    echo -e "${GREEN}✓${NC} Token refresh successful"
    NEW_ACCESS_TOKEN=$(echo "$body" | python -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
    echo "New Access Token: ${NEW_ACCESS_TOKEN:0:20}..."
else
    echo -e "${RED}✗${NC} Token refresh failed (HTTP $http_code)"
    echo "$body"
fi
echo ""

echo "=========================================="
echo -e "${GREEN}✅ All authentication tests completed!${NC}"
echo ""
echo "Next steps:"
echo "  • Use the access token for protected endpoints"
echo "  • Try creating a session: POST /mew/session"
echo "  • Confirm a session: POST /mew/confirm"
echo "  • View API docs: $BASE_URL/docs"
