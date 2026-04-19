from fastapi import APIRouter

from core import db, track_event
from models import AnalyticsEvent

router = APIRouter()


@router.post("/analytics/track")
async def track_analytics(event: AnalyticsEvent):
    await track_event(event.restaurant_id, event.event_type, event.metadata)
    return {"status": "tracked"}


@router.get("/analytics/summary")
async def get_analytics_summary(restaurant_id: str = "default"):
    total_orders = await db.orders.count_documents({"restaurant_id": restaurant_id})
    conversations = await db.analytics.count_documents({"restaurant_id": restaurant_id, "event_type": "conversation_started"})
    messages = await db.analytics.count_documents({"restaurant_id": restaurant_id, "event_type": "message_exchanged"})
    wa_sent = await db.analytics.count_documents({"restaurant_id": restaurant_id, "event_type": "whatsapp_sent"})
    reviews = await db.analytics.count_documents({"restaurant_id": restaurant_id, "event_type": "review_requested"})
    kitchen_alerts = await db.analytics.count_documents({"restaurant_id": restaurant_id, "event_type": "kitchen_alert_sent"})

    orders = await db.orders.find({"restaurant_id": restaurant_id}, {"_id": 0}).sort("created_at", -1).to_list(10)
    revenue_est = 0
    async for o in db.orders.find({"restaurant_id": restaurant_id}, {"_id": 0, "items": 1}):
        revenue_est += len(o.get("items", [])) * 15

    by_lang: dict = {}
    async for doc in db.orders.aggregate([
        {"$match": {"restaurant_id": restaurant_id}},
        {"$group": {"_id": "$language", "count": {"$sum": 1}}},
    ]):
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
        "recent_orders": orders,
    }


@router.get("/analytics/events")
async def get_analytics_events(restaurant_id: str = "default", event_type: str = "", limit: int = 50):
    query = {"restaurant_id": restaurant_id}
    if event_type:
        query["event_type"] = event_type
    return await db.analytics.find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)
