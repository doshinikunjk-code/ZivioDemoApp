import os
import time
import uuid
from collections import OrderedDict
from typing import Optional

import httpx
from emergentintegrations.llm.chat import LlmChat, UserMessage
from fastapi import APIRouter, HTTPException, Request, Response

from core import (
    EL_API_KEY,
    EL_DEFAULT_VOICE,
    EMERGENT_LLM_KEY,
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    build_system_prompt,
    chat_sessions,
    db,
    logger,
    track_event,
)
from twilio_helpers import validate_twilio_signature

router = APIRouter()

# ─── Short-lived audio cache for Twilio <Play> ─────────────────────────
# id → (timestamp, mp3 bytes). Twilio fetches within seconds of TwiML return.
_TTS_CACHE: "OrderedDict[str, tuple[float, bytes]]" = OrderedDict()
_TTS_CACHE_MAX = 200
_TTS_CACHE_TTL_S = 120


def _cache_audio(audio_bytes: bytes) -> str:
    audio_id = uuid.uuid4().hex[:12]
    now = time.time()
    while _TTS_CACHE and next(iter(_TTS_CACHE.values()))[0] < now - _TTS_CACHE_TTL_S:
        _TTS_CACHE.popitem(last=False)
    while len(_TTS_CACHE) >= _TTS_CACHE_MAX:
        _TTS_CACHE.popitem(last=False)
    _TTS_CACHE[audio_id] = (now, audio_bytes)
    return audio_id


async def _generate_eleven_audio(text: str, voice_id: str) -> Optional[bytes]:
    if not EL_API_KEY or not voice_id or not (text or "").strip():
        return None
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                json={
                    "text": text,
                    "model_id": "eleven_multilingual_v2",
                    "voice_settings": {
                        "stability": 0.38,
                        "similarity_boost": 0.88,
                        "style": 0.55,
                        "use_speaker_boost": True,
                    },
                },
                headers={"xi-api-key": EL_API_KEY, "Content-Type": "application/json", "Accept": "audio/mpeg"},
            )
            if r.status_code == 200:
                return r.content
            logger.error(f"IVR EL error {r.status_code}: {r.text[:200]}")
            return None
    except Exception as e:
        logger.error(f"IVR EL exception: {e}")
        return None


def _public_base_url(request: Request) -> str:
    forwarded_host = request.headers.get("x-forwarded-host") or request.url.hostname
    return f"https://{forwarded_host}"


def _pick_voice_id(config: dict, lang: str) -> str:
    voice_map = (config or {}).get("voice_ids") or {}
    return voice_map.get(lang) or voice_map.get("en") or EL_DEFAULT_VOICE


# Twilio Polly Neural fallback — preserves Indian accent when ElevenLabs fails.
_POLLY_FALLBACK = {
    "en": ("Polly.Raveena-Neural", "en-IN"),
    "hi": ("Polly.Aditi", "hi-IN"),
    "pa": ("Polly.Raveena-Neural", "en-IN"),  # Polly has no Punjabi — use Indian English
    "auto": ("Polly.Raveena-Neural", "en-IN"),
}


def _twiml_speak(text: str, audio_id: Optional[str], base_url: str, lang: str) -> str:
    if audio_id:
        return f"<Play>{base_url}/api/tts-cache/{audio_id}.mp3</Play>"
    voice, tw_lang = _POLLY_FALLBACK.get(lang, _POLLY_FALLBACK["en"])
    safe = (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f'<Say voice="{voice}" language="{tw_lang}">{safe}</Say>'


def _build_voice_twiml(reply_text: str, audio_id: Optional[str], base_url: str, lang: str, session_id: str, end: bool = False) -> str:
    spoken = _twiml_speak(reply_text, audio_id, base_url, lang)
    if end:
        return f'<?xml version="1.0" encoding="UTF-8"?><Response>{spoken}<Hangup/></Response>'
    gather_action = f"{base_url}/api/webhook/twilio/voice/respond?session_id={session_id}&lang={lang}"
    voice, tw_lang = _POLLY_FALLBACK.get(lang, _POLLY_FALLBACK["en"])
    gather = (
        f'<Gather input="speech" speechTimeout="auto" speechModel="experimental_conversations" '
        f'enhanced="true" profanityFilter="false" '
        f'language="{tw_lang}" hints="butter chicken, lamb chops, biryani, naan, lassi, '
        f'order, yes, no, confirm, pickup, delivery" '
        f'action="{gather_action}" method="POST">'
        f"{spoken}"
        f"</Gather>"
        f'<Say voice="{voice}" language="{tw_lang}">Sorry, I didn\'t catch that. Please call again.</Say>'
        f"<Hangup/>"
    )
    return f'<?xml version="1.0" encoding="UTF-8"?><Response>{gather}</Response>'


async def _ivr_ai_turn(session_id: str, user_text: str, lang: str, config: dict) -> str:
    if session_id not in chat_sessions:
        system = build_system_prompt(config, is_call=True)
        chat = LlmChat(api_key=EMERGENT_LLM_KEY, session_id=session_id, system_message=system)
        chat.with_model("anthropic", "claude-haiku-4-5-20251001")
        chat_sessions[session_id] = chat
        await track_event(config.get("id", "default"), "call_started", {"session_id": session_id})

    msg = user_text
    if lang and lang != "auto":
        lang_instr = {
            "en": "Reply ONLY in natural spoken English with an Indian tone.",
            "hi": "Reply ONLY in Hindi (Devanagari script). No English words.",
            "pa": "Reply ONLY in Punjabi (Gurmukhi script). No English words.",
        }.get(lang)
        if lang_instr:
            msg = f"[Language instruction: {lang_instr}]\n{msg}"

    response = await chat_sessions[session_id].send_message(UserMessage(text=msg))
    await track_event(config.get("id", "default"), "call_message", {"session_id": session_id})
    return (response or "").strip()


@router.post("/webhook/twilio/voice")
async def voice_inbound(request: Request):
    """Inbound call entrypoint. Greets the caller and starts the Gather loop."""
    config = await db.restaurants.find_one({"id": "default"}, {"_id": 0}) or {}
    await validate_twilio_signature(request, config)

    form = await request.form()
    call_sid = form.get("CallSid", uuid.uuid4().hex)
    from_number = form.get("From", "")
    logger.info(f"Voice call received from {from_number} (sid={call_sid})")

    rname = config.get("name", "Desi Road")
    base_url = _public_base_url(request)
    session_id = f"call_{call_sid}"
    lang = "en"

    greeting = f"Hello! Thank you for calling {rname}. This is Riya. What can I get started for you today?"
    voice_id = _pick_voice_id(config, lang)
    audio = await _generate_eleven_audio(greeting, voice_id)
    audio_id = _cache_audio(audio) if audio else None

    return Response(
        content=_build_voice_twiml(greeting, audio_id, base_url, lang, session_id),
        media_type="application/xml",
    )


@router.post("/webhook/twilio/voice/respond")
async def voice_respond(request: Request, session_id: str = "", lang: str = "en"):
    """Each speech turn from the caller."""
    config = await db.restaurants.find_one({"id": "default"}, {"_id": 0}) or {}
    await validate_twilio_signature(request, config)

    form = await request.form()
    speech_result = (form.get("SpeechResult") or "").strip()
    confidence = float(form.get("Confidence") or 0.0)
    logger.info(f"Voice turn {session_id} (conf={confidence:.2f}): {speech_result}")

    base_url = _public_base_url(request)

    if not speech_result:
        prompt = "Sorry, I didn't catch that. Could you say it again?"
        voice_id = _pick_voice_id(config, lang)
        audio = await _generate_eleven_audio(prompt, voice_id)
        audio_id = _cache_audio(audio) if audio else None
        return Response(
            content=_build_voice_twiml(prompt, audio_id, base_url, lang, session_id),
            media_type="application/xml",
        )

    try:
        reply = await _ivr_ai_turn(session_id, speech_result, lang, config)
    except Exception as e:
        logger.error(f"IVR AI turn error: {e}")
        reply = "Sorry, I had a small glitch. Could you repeat that?"

    end_phrases = ["see you at", "thank you", "bye", "alhamdulillah", "milte hain", "20 min", "ready in", "pickup confirmed"]
    should_end = any(p in reply.lower() for p in end_phrases) and len(reply) > 20

    voice_id = _pick_voice_id(config, lang)
    audio = await _generate_eleven_audio(reply, voice_id)
    audio_id = _cache_audio(audio) if audio else None

    return Response(
        content=_build_voice_twiml(reply, audio_id, base_url, lang, session_id, end=should_end),
        media_type="application/xml",
    )


@router.get("/tts-cache/{audio_id}.mp3")
async def serve_cached_audio(audio_id: str):
    entry = _TTS_CACHE.get(audio_id)
    if not entry:
        raise HTTPException(status_code=404, detail="audio expired")
    _, audio_bytes = entry
    return Response(content=audio_bytes, media_type="audio/mpeg")


@router.get("/voice/status")
async def voice_status(restaurant_id: str = "default"):
    config = await db.restaurants.find_one({"id": restaurant_id}, {"_id": 0}) or {}
    sid = config.get("twilio_account_sid") or TWILIO_ACCOUNT_SID
    token = config.get("twilio_auth_token") or TWILIO_AUTH_TOKEN
    voice_num = config.get("twilio_voice_number") or os.environ.get("TWILIO_VOICE_NUMBER", "")
    return {
        "configured": bool(sid and token),
        "voice_number": voice_num,
        "webhook_url": "/api/webhook/twilio/voice",
        "elevenlabs_enabled": bool(EL_API_KEY),
    }
