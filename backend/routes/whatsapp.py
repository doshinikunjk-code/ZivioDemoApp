from datetime import datetime, timezone

from emergentintegrations.llm.chat import LlmChat, UserMessage
from fastapi import APIRouter, HTTPException, Request, Response

from core import (
    EMERGENT_LLM_KEY,
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    TWILIO_WHATSAPP_NUMBER,
    build_system_prompt,
    chat_sessions,
    db,
    logger,
    track_event,
)
from models import WhatsAppMessage
from twilio_helpers import send_whatsapp, validate_twilio_signature

router = APIRouter()


@router.post("/whatsapp/send")
async def send_whatsapp_endpoint(req: WhatsAppMessage):
    config = await db.restaurants.find_one({"id": req.restaurant_id}, {"_id": 0})
    if not config:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    success = await send_whatsapp(config, req.to, req.message)
    await track_event(req.restaurant_id, "whatsapp_sent", {"to": req.to, "success": success})
    return {"sent": success}


@router.post("/whatsapp/webhook")
async def whatsapp_webhook(request: Request):
    # Signature validation (skipped in dev if no auth token)
    config = await db.restaurants.find_one({"id": "default"}, {"_id": 0}) or {}
    await validate_twilio_signature(request, config)

    form = await request.form()
    from_number = form.get("From", "")
    body = form.get("Body", "")
    logger.info(f"WhatsApp received from {from_number}: {body}")

    if config and body:
        sid = f"wa_{from_number}_{datetime.now(timezone.utc).strftime('%Y%m%d')}"
        if sid not in chat_sessions:
            system = build_system_prompt(config)
            chat = LlmChat(api_key=EMERGENT_LLM_KEY, session_id=sid, system_message=system)
            chat.with_model("anthropic", "claude-haiku-4-5-20251001")
            chat_sessions[sid] = chat
        response = await chat_sessions[sid].send_message(UserMessage(text=body))
        await send_whatsapp(config, from_number, response)
        await track_event("default", "whatsapp_conversation", {"from": from_number})

    return Response(content="<Response></Response>", media_type="application/xml")


@router.get("/whatsapp/status")
async def whatsapp_status(restaurant_id: str = "default"):
    config = await db.restaurants.find_one({"id": restaurant_id}, {"_id": 0})
    if not config:
        return {"configured": False}
    sid = config.get("twilio_account_sid") or TWILIO_ACCOUNT_SID
    token = config.get("twilio_auth_token") or TWILIO_AUTH_TOKEN
    wa = config.get("twilio_whatsapp_number") or TWILIO_WHATSAPP_NUMBER
    return {"configured": bool(sid and token and wa), "whatsapp_number": wa or ""}
