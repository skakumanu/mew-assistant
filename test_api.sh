#!/bin/bash
# Mew Assistant - API Test Script
# Quick tests to verify all endpoints are working

BASE_URL="http://localhost:8000"

echo "🧪 Testing Mew Assistant API"
echo "=============================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test health endpoint
echo "1. Testing health endpoint..."
response=$(curl -s -o /dev/null -w "%{http_code}" $BASE_URL/health)
if [ $response -eq 200 ]; then
    echo -e "${GREEN}✓ Health check passed${NC}"
else
    echo -e "${RED}✗ Health check failed (HTTP $response)${NC}"
fi
echo ""

# Test root endpoint
echo "2. Testing root endpoint..."
response=$(curl -s -o /dev/null -w "%{http_code}" $BASE_URL/)
if [ $response -eq 200 ]; then
    echo -e "${GREEN}✓ Root endpoint passed${NC}"
else
    echo -e "${RED}✗ Root endpoint failed (HTTP $response)${NC}"
fi
echo ""

# Test API docs
echo "3. Testing API documentation..."
response=$(curl -s -o /dev/null -w "%{http_code}" $BASE_URL/docs)
if [ $response -eq 200 ]; then
    echo -e "${GREEN}✓ API docs accessible${NC}"
else
    echo -e "${RED}✗ API docs failed (HTTP $response)${NC}"
fi
echo ""

echo "📝 Manual Testing Commands:"
echo ""
echo "Create a session:"
echo 'curl -X POST "'$BASE_URL'/mew/session" \'
echo '  -H "Content-Type: application/json" \'
echo '  -d '"'"'{"user_id":"test_user","session_type":"tutoring","title":"Test Session","priority":"normal"}'"'"
echo ""

echo "Ingest a message:"
echo 'curl -X POST "'$BASE_URL'/mew/ingest" \'
echo '  -H "Content-Type: application/json" \'
echo '  -d '"'"'{"channel":"email","sender":"test@example.com","body":"Test message"}'"'"
echo ""

echo "📚 Full API documentation available at:"
echo "   $BASE_URL/docs"
echo ""
