import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from core import db, logger, track_event
from models import OrderCreate
from twilio_helpers import send_whatsapp

router = APIRouter()


# Forward declarations — imported lazily to avoid circular imports at module load.
async def _alerts_kitchen(config, doc):
    from routes.alerts import send_kitchen_alert
    await send_kitchen_alert(config, doc)


async def _alerts_reception(config, doc):
    from routes.alerts import send_reception_alert
    await send_reception_alert(config, doc)


@router.post("/orders")
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
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.orders.insert_one(doc)
    await track_event(order.restaurant_id, "order_placed", {"order_id": order_id, "items_count": len(order.items)})

    config = await db.restaurants.find_one({"id": order.restaurant_id}, {"_id": 0})
    if config:
        await _alerts_kitchen(config, doc)
        await _alerts_reception(config, doc)

    return {"order_id": order_id, "status": "confirmed"}


@router.get("/orders")
async def get_orders(restaurant_id: str = "default", limit: int = 50):
    return await db.orders.find({"restaurant_id": restaurant_id}, {"_id": 0}).sort("created_at", -1).to_list(limit)


@router.put("/orders/{order_id}/status")
async def update_order_status(order_id: str, status: str):
    result = await db.orders.update_one(
        {"id": order_id},
        {"$set": {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Order not found")

    if status == "ready":
        order = await db.orders.find_one({"id": order_id}, {"_id": 0})
        if order and order.get("customer_phone"):
            config = await db.restaurants.find_one({"id": order["restaurant_id"]}, {"_id": 0})
            if config:
                rname = config.get("name", "the restaurant")
                await send_whatsapp(
                    config,
                    order["customer_phone"],
                    f"Namaste ji! Your order {order_id} is ready for pickup at {rname}. See you soon!",
                )
    logger.info(f"Order {order_id} -> status={status}")
    return {"status": "updated"}
