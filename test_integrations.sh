#!/bin/bash
# Test script for Phase 5 integrations

echo "🧪 Testing Mew Assistant Integrations"
echo "===================================="

API_URL="http://localhost:8000"

# Test webhook health
echo -e "\n📡 Testing Webhook Health..."
curl -s "${API_URL}/webhooks/health" | jq '.'

# Test incoming SMS webhook (simulated)
echo -e "\n📱 Testing SMS Webhook..."
curl -X POST "${API_URL}/webhooks/sms/incoming" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "MessageSid=SM123456" \
  -d "From=+1234567890" \
  -d "To=+0987654321" \
  -d "Body=Hello Mew, I need help with scheduling" \
  -d "NumMedia=0"

# Test incoming WhatsApp webhook (simulated)
echo -e "\n💬 Testing WhatsApp Webhook..."
curl -X POST "${API_URL}/webhooks/whatsapp/incoming" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "MessageSid=WA123456" \
  -d "From=whatsapp:+1234567890" \
  -d "To=whatsapp:+0987654321" \
  -d "Body=Can you send me today's summary?" \
  -d "NumMedia=0" \
  -d "ProfileName=John Doe"

echo -e "\n✅ Integration tests completed!"
echo "Note: For full testing, configure external services in .env"
