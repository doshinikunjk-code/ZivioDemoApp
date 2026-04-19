from fastapi import APIRouter, HTTPException

from core import db, track_event
from models import ReviewRequest
from twilio_helpers import send_whatsapp

router = APIRouter()


def _review_url(config: dict) -> str:
    url = config.get("google_review_url", "")
    pid = config.get("google_place_id", "")
    if not url and pid:
        url = f"https://search.google.com/local/writereview?placeid={pid}"
    return url


@router.post("/reviews/request")
async def request_review(req: ReviewRequest):
    config = await db.restaurants.find_one({"id": req.restaurant_id}, {"_id": 0})
    if not config:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    rname = config.get("name", "the restaurant")
    review_url = _review_url(config)
    message = (
        f"Namaste ji! 🙏 Thank you for ordering from {rname}. We hope you loved your food! "
        f"If you have a moment, please leave us a review — it means the world to us. {review_url}"
        if review_url
        else f"Namaste ji! 🙏 Thank you for ordering from {rname}. We hope you loved your food!"
    )
    sent = await send_whatsapp(config, req.customer_phone, message)
    if sent:
        await db.orders.update_one({"id": req.order_id}, {"$set": {"review_requested": True}})
    await track_event(req.restaurant_id, "review_requested", {"order_id": req.order_id, "sent": sent})
    return {"sent": sent, "review_url": review_url}


@router.post("/reviews/schedule")
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
    url = _review_url(config)
    msg = (
        f"Shukriya ji! 🙏 Hope you enjoyed your meal from {rname}. A quick review would make our day: {url}"
        if url
        else f"Shukriya ji! Hope you enjoyed {rname}! 🙏"
    )
    sent = await send_whatsapp(config, order["customer_phone"], msg)
    if sent:
        await db.orders.update_one({"id": order_id}, {"$set": {"review_requested": True}})
    return {"sent": sent}
