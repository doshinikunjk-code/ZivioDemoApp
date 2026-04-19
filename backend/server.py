from fastapi import FastAPI, APIRouter, Response, HTTPException, Request
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import re
import httpx
import uuid
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone
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
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_WHATSAPP_NUMBER = os.environ.get('TWILIO_WHATSAPP_NUMBER')

chat_sessions = {}

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# MODELS
# ═══════════════════════════════════════════════════════════════

class MenuItem(BaseModel):
    name: str
    price: float
    category: str = "main"

class RestaurantConfig(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Desi Road Restaurant"
    tagline: str = "Elevated Indian Cuisine"
    city: str = "Brampton"
    logo_url: str = "https://desiroad.ca/wp-content/uploads/2016/10/DESI-ROAD-LOGO-1.jpg"
    phone: str = "(289) 499-1000"
    location: str = "185 Fletchers Creek Blvd or 100 Peel Centre Dr, Brampton"
    hours: str = "Mon-Sat 11am-11pm, Sun 12pm-10pm"
    menu: List[MenuItem] = []
    special_name: str = "Shahi Lamb Chops"
    special_desc: str = "discounted price"
    brand_tagline: str = "Desi Daru Desi Khana"
    languages: List[str] = ["en", "pa", "hi"]
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_number: str = ""
    kitchen_phone: str = ""
    reception_phone: str = ""
    google_place_id: str = ""
    google_review_url: str = ""
    monthly_price: str = "$799"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class OrderCreate(BaseModel):
    restaurant_id: str = "default"
    items: List[str]
    session_id: str = ""
    language: str = "auto"
    customer_phone: str = ""
    customer_name: str = ""

class ChatRequest(BaseModel):
    session_id: str
    message: str
    context: Optional[str] = None
    lang: Optional[str] = 'auto'
    is_call: Optional[bool] = False
    restaurant_id: Optional[str] = "default"

class TTSRequest(BaseModel):
    text: str
    voice_id: Optional[str] = None
    lang: Optional[str] = 'auto'
    restaurant_id: Optional[str] = 'default'

class WhatsAppMessage(BaseModel):
    to: str
    message: str
    restaurant_id: str = "default"

class ReviewRequest(BaseModel):
    order_id: str
    customer_phone: str
    restaurant_id: str = "default"

class AnalyticsEvent(BaseModel):
    restaurant_id: str = "default"
    event_type: str
    metadata: dict = {}

# ═══════════════════════════════════════════════════════════════
# SEED DEFAULT RESTAURANT
# ═══════════════════════════════════════════════════════════════

DEFAULT_MENU = [
    MenuItem(name="Butter Chicken Cones", price=16.99, category="main"),
    MenuItem(name="Shahi Lamb Chops", price=29.99, category="main"),
    MenuItem(name="Dal Makhani", price=15.99, category="main"),
    MenuItem(name="Palak Paneer", price=14.99, category="main"),
    MenuItem(name="Raj Kachori", price=12.99, category="starter"),
    MenuItem(name="Paneer Hardshell Tacos", price=13.99, category="main"),
    MenuItem(name="Chicken Tikka", price=16.99, category="main"),
    MenuItem(name="Chicken Biryani", price=18.99, category="main"),
    MenuItem(name="Seekh Kebab", price=15.99, category="main"),
    MenuItem(name="Garlic Naan", price=3.99, category="bread"),
    MenuItem(name="Butter Naan", price=3.49, category="bread"),
    MenuItem(name="Mango Lassi", price=5.99, category="drink"),
    MenuItem(name="Masala Chai", price=3.99, category="drink"),
    MenuItem(name="Gulab Jamun", price=6.99, category="dessert"),
    MenuItem(name="Kulfi Falooda", price=7.99, category="dessert"),
]

async def seed_default_restaurant():
    existing = await db.restaurants.find_one({"id": "default"}, {"_id": 0})
    if not existing:
        config = RestaurantConfig(id="default", menu=DEFAULT_MENU)
        await db.restaurants.insert_one(config.model_dump())
        logger.info("Seeded default Desi Road restaurant config")

@app.on_event("startup")
async def startup():
    await seed_default_restaurant()

# ═══════════════════════════════════════════════════════════════
# DYNAMIC SYSTEM PROMPT BUILDER
# ═══════════════════════════════════════════════════════════════

def build_system_prompt(config: dict, is_call: bool = False) -> str:
    name = config.get("name", "Desi Road")
    menu_items = config.get("menu", [])
    menu_str = ", ".join([f"{m['name']} ${m['price']}" for m in menu_items])
    location = config.get("location", "")
    phone = config.get("phone", "")
    hours = config.get("hours", "")
    special = config.get("special_name", "")
    special_desc = config.get("special_desc", "")

    if is_call:
        return f"""You answer phone calls at {name} {config.get('city','')}. You are Riya, a warm local team member. NOT AI.
1-2 sentences max. Match caller's language exactly — Punjabi, Hindi, or English. Natural, warm, conversational.
Sound like a real person — vary your tone. Sometimes short "Got it!", sometimes warm "That's our bestseller, great pick!"
NEVER say "ji" or "hey" repeatedly. Talk like a real young person would.
Take orders. Answer anything. NEVER restart if second person talks — continue the same order.
MENU: {menu_str}
HOURS: {hours} | LOCATION: {location} | PHONE: {phone}
Tonight's Special: {special} ({special_desc})"""

    return f"""You are the AI ordering assistant at {name}, {config.get('city','')}, Ontario. You handle WhatsApp and phone orders.

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


# ═══════════════════════════════════════════════════════════════
# RESTAURANT CONFIG CRUD
# ═══════════════════════════════════════════════════════════════

@api_router.get("/")
async def root():
    return {"message": "Zivio AI Backend Active"}

@api_router.get("/restaurant/{restaurant_id}")
async def get_restaurant(restaurant_id: str = "default"):
    config = await db.restaurants.find_one({"id": restaurant_id}, {"_id": 0})
    if not config:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    safe = {k: v for k, v in config.items() if k not in ["twilio_auth_token"]}
    return safe

@api_router.get("/restaurants")
async def list_restaurants():
    configs = await db.restaurants.find({}, {"_id": 0, "twilio_auth_token": 0}).to_list(100)
    return configs

@api_router.post("/restaurant")
async def create_restaurant(config: RestaurantConfig):
    config.created_at = datetime.now(timezone.utc).isoformat()
    await db.restaurants.insert_one(config.model_dump())
    await track_event(config.id, "restaurant_created", {"name": config.name})
    return {"id": config.id, "status": "created"}

@api_router.put("/restaurant/{restaurant_id}")
async def update_restaurant(restaurant_id: str, updates: dict):
    updates.pop("_id", None)
    updates.pop("id", None)
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.restaurants.update_one({"id": restaurant_id}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    if restaurant_id in chat_sessions:
        del chat_sessions[restaurant_id]
    # Clear all chat sessions so AI picks up new config
    chat_sessions.clear()
    await track_event(restaurant_id, "restaurant_updated", {"fields": list(updates.keys())})
    return {"status": "updated"}


# ═══════════════════════════════════════════════════════════════
# CHAT (Dynamic Restaurant Config)
# ═══════════════════════════════════════════════════════════════

@api_router.post("/chat")
async def chat_endpoint(req: ChatRequest):
    try:
        sid = req.session_id
        msg = req.message
        rid = req.restaurant_id or "default"

        config = await db.restaurants.find_one({"id": rid}, {"_id": 0})
        if not config:
            config = await db.restaurants.find_one({"id": "default"}, {"_id": 0})

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
            system = build_system_prompt(config, is_call=req.is_call)
            chat = LlmChat(
                api_key=EMERGENT_LLM_KEY,
                session_id=sid,
                system_message=system
            )
            chat.with_model("anthropic", "claude-haiku-4-5-20251001")
            chat_sessions[sid] = chat
            await track_event(rid, "conversation_started", {"session_id": sid, "is_call": req.is_call})

        response = await chat_sessions[sid].send_message(UserMessage(text=msg))
        await track_event(rid, "message_exchanged", {"session_id": sid})
        return {"reply": response}
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/chat/reset")
async def reset_chat(session_id: str = ""):
    if session_id in chat_sessions:
        del chat_sessions[session_id]
    return {"status": "reset"}


# ═══════════════════════════════════════════════════════════════
# TTS (ElevenLabs)
# ═══════════════════════════════════════════════════════════════

@api_router.post("/tts")
async def tts_endpoint(req: TTSRequest):
    try:
        text = req.text
        voice_id = req.voice_id or EL_DEFAULT_VOICE

        # Check for language-specific voice from restaurant config
        if req.restaurant_id and req.lang and req.lang != 'auto':
            config = await db.restaurants.find_one({"id": req.restaurant_id}, {"_id": 0})
            if config:
                voice_map = config.get("voice_ids", {})
                if req.lang in voice_map and voice_map[req.lang]:
                    voice_id = voice_map[req.lang]

        clean = re.sub(r'[\U0001F300-\U0001FFFF]', '', text)
        clean = re.sub(r'[—]', ', ', clean)
        clean = re.sub(r'[•\n]', ' ', clean)
        clean = re.sub(r'[\U0000FE00-\U0000FE0F]', '', clean)
        clean = re.sub(r'[\U0000200D]', '', clean)
        clean = re.sub(r'  +', ' ', clean).strip()
        if not clean:
            raise HTTPException(status_code=400, detail="Empty text")
        async with httpx.AsyncClient(timeout=30.0) as http_client:
            response = await http_client.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                json={
                    "text": clean,
                    "model_id": "eleven_multilingual_v2",
                    "voice_settings": {"stability": 0.50, "similarity_boost": 0.90, "style": 0.30, "use_speaker_boost": True}
                },
                headers={"xi-api-key": EL_API_KEY, "Content-Type": "application/json", "Accept": "audio/mpeg"}
            )
            if response.status_code != 200:
                logger.error(f"EL error: {response.status_code} {response.text[:300]}")
                raise HTTPException(status_code=500, detail="TTS failed")
            return Response(content=response.content, media_type="audio/mpeg")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TTS error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════
# ORDER MANAGEMENT
# ═══════════════════════════════════════════════════════════════

@api_router.post("/orders")
async def create_order(order: OrderCreate):
    order_id = "DR-" + str(uuid.uuid4())[:6].upper()
    doc = {
        "id": order_id,
        "restaurant_id": order.restaurant_id,
        "items": order.items,
        "session_id": order.session_id,
        "language": order.language,
        "customer_phone": order.customer_phone,
        "customer_name": order.customer_name,
        "status": "confirmed",
        "kitchen_alerted": False,
        "reception_alerted": False,
        "review_requested": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.orders.insert_one(doc)
    await track_event(order.restaurant_id, "order_placed", {"order_id": order_id, "items_count": len(order.items)})

    config = await db.restaurants.find_one({"id": order.restaurant_id}, {"_id": 0})
    if config:
        await send_kitchen_alert(config, doc)
        await send_reception_alert(config, doc)

    return {"order_id": order_id, "status": "confirmed"}

@api_router.get("/orders")
async def get_orders(restaurant_id: str = "default", limit: int = 50):
    orders = await db.orders.find(
        {"restaurant_id": restaurant_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(limit)
    return orders

@api_router.put("/orders/{order_id}/status")
async def update_order_status(order_id: str, status: str):
    result = await db.orders.update_one(
        {"id": order_id},
        {"$set": {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Order not found")

    if status == "ready":
        order = await db.orders.find_one({"id": order_id}, {"_id": 0})
        if order and order.get("customer_phone"):
            config = await db.restaurants.find_one({"id": order["restaurant_id"]}, {"_id": 0})
            if config:
                rname = config.get("name", "the restaurant")
                await send_whatsapp(config, order["customer_phone"],
                    f"Namaste ji! Your order {order_id} is ready for pickup at {rname}. See you soon!")

    return {"status": "updated"}


# ═══════════════════════════════════════════════════════════════
# TWILIO WHATSAPP (Ready-to-Connect)
# ═══════════════════════════════════════════════════════════════

async def get_twilio_client(config: dict):
    sid = config.get("twilio_account_sid") or TWILIO_ACCOUNT_SID
    token = config.get("twilio_auth_token") or TWILIO_AUTH_TOKEN
    wa_num = config.get("twilio_whatsapp_number") or TWILIO_WHATSAPP_NUMBER
    if not sid or not token or not wa_num:
        return None, None
    try:
        from twilio.rest import Client
        return Client(sid, token), wa_num
    except Exception as e:
        logger.error(f"Twilio init error: {e}")
        return None, None

async def send_whatsapp(config: dict, to_number: str, message: str):
    client, from_number = await get_twilio_client(config)
    if not client:
        logger.info(f"WhatsApp not configured. Would send to {to_number}: {message}")
        return False
    try:
        to_wa = f"whatsapp:{to_number}" if not to_number.startswith("whatsapp:") else to_number
        from_wa = f"whatsapp:{from_number}" if not from_number.startswith("whatsapp:") else from_number
        msg = client.messages.create(body=message, from_=from_wa, to=to_wa)
        logger.info(f"WhatsApp sent: {msg.sid}")
        return True
    except Exception as e:
        logger.error(f"WhatsApp send error: {e}")
        return False

@api_router.post("/whatsapp/send")
async def send_whatsapp_endpoint(req: WhatsAppMessage):
    config = await db.restaurants.find_one({"id": req.restaurant_id}, {"_id": 0})
    if not config:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    success = await send_whatsapp(config, req.to, req.message)
    await track_event(req.restaurant_id, "whatsapp_sent", {"to": req.to, "success": success})
    return {"sent": success}

@api_router.post("/whatsapp/webhook")
async def whatsapp_webhook(request: Request):
    form = await request.form()
    from_number = form.get("From", "")
    body = form.get("Body", "")
    to_number = form.get("To", "")
    logger.info(f"WhatsApp received from {from_number}: {body}")

    config = await db.restaurants.find_one({"id": "default"}, {"_id": 0})
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

@api_router.get("/whatsapp/status")
async def whatsapp_status(restaurant_id: str = "default"):
    config = await db.restaurants.find_one({"id": restaurant_id}, {"_id": 0})
    if not config:
        return {"configured": False}
    sid = config.get("twilio_account_sid") or TWILIO_ACCOUNT_SID
    token = config.get("twilio_auth_token") or TWILIO_AUTH_TOKEN
    wa = config.get("twilio_whatsapp_number") or TWILIO_WHATSAPP_NUMBER
    return {"configured": bool(sid and token and wa), "whatsapp_number": wa or ""}


# ═══════════════════════════════════════════════════════════════
# KITCHEN & RECEPTION ALERTS
# ═══════════════════════════════════════════════════════════════

async def send_kitchen_alert(config: dict, order: dict):
    kitchen_phone = config.get("kitchen_phone", "")
    if not kitchen_phone:
        logger.info(f"Kitchen phone not configured. Order: {order['id']}")
        return
    items_str = "\n".join([f"  • {item}" for item in order["items"]])
    rname = config.get("name", "Restaurant")
    message = f"🔔 NEW ORDER — {rname}\nOrder: {order['id']}\n{items_str}\nPickup · ~20 mins\n⏰ {datetime.now(timezone.utc).strftime('%I:%M %p')}"
    sent = await send_whatsapp(config, kitchen_phone, message)
    if sent:
        await db.orders.update_one({"id": order["id"]}, {"$set": {"kitchen_alerted": True}})
        await track_event(config.get("id", "default"), "kitchen_alert_sent", {"order_id": order["id"]})

async def send_reception_alert(config: dict, order: dict):
    reception_phone = config.get("reception_phone", "")
    if not reception_phone:
        logger.info(f"Reception phone not configured. Order: {order['id']}")
        return
    items_str = ", ".join(order["items"])
    rname = config.get("name", "Restaurant")
    customer = order.get("customer_name", "Walk-in")
    message = f"📋 {rname} — New order {order['id']}\nCustomer: {customer}\nItems: {items_str}\nStatus: Confirmed"
    sent = await send_whatsapp(config, reception_phone, message)
    if sent:
        await db.orders.update_one({"id": order["id"]}, {"$set": {"reception_alerted": True}})
        await track_event(config.get("id", "default"), "reception_alert_sent", {"order_id": order["id"]})

@api_router.post("/alerts/kitchen/test")
async def test_kitchen_alert(restaurant_id: str = "default"):
    config = await db.restaurants.find_one({"id": restaurant_id}, {"_id": 0})
    if not config:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    test_order = {"id": "TEST-001", "items": ["Butter Chicken Cones", "Garlic Naan", "Mango Lassi"], "customer_name": "Test Customer"}
    await send_kitchen_alert(config, test_order)
    return {"status": "test_sent"}

@api_router.post("/alerts/reception/test")
async def test_reception_alert(restaurant_id: str = "default"):
    config = await db.restaurants.find_one({"id": restaurant_id}, {"_id": 0})
    if not config:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    test_order = {"id": "TEST-001", "items": ["Butter Chicken Cones", "Garlic Naan"], "customer_name": "Test Customer"}
    await send_reception_alert(config, test_order)
    return {"status": "test_sent"}


# ═══════════════════════════════════════════════════════════════
# GOOGLE REVIEW AUTOMATION
# ═══════════════════════════════════════════════════════════════

@api_router.post("/reviews/request")
async def request_review(req: ReviewRequest):
    config = await db.restaurants.find_one({"id": req.restaurant_id}, {"_id": 0})
    if not config:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    rname = config.get("name", "the restaurant")
    review_url = config.get("google_review_url", "")
    place_id = config.get("google_place_id", "")
    if not review_url and place_id:
        review_url = f"https://search.google.com/local/writereview?placeid={place_id}"
    message = (f"Namaste ji! 🙏 Thank you for ordering from {rname}. "
               f"We hope you loved your food! If you have a moment, please leave us a review — it means the world to us. "
               f"{review_url}" if review_url else
               f"Namaste ji! 🙏 Thank you for ordering from {rname}. We hope you loved your food!")
    sent = await send_whatsapp(config, req.customer_phone, message)
    if sent:
        await db.orders.update_one({"id": req.order_id}, {"$set": {"review_requested": True}})
    await track_event(req.restaurant_id, "review_requested", {"order_id": req.order_id, "sent": sent})
    return {"sent": sent, "review_url": review_url}

@api_router.post("/reviews/schedule")
async def schedule_review_for_order(order_id: str):
    order = await db.orders.find_one({"id": order_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if not order.get("customer_phone"):
        return {"status": "no_phone", "message": "No customer phone on order"}
    if order.get("review_requested"):
        return {"status": "already_requested"}
    config = await db.restaurants.find_one({"id": order["restaurant_id"]}, {"_id": 0})
    if not config:
        return {"status": "no_config"}
    rname = config.get("name", "the restaurant")
    review_url = config.get("google_review_url", "")
    place_id = config.get("google_place_id", "")
    if not review_url and place_id:
        review_url = f"https://search.google.com/local/writereview?placeid={place_id}"
    msg = f"Shukriya ji! 🙏 Hope you enjoyed your meal from {rname}. A quick review would make our day: {review_url}" if review_url else f"Shukriya ji! Hope you enjoyed {rname}! 🙏"
    sent = await send_whatsapp(config, order["customer_phone"], msg)
    if sent:
        await db.orders.update_one({"id": order_id}, {"$set": {"review_requested": True}})
    return {"sent": sent}


# ═══════════════════════════════════════════════════════════════
# ANALYTICS
# ═══════════════════════════════════════════════════════════════

async def track_event(restaurant_id: str, event_type: str, metadata: dict = None):
    doc = {
        "id": str(uuid.uuid4()),
        "restaurant_id": restaurant_id,
        "event_type": event_type,
        "metadata": metadata or {},
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.analytics.insert_one(doc)

@api_router.post("/analytics/track")
async def track_analytics(event: AnalyticsEvent):
    await track_event(event.restaurant_id, event.event_type, event.metadata)
    return {"status": "tracked"}

@api_router.get("/analytics/summary")
async def get_analytics_summary(restaurant_id: str = "default"):
    total_orders = await db.orders.count_documents({"restaurant_id": restaurant_id})
    conversations = await db.analytics.count_documents({"restaurant_id": restaurant_id, "event_type": "conversation_started"})
    messages = await db.analytics.count_documents({"restaurant_id": restaurant_id, "event_type": "message_exchanged"})
    wa_sent = await db.analytics.count_documents({"restaurant_id": restaurant_id, "event_type": "whatsapp_sent"})
    reviews = await db.analytics.count_documents({"restaurant_id": restaurant_id, "event_type": "review_requested"})
    kitchen_alerts = await db.analytics.count_documents({"restaurant_id": restaurant_id, "event_type": "kitchen_alert_sent"})

    orders = await db.orders.find({"restaurant_id": restaurant_id}, {"_id": 0}).sort("created_at", -1).to_list(10)
    revenue_est = 0
    for o in await db.orders.find({"restaurant_id": restaurant_id}, {"_id": 0, "items": 1}).to_list(1000):
        revenue_est += len(o.get("items", [])) * 15

    by_lang = {}
    pipeline = [
        {"$match": {"restaurant_id": restaurant_id}},
        {"$group": {"_id": "$language", "count": {"$sum": 1}}}
    ]
    async for doc in db.orders.aggregate(pipeline):
        by_lang[doc["_id"] or "auto"] = doc["count"]

    return {
        "total_orders": total_orders,
        "conversations": conversations,
        "messages": messages,
        "whatsapp_sent": wa_sent,
        "reviews_requested": reviews,
        "kitchen_alerts": kitchen_alerts,
        "revenue_estimate": revenue_est,
        "orders_by_language": by_lang,
        "recent_orders": orders
    }

@api_router.get("/analytics/events")
async def get_analytics_events(restaurant_id: str = "default", event_type: str = "", limit: int = 50):
    query = {"restaurant_id": restaurant_id}
    if event_type:
        query["event_type"] = event_type
    events = await db.analytics.find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)
    return events


# ═══════════════════════════════════════════════════════════════
# MIDDLEWARE & SHUTDOWN
# ═══════════════════════════════════════════════════════════════

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    mongo_client.close()
