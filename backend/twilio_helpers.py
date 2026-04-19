"""Twilio client + signature validation + WhatsApp send helper.

Shared between WhatsApp and Voice IVR routes.
"""
from typing import Optional, Tuple

from fastapi import HTTPException, Request

from core import (
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    TWILIO_VALIDATE_SIGNATURE,
    TWILIO_WHATSAPP_NUMBER,
    logger,
)


def get_twilio_client_sync(config: dict) -> Tuple[Optional[object], Optional[str]]:
    """Return (twilio.rest.Client, whatsapp_number) or (None, None) if not configured."""
    sid = (config or {}).get("twilio_account_sid") or TWILIO_ACCOUNT_SID
    token = (config or {}).get("twilio_auth_token") or TWILIO_AUTH_TOKEN
    wa_num = (config or {}).get("twilio_whatsapp_number") or TWILIO_WHATSAPP_NUMBER
    if not sid or not token or not wa_num:
        return None, None
    try:
        from twilio.rest import Client
        return Client(sid, token), wa_num
    except Exception as e:
        logger.error(f"Twilio init error: {e}")
        return None, None


async def send_whatsapp(config: dict, to_number: str, message: str) -> bool:
    client, from_number = get_twilio_client_sync(config)
    if not client:
        logger.info(f"WhatsApp not configured. Would send to {to_number}: {message}")
        return False
    try:
        to_wa = to_number if to_number.startswith("whatsapp:") else f"whatsapp:{to_number}"
        from_wa = from_number if from_number.startswith("whatsapp:") else f"whatsapp:{from_number}"
        msg = client.messages.create(body=message, from_=from_wa, to=to_wa)
        logger.info(f"WhatsApp sent: {msg.sid}")
        return True
    except Exception as e:
        logger.error(f"WhatsApp send error: {e}")
        return False


async def validate_twilio_signature(request: Request, config: Optional[dict] = None) -> None:
    """Validate X-Twilio-Signature on inbound webhook requests.

    If TWILIO_VALIDATE_SIGNATURE is false (dev mode) or no auth token is configured,
    validation is skipped with a WARNING log — the endpoints still work so the
    agent is testable in preview environments.

    Raises HTTPException(403) on mismatch.
    """
    token = (config or {}).get("twilio_auth_token") or TWILIO_AUTH_TOKEN
    if not TWILIO_VALIDATE_SIGNATURE:
        logger.warning("Twilio signature validation DISABLED (TWILIO_VALIDATE_SIGNATURE=false)")
        return
    if not token:
        logger.warning("Twilio signature validation SKIPPED — no auth token configured (dev mode)")
        return

    signature = request.headers.get("X-Twilio-Signature", "")
    if not signature:
        logger.warning("Twilio webhook missing X-Twilio-Signature header — rejecting")
        raise HTTPException(status_code=403, detail="Missing signature")

    # Twilio validates against the full PUBLIC URL + sorted form params.
    # Behind a proxy the scheme/host must come from forwarded headers.
    forwarded_proto = request.headers.get("x-forwarded-proto", "https")
    forwarded_host = request.headers.get("x-forwarded-host") or request.url.netloc
    url = f"{forwarded_proto}://{forwarded_host}{request.url.path}"
    if request.url.query:
        url = f"{url}?{request.url.query}"

    form = await request.form()
    params = {k: v for k, v in form.items()}

    try:
        from twilio.request_validator import RequestValidator
        validator = RequestValidator(token)
        if not validator.validate(url, params, signature):
            logger.warning(f"Twilio signature INVALID for {url}")
            raise HTTPException(status_code=403, detail="Invalid signature")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Twilio signature validation error: {e}")
        raise HTTPException(status_code=403, detail="Signature validation failed")
