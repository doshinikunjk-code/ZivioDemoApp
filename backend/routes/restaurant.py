from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from core import chat_sessions, db, track_event
from models import RestaurantConfig

router = APIRouter()


@router.get("/restaurant/{restaurant_id}")
async def get_restaurant(restaurant_id: str = "default"):
    config = await db.restaurants.find_one({"id": restaurant_id}, {"_id": 0})
    if not config:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return {k: v for k, v in config.items() if k not in ("twilio_auth_token",)}


@router.get("/restaurants")
async def list_restaurants():
    return await db.restaurants.find({}, {"_id": 0, "twilio_auth_token": 0}).to_list(100)


@router.post("/restaurant")
async def create_restaurant(config: RestaurantConfig):
    config.created_at = datetime.now(timezone.utc).isoformat()
    await db.restaurants.insert_one(config.model_dump())
    await track_event(config.id, "restaurant_created", {"name": config.name})
    return {"id": config.id, "status": "created"}


@router.put("/restaurant/{restaurant_id}")
async def update_restaurant(restaurant_id: str, updates: dict):
    updates.pop("_id", None)
    updates.pop("id", None)
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.restaurants.update_one({"id": restaurant_id}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    # Clear all chat sessions so the AI re-builds its system prompt with the new config
    chat_sessions.clear()
    await track_event(restaurant_id, "restaurant_updated", {"fields": list(updates.keys())})
    return {"status": "updated"}
