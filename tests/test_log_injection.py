"""
Regression tests for log injection via unsanitized f-string interpolation.

`app/middleware/{compliance,middlewares,security}.py` used to build log
messages like `f"Missing consent for {request.url.path}"` - request-controlled
text (a URL path, a header value, a query string) landing directly in the
formatted message. An attacker who gets a CRLF sequence through URL decoding
into one of those values could forge extra log lines. The fix keeps every log
*message* a static string and carries the untrusted value in `extra_data`
instead, which either never reaches the rendered line (StandardFormatter
ignores `extra_data`) or is JSON-escaped (JSONFormatter) - either way a
newline in the value can't masquerade as a new log line.
"""

import logging

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.security import SecurityMiddleware

FORGED_LINE = 'FORGED_LOG_ENTRY level=CRITICAL msg="fake"'
# "; DROP TABLE" trips SecurityMiddleware.DANGEROUS_PATTERNS so the log call
# actually fires; the CRLF + forged line is the injection attempt riding
# along with it.
INJECTION_PAYLOAD = f"; DROP TABLE users;--\r\n{FORGED_LINE}"


@pytest.fixture
def app():
    app = FastAPI()
    app.add_middleware(SecurityMiddleware)

    @app.get("/test")
    async def test_endpoint():
        return {"status": "ok"}

    return app


@pytest.fixture
def client(app):
    return TestClient(app, raise_server_exceptions=False)


class TestSecurityMiddlewareLogInjection:
    def test_malicious_header_value_never_lands_in_the_log_message(self, client, caplog):
        """
        A header value carrying both a dangerous pattern (to trigger the log
        call) and a forged log line must never appear in the rendered
        message - only in structured extra_data.
        """
        with caplog.at_level(logging.ERROR, logger="app.middleware.security"):
            client.get("/test", headers={"X-Test": INJECTION_PAYLOAD})

        assert caplog.records, "expected the malicious-pattern log call to fire"
        for record in caplog.records:
            assert FORGED_LINE not in record.getMessage()

        # The raw value is still captured, just as structured data rather
        # than interpolated text.
        carried = [
            getattr(r, "extra_data", None) for r in caplog.records if hasattr(r, "extra_data")
        ]
        assert any(
            d and FORGED_LINE in str(d.get("value", "")) for d in carried
        ), "the raw header value should still be captured in extra_data"

    def test_rate_limit_log_carries_client_ip_as_structured_data(self, caplog):
        """`_check_rate_limit` must not interpolate client_ip/path into text."""
        import asyncio

        mw = SecurityMiddleware(app=None)
        mw.RATE_LIMITS = {"/x": 1}

        async def hit_twice():
            await mw._check_rate_limit("1.2.3.4", "/x")
            await mw._check_rate_limit("1.2.3.4", "/x")

        with caplog.at_level(logging.WARNING, logger="app.middleware.security"):
            with pytest.raises(Exception):
                asyncio.run(hit_twice())

        assert caplog.records
        record = caplog.records[-1]
        assert "1.2.3.4" not in record.getMessage()
        assert getattr(record, "extra_data", {}).get("client_ip") == "1.2.3.4"


class TestComplianceMiddlewareLogInjection:
    def test_missing_consent_log_carries_path_as_structured_data(self, caplog):
        from app.middleware.compliance import ComplianceMiddleware

        class FakeURL:
            path = f"/mew/ingest\r\n{FORGED_LINE}"

        class FakeRequest:
            url = FakeURL()
            headers = {}

        mw = ComplianceMiddleware(app=None)

        import asyncio

        with caplog.at_level(logging.WARNING, logger="app.middleware.compliance"):
            with pytest.raises(Exception):
                asyncio.run(mw._verify_consent(FakeRequest()))

        assert caplog.records
        record = caplog.records[0]
        assert FORGED_LINE not in record.getMessage()
        assert FORGED_LINE in getattr(record, "extra_data", {}).get("path", "")
