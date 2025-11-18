#!/bin/bash

# Test AI Scheduler Endpoints
# Run this after starting the server with ./podman-start.sh

APP_URL="http://localhost:8888"
TOKEN="${1:-YOUR_TOKEN_HERE}"

echo "🧪 Testing AI Scheduler Endpoints"
echo "=================================="
echo ""

# Test 1: Detect Conflicts
echo "📍 Test 1: Detect Conflicts"
echo "----------------------------"
curl -s -X POST "$APP_URL/ai-scheduler/detect-conflicts" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "start_time": "2025-01-20T10:00:00",
    "end_time": "2025-01-20T11:00:00",
    "title": "Therapy Session",
    "activity_type": "therapy",
    "priority": "high"
  }' | python -m json.tool
echo ""
echo ""

# Test 2: Suggest Times
echo "📍 Test 2: Suggest Optimal Times"
echo "----------------------------"
curl -s -X POST "$APP_URL/ai-scheduler/suggest-times" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "activity_type": "therapy",
    "duration_minutes": 60,
    "preferred_date": "2025-01-20T00:00:00",
    "constraints": {
      "earliest_hour": 8,
      "latest_hour": 18,
      "buffer_minutes": 15
    }
  }' | python -m json.tool
echo ""
echo ""

# Test 3: Learning Status
echo "📍 Test 3: Learning Status"
echo "----------------------------"
curl -s -X GET "$APP_URL/ai-scheduler/learning-status" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
echo ""
echo ""

# Test 4: Optimize Schedule
echo "📍 Test 4: Optimize Schedule"
echo "----------------------------"
curl -s -X POST "$APP_URL/ai-scheduler/optimize-schedule" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2025-01-20T00:00:00",
    "optimization_goals": [
      "minimize_transitions",
      "respect_energy_levels",
      "balance_activities"
    ]
  }' | python -m json.tool
echo ""

echo "✅ All tests complete!"
echo ""
echo "Note: You need a valid token. Get one by:"
echo "  1. Register: curl -X POST $APP_URL/auth/register ..."
echo "  2. Login: curl -X POST $APP_URL/auth/login ..."
echo "  3. Run: ./test_ai_endpoints.sh YOUR_TOKEN"
