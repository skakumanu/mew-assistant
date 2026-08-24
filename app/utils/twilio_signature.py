"""
Twilio webhook signature verification.

Twilio signs every webhook it sends with `X-Twilio-Signature`: HMAC-SHA1 of
the full request URL plus every POST parameter (sorted by name, no
separator), keyed with the account's auth token, base64-encoded. Verifying
it is what makes a webhook endpoint a *Twilio* webhook endpoint rather than
an open door - without it, anyone who finds the URL can POST a fake "SMS
from Mom" and get it processed exactly like a real one.

Uses Twilio's own SDK rather than a hand-rolled reimplementation: this is
exactly the kind of correctness-critical check where drift from the
vendor's own behavior (edge cases in encoding, future changes to the
algorithm) should be Twilio's problem to keep fixed, not ours to
rediscover.
"""

from __future__ import annotations

from fastapi import Request
from twilio.request_validator import RequestValidator

from .config import settings


def is_configured() -> bool:
    return bool(settings.TWILIO_AUTH_TOKEN)


async def verify_twilio_request(request: Request) -> bool:
    """
    True only if this request carries a valid Twilio signature.

    Fails closed: if the auth token isn't configured at all, this returns
    False rather than silently accepting unsigned requests - a webhook
    receiver with no way to verify its caller has no legitimate caller.
    """
    if not is_configured():
        return False

    signature = request.headers.get("X-Twilio-Signature")
    if not signature:
        return False

    form = await request.form()
    params = {key: str(value) for key, value in form.multi_items()}

    validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)
    return validator.validate(str(request.url), params, signature)
