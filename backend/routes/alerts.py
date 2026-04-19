from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from core import db, logger, track_event
from twilio_helpers import send_whatsapp

router = APIRouter()


async def send_kitchen_alert(config: dict, order: dict) -> None:
    kitchen_phone = config.get("kitchen_phone", "")
    if not kitchen_phone:
        logger.info(f"Kitchen phone not configured. Order: {order['id']}")
        return
    items_str = "\n".join(f"  • {item}" for item in order["items"])
    rname = config.get("name", "Restaurant")
    message = (
        f"🔔 NEW ORDER — {rname}\nOrder: {order['id']}\n{items_str}\n"
        f"Pickup · ~20 mins\n⏰ {datetime.now(timezone.utc).strftime('%I:%M %p')}"
    )
    sent = await send_whatsapp(config, kitchen_phone, message)
    if sent:
        await db.orders.update_one({"id": order["id"]}, {"$set": {"kitchen_alerted": True}})
        await track_event(config.get("id", "default"), "kitchen_alert_sent", {"order_id": order["id"]})


async def send_reception_alert(config: dict, order: dict) -> None:
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


@router.post("/alerts/kitchen/test")
async def test_kitchen_alert(restaurant_id: str = "default"):
    config = await db.restaurants.find_one({"id": restaurant_id}, {"_id": 0})
    if not config:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    test_order = {"id": "TEST-001", "items": ["Butter Chicken Cones", "Garlic Naan", "Mango Lassi"], "customer_name": "Test Customer"}
    await send_kitchen_alert(config, test_order)
    return {"status": "test_sent"}


@router.post("/alerts/reception/test")
async def test_reception_alert(restaurant_id: str = "default"):
    config = await db.restaurants.find_one({"id": restaurant_id}, {"_id": 0})
    if not config:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    test_order = {"id": "TEST-001", "items": ["Butter Chicken Cones", "Garlic Naan"], "customer_name": "Test Customer"}
    await send_reception_alert(config, test_order)
    return {"status": "test_sent"}
