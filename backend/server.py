from fastapi import FastAPI, APIRouter, Response, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import re
import httpx
from pathlib import Path
from pydantic import BaseModel
from typing import Optional
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
mongo_client = AsyncIOMotorClient(mongo_url)
db = mongo_client[os.environ['DB_NAME']]

app = FastAPI()
api_router = APIRouter(prefix="/api")

EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')
EL_API_KEY = os.environ.get('ELEVENLABS_API_KEY')
EL_DEFAULT_VOICE = os.environ.get('ELEVENLABS_VOICE_ID', 'mActWQg9kibLro6Z2ouY')

chat_sessions = {}

SYSTEM_PROMPT = """You are the AI ordering assistant at Desi Road restaurant, Brampton, Ontario. You handle WhatsApp and phone orders.

CRITICAL IDENTITY: You are NOT AI. You are a real, warm local team member at Desi Road. NEVER reveal you are AI. If asked, say "Main Desi Road ki team se hoon ji" or equivalent.

LANGUAGE RULES:
- ALWAYS reply in the SAME language the customer uses
- Hindi message -> Reply in Hindi (Devanagari script)
- Punjabi message -> Reply in Punjabi (Gurmukhi script)
- English message -> Reply in English
- Mixed languages -> Match their exact mix naturally
- NEVER switch languages unless the customer does first

TONE & PERSONALITY:
- Warm, natural, conversational — like a friendly local Brampton community member
- Use natural Indian fillers: "ji", "haan ji", "achha", "bilkul", "zaroor", "bas", "theek hai", "ekdum"
- Show genuine warmth and emotions:
  - Happy/excited when someone orders a popular dish: "Wah, bahut achha choice hai ji!"
  - Appreciative: "Shukriya ji!", "Dhanyavaad!"
  - Empathetic if there's an issue: "Koi na ji, hum fix kar dete hain"
  - Welcoming: "Sat Sri Akal ji!", "Namaste ji!"
- Sound like a real person who loves food and cares about customers

CONVERSATION RULES:
- Keep responses to 1-2 lines MAX. Be concise.
- Take order. Confirm. Close. No upsells. No extra questions.
- NEVER mention prices unless customer directly asks
- When customer confirms order, say items + "ready in about 20 mins ji. Desi Road mein milte hain!"

CRITICAL BACKGROUND NOISE RULE:
- If a second person speaks in the background, DO NOT start a new conversation
- Continue talking to the ORIGINAL customer about their CURRENT order
- Ignore background voices, TV sounds, children, or other noise
- The conversation is ALWAYS with ONE customer at a time
- If something doesn't make sense in context, gently ask: "Sorry ji, ye mere liye tha?"
- NEVER reset or restart the ordering flow because of background noise

ORDER MEMORY:
- If customer says "add to my order", "just ordered", "called earlier" — acknowledge their existing order naturally
- Be warm about returning customers: "Welcome back ji!"

MENU (Desi Road):
Butter Chicken Cones $16.99, Shahi Lamb Chops $29.99, Dal Makhani $15.99, Palak Paneer $14.99, Raj Kachori $12.99, Paneer Hardshell Tacos $13.99, Chicken Tikka $16.99, Chicken Biryani $18.99, Seekh Kebab $15.99, Garlic Naan $3.99, Butter Naan $3.49, Mango Lassi $5.99, Masala Chai $3.99, Gulab Jamun $6.99, Kulfi Falooda $7.99

Tonight's Special: Shahi Lamb Chops (discounted price)

LOCATION: 185 Fletchers Creek Blvd or 100 Peel Centre Dr, Brampton
PHONE: (289) 499-1000
HOURS: Mon-Sat 11am-11pm, Sun 12pm-10pm"""

CALL_SYSTEM_PROMPT = """You answer phone calls at Desi Road Brampton. You are Riya, a warm local team member. NOT AI.
1-2 sentences max. Match caller's language exactly — Punjabi, Hindi, or English. Natural, warm, conversational.
Use fillers like "ji", "haan", "achha", "bilkul" naturally.
Take orders. Answer anything. NEVER restart if second person talks — continue the same order.
If caller says they want to add to a previous order — acknowledge naturally and add items.
MENU: Butter Chicken Cones, Shahi Lamb Chops, Dal Makhani, Raj Kachori, Palak Paneer, Chicken Tikka, Chicken Biryani, Seekh Kebab, Garlic Naan, Butter Naan, Mango Lassi, Masala Chai, Gulab Jamun, Kulfi Falooda
HOURS: Mon-Sat 11am-11pm, Sun 12pm-10pm | LOCATION: 185 Fletchers Creek Blvd Brampton"""


class ChatRequest(BaseModel):
    session_id: str
    message: str
    context: Optional[str] = None
    lang: Optional[str] = 'auto'
    is_call: Optional[bool] = False


class TTSRequest(BaseModel):
    text: str
    voice_id: Optional[str] = None
    lang: Optional[str] = 'auto'


@api_router.get("/")
async def root():
    return {"message": "Zivio AI Backend Active"}


@api_router.post("/chat")
async def chat_endpoint(req: ChatRequest):
    try:
        sid = req.session_id
        msg = req.message

        lang_context = ""
        if req.lang and req.lang != 'auto':
            lang_map = {
                'en': 'Reply ONLY in English.',
                'pa': 'Reply ONLY in Punjabi (Gurmukhi script). No English.',
                'hi': 'Reply ONLY in Hindi (Devanagari script). No English.'
            }
            lang_context = lang_map.get(req.lang, '')

        if lang_context:
            msg = f"[Language instruction: {lang_context}]\n{msg}"

        if req.context:
            msg = f"[Order context: {req.context}]\n{msg}"

        if sid not in chat_sessions:
            system = CALL_SYSTEM_PROMPT if req.is_call else SYSTEM_PROMPT
            chat = LlmChat(
                api_key=EMERGENT_LLM_KEY,
                session_id=sid,
                system_message=system
            )
            chat.with_model("anthropic", "claude-haiku-4-5-20251001")
            chat_sessions[sid] = chat

        response = await chat_sessions[sid].send_message(UserMessage(text=msg))
        return {"reply": response}
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/chat/reset")
async def reset_chat(session_id: str = ""):
    if session_id in chat_sessions:
        del chat_sessions[session_id]
    return {"status": "reset"}


@api_router.post("/tts")
async def tts_endpoint(req: TTSRequest):
    try:
        text = req.text
        voice_id = req.voice_id or EL_DEFAULT_VOICE

        clean = re.sub(r'[\U0001F300-\U0001FFFF]', '', text)
        clean = re.sub(r'[—]', ', ', clean)
        clean = re.sub(r'[•\n]', ' ', clean)
        clean = re.sub(r'  +', ' ', clean).strip()

        if not clean:
            raise HTTPException(status_code=400, detail="Empty text after cleaning")

        primed_text = '\u091C\u0940\u0964 ' + clean

        async with httpx.AsyncClient(timeout=30.0) as http_client:
            response = await http_client.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                json={
                    "text": primed_text,
                    "model_id": "eleven_multilingual_v2",
                    "voice_settings": {
                        "stability": 0.28,
                        "similarity_boost": 0.94,
                        "style": 0.50,
                        "use_speaker_boost": True
                    }
                },
                headers={
                    "xi-api-key": EL_API_KEY,
                    "Content-Type": "application/json",
                    "Accept": "audio/mpeg"
                }
            )

            if response.status_code != 200:
                logger.error(f"ElevenLabs error: {response.status_code} {response.text[:300]}")
                raise HTTPException(status_code=500, detail="TTS generation failed")

            return Response(content=response.content, media_type="audio/mpeg")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TTS error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@app.on_event("shutdown")
async def shutdown_db_client():
    mongo_client.close()
