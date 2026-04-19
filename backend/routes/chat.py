from emergentintegrations.llm.chat import LlmChat, UserMessage
from fastapi import APIRouter, HTTPException

from core import EMERGENT_LLM_KEY, build_system_prompt, chat_sessions, db, logger, track_event
from models import ChatRequest

router = APIRouter()


@router.post("/chat")
async def chat_endpoint(req: ChatRequest):
    try:
        sid = req.session_id
        msg = req.message
        rid = req.restaurant_id or "default"

        config = await db.restaurants.find_one({"id": rid}, {"_id": 0})
        if not config:
            config = await db.restaurants.find_one({"id": "default"}, {"_id": 0})

        lang_map = {
            "en": "STRICT OVERRIDE: Regardless of the language this message is typed in, you MUST reply ONLY in natural spoken English. The user has pinned the English tab. Do not reply in Hindi or Punjabi.",
            "pa": "STRICT OVERRIDE: Regardless of the language this message is typed in, you MUST reply ONLY in Punjabi using Gurmukhi script (ਪੰਜਾਬੀ). Every single word in Punjabi. No English. No Hindi. The user has pinned the Punjabi tab.",
            "hi": "STRICT OVERRIDE: Regardless of the language this message is typed in, you MUST reply ONLY in Hindi using Devanagari script (हिन्दी). Every single word in Hindi. No English. No Punjabi. The user has pinned the Hindi tab.",
        }
        lang_context = lang_map.get(req.lang, "") if (req.lang and req.lang != "auto") else ""
        if lang_context:
            msg = f"[{lang_context}]\n{msg}"
        if req.context:
            msg = f"[Order context: {req.context}]\n{msg}"

        if sid not in chat_sessions:
            system = build_system_prompt(config, is_call=req.is_call)
            chat = LlmChat(api_key=EMERGENT_LLM_KEY, session_id=sid, system_message=system)
            chat.with_model("anthropic", "claude-haiku-4-5-20251001")
            chat_sessions[sid] = chat
            await track_event(rid, "conversation_started", {"session_id": sid, "is_call": req.is_call})

        response = await chat_sessions[sid].send_message(UserMessage(text=msg))
        await track_event(rid, "message_exchanged", {"session_id": sid})
        return {"reply": response}
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/reset")
async def reset_chat(session_id: str = ""):
    if session_id in chat_sessions:
        del chat_sessions[session_id]
    return {"status": "reset"}
