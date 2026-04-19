"""Pydantic request/response models."""
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field


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
    twilio_voice_number: str = ""
    kitchen_phone: str = ""
    reception_phone: str = ""
    google_place_id: str = ""
    google_review_url: str = ""
    monthly_price: str = "$599"
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
    lang: Optional[str] = "auto"
    is_call: Optional[bool] = False
    restaurant_id: Optional[str] = "default"


class TTSRequest(BaseModel):
    text: str
    voice_id: Optional[str] = None
    lang: Optional[str] = "auto"
    restaurant_id: Optional[str] = "default"


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
