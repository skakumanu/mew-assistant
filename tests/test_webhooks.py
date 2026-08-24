"""
Tests for the Twilio SMS/WhatsApp webhook receiver.

The receiver is only trustworthy because of the signature check: anyone who
finds the URL can otherwise POST a fake "SMS from Mom" and have it processed
like a real one. These cover the signature gate (missing header, wrong
signature, unconfigured token - all must fail closed) and the payload
parsers that normalise Twilio's field names into what the rest of the app
expects.
"""

from unittest.mock import AsyncMock, patch

from twilio.request_validator import RequestValidator

from app.integrations.sms_integration import SMSIntegration
from app.integrations.whatsapp_integration import WhatsAppIntegration

AUTH_TOKEN = "test-twilio-auth-token"


def _sign(url: str, params: dict) -> str:
    return RequestValidator(AUTH_TOKEN).compute_signature(url, params)


class TestParseIncomingSms:
    def test_parses_twilio_field_names(self):
        parsed = SMSIntegration().parse_incoming_sms(
            {
                "MessageSid": "SM123",
                "From": "+14155551234",
                "To": "+14155556789",
                "Body": "Can we move Tuesday's session?",
                "NumMedia": "0",
            }
        )
        assert parsed == {
            "message_sid": "SM123",
            "from_number": "+14155551234",
            "to_number": "+14155556789",
            "body": "Can we move Tuesday's session?",
            "num_media": 0,
        }

    def test_missing_fields_default_safely(self):
        parsed = SMSIntegration().parse_incoming_sms({})
        assert parsed["message_sid"] == ""
        assert parsed["from_number"] == ""
        assert parsed["num_media"] == 0


class TestParseIncomingWhatsApp:
    def test_strips_whatsapp_prefix(self):
        parsed = WhatsAppIntegration().parse_incoming_message(
            {
                "MessageSid": "SM456",
                "From": "whatsapp:+14155551234",
                "To": "whatsapp:+14155556789",
                "Body": "Running late",
                "NumMedia": "0",
                "ProfileName": "Dana",
            }
        )
        assert parsed["from_number"] == "+14155551234"
        assert parsed["to_number"] == "whatsapp:+14155556789"
        assert parsed["profile_name"] == "Dana"

    def test_number_without_prefix_is_left_alone(self):
        parsed = WhatsAppIntegration().parse_incoming_message({"From": "+14155551234"})
        assert parsed["from_number"] == "+14155551234"

    def test_missing_profile_name_is_none(self):
        parsed = WhatsAppIntegration().parse_incoming_message({"From": "whatsapp:+1"})
        assert parsed["profile_name"] is None


class TestWebhookSignatureGate:
    """Every message-processing endpoint must fail closed."""

    def test_sms_incoming_rejects_missing_signature(self, client):
        with patch("app.utils.twilio_signature.settings.TWILIO_AUTH_TOKEN", AUTH_TOKEN):
            resp = client.post(
                "/webhooks/sms/incoming",
                data={"MessageSid": "SM1", "From": "+1", "To": "+2", "Body": "hi"},
            )
        assert resp.status_code == 403

    def test_sms_incoming_rejects_wrong_signature(self, client):
        with patch("app.utils.twilio_signature.settings.TWILIO_AUTH_TOKEN", AUTH_TOKEN):
            resp = client.post(
                "/webhooks/sms/incoming",
                data={"MessageSid": "SM1", "From": "+1", "To": "+2", "Body": "hi"},
                headers={"X-Twilio-Signature": "not-a-real-signature"},
            )
        assert resp.status_code == 403

    def test_sms_incoming_fails_closed_when_unconfigured(self, client):
        params = {"MessageSid": "SM1", "From": "+1", "To": "+2", "Body": "hi"}
        with patch("app.utils.twilio_signature.settings.TWILIO_AUTH_TOKEN", None):
            sig = _sign("http://testserver/webhooks/sms/incoming", params)
            resp = client.post(
                "/webhooks/sms/incoming",
                data=params,
                headers={"X-Twilio-Signature": sig},
            )
        assert resp.status_code == 403

    def test_whatsapp_incoming_rejects_missing_signature(self, client):
        with patch("app.utils.twilio_signature.settings.TWILIO_AUTH_TOKEN", AUTH_TOKEN):
            resp = client.post(
                "/webhooks/whatsapp/incoming",
                data={
                    "MessageSid": "SM1",
                    "From": "whatsapp:+1",
                    "To": "whatsapp:+2",
                    "Body": "hi",
                },
            )
        assert resp.status_code == 403

    def test_sms_incoming_accepts_valid_signature(self, client):
        params = {"MessageSid": "SM1", "From": "+15550001111", "To": "+15550002222", "Body": "hi"}
        with patch("app.utils.twilio_signature.settings.TWILIO_AUTH_TOKEN", AUTH_TOKEN):
            sig = _sign("http://testserver/webhooks/sms/incoming", params)
            with patch(
                "app.services.message_service.MessageService.process_incoming_message",
                new_callable=AsyncMock,
                return_value={"reply": "Got it!"},
            ):
                resp = client.post(
                    "/webhooks/sms/incoming",
                    data=params,
                    headers={"X-Twilio-Signature": sig},
                )
        assert resp.status_code == 200
        assert "Got it!" in resp.text

    def test_whatsapp_incoming_accepts_valid_signature(self, client):
        params = {
            "MessageSid": "SM2",
            "From": "whatsapp:+15550001111",
            "To": "whatsapp:+15550002222",
            "Body": "Running late",
            "ProfileName": "Dana",
        }
        with patch("app.utils.twilio_signature.settings.TWILIO_AUTH_TOKEN", AUTH_TOKEN):
            sig = _sign("http://testserver/webhooks/whatsapp/incoming", params)
            with patch(
                "app.services.message_service.MessageService.process_incoming_message",
                new_callable=AsyncMock,
                return_value={"reply": "Noted."},
            ) as mocked:
                resp = client.post(
                    "/webhooks/whatsapp/incoming",
                    data=params,
                    headers={"X-Twilio-Signature": sig},
                )
        assert resp.status_code == 200
        assert "Noted." in resp.text
        # The "whatsapp:" prefix must never reach the shared message pipeline.
        assert mocked.call_args.kwargs["from_contact"] == "+15550001111"
        assert mocked.call_args.kwargs["profile_name"] == "Dana"


class TestWebhookUnauthenticatedEndpoints:
    """Status callbacks and health checks don't feed message processing."""

    def test_health_check_is_public(self, client):
        resp = client.get("/webhooks/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    def test_sms_status_is_public(self, client):
        resp = client.get(
            "/webhooks/sms/status", params={"MessageSid": "SM1", "MessageStatus": "delivered"}
        )
        assert resp.status_code == 200
