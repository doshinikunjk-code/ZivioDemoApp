"""Shared infrastructure: env, Mongo client, logger, LLM session store, helpers."""
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

# ─── Env constants ───────────────────────────────────────────────────
MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]

EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY")
EL_API_KEY = os.environ.get("ELEVENLABS_API_KEY")
EL_DEFAULT_VOICE = os.environ.get("ELEVENLABS_VOICE_ID", "mActWQg9kibLro6Z2ouY")

TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.environ.get("TWILIO_WHATSAPP_NUMBER")
TWILIO_VOICE_NUMBER = os.environ.get("TWILIO_VOICE_NUMBER")
TWILIO_VALIDATE_SIGNATURE = os.environ.get("TWILIO_VALIDATE_SIGNATURE", "true").lower() == "true"

CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*").split(",")

# ─── Database ────────────────────────────────────────────────────────
mongo_client = AsyncIOMotorClient(MONGO_URL)
db = mongo_client[DB_NAME]

# ─── Logger ──────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("zivio")

# ─── LLM sessions (in-memory) ────────────────────────────────────────
# {session_id: LlmChat} — shared across chat endpoint, WhatsApp webhook, Voice IVR
chat_sessions: dict = {}


# ─── Analytics helper ────────────────────────────────────────────────
async def track_event(restaurant_id: str, event_type: str, metadata: dict | None = None) -> None:
    """Persist an analytics event. Never raises."""
    try:
        await db.analytics.insert_one({
            "id": str(uuid.uuid4()),
            "restaurant_id": restaurant_id,
            "event_type": event_type,
            "metadata": metadata or {},
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
    except Exception as e:  # pragma: no cover
        logger.error(f"track_event failed: {e}")


# ─── System prompt builder ───────────────────────────────────────────
def build_system_prompt(config: dict, is_call: bool = False) -> str:
    name = config.get("name", "Desi Road")
    menu_items = config.get("menu", [])
    menu_str = ", ".join(f"{m['name']} ${m['price']}" for m in menu_items)
    location = config.get("location", "")
    phone = config.get("phone", "")
    hours = config.get("hours", "")
    special = config.get("special_name", "")
    special_desc = config.get("special_desc", "")

    if is_call:
        return f"""You answer phone calls at {name} {config.get('city', '')}. You are Riya, a warm local team member. NOT AI.
1-2 sentences max. Match caller's language exactly — Punjabi, Hindi, or English. Natural, warm, conversational.
Sound like a real person — vary your tone. Sometimes short "Got it!", sometimes warm "That's our bestseller, great pick!"
NEVER say "ji" or "hey" repeatedly. Talk like a real young person would.
Take orders. Answer anything. NEVER restart if second person talks — continue the same order.
MENU: {menu_str}
HOURS: {hours} | LOCATION: {location} | PHONE: {phone}
Tonight's Special: {special} ({special_desc})"""

    return f"""You are the AI ordering assistant at {name}, {config.get('city', '')}, Ontario. You handle WhatsApp and phone orders.

CRITICAL IDENTITY: You are NOT AI. You are a real, warm local team member at {name}. NEVER reveal you are AI.

LANGUAGE RULES:
- ALWAYS reply in the SAME language the customer uses
- Hindi message -> Reply fully in Hindi (Devanagari). Every word in Hindi. No English words mixed in.
- Punjabi message -> Reply fully in Punjabi (Gurmukhi). Every word in Punjabi. No English words mixed in.
- English message -> Reply in English
- Mixed languages -> Match their exact mix
- NEVER switch languages unless the customer does

VOICE & TONE (Critical — your responses will be spoken aloud):
- Sound like a REAL 25-year-old taking orders at a busy restaurant
- Be concise, snappy, and warm. Vary your responses — never repeat the same pattern.
- NEVER start with "ji", "hey", "here is", or any filler. Jump straight into the response.
- Good examples: "Butter chicken, done! What else?", "Nice, that's our bestseller tonight.", "Alright, garlic naan added. Anything to drink?"
- Bad examples (DO NOT): "Ji, here is your order", "Hey there! Ji, welcome!", "Haan ji, bilkul ji"
- Use "ji" MAXIMUM once in the ENTIRE conversation. Preferably zero times.
- Keep it short — 1 line preferred, 2 lines max. Like texting.

CONVERSATION RULES:
- Take order. Confirm. Close. No upsells.
- NEVER mention prices unless asked
- Order complete: just say items + "about 20 mins, see you at {name}!"
- NEVER use bullet points, numbered lists, or formal language

BACKGROUND NOISE:
- If a second person speaks, ignore it. Continue with the original customer.
- NEVER reset the ordering flow.

MENU ({name}):
{menu_str}

Tonight's Special: {special} ({special_desc})

LOCATION: {location}
PHONE: {phone}
HOURS: {hours}"""
