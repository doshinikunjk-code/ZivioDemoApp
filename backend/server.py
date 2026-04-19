"""Zivio AI backend — thin app factory.

All business logic lives under routes/. Shared infra in core.py / models.py.
"""
from fastapi import APIRouter, FastAPI
from starlette.middleware.cors import CORSMiddleware

from core import CORS_ORIGINS, logger, mongo_client
from routes import alerts, analytics, chat, health, orders, restaurant, reviews, tts, voice_ivr, whatsapp
from seed import seed_default_restaurant

app = FastAPI(title="Zivio AI", version="1.0.0")

api_router = APIRouter(prefix="/api")
for module in (health, restaurant, chat, tts, orders, whatsapp, alerts, voice_ivr, reviews, analytics):
    api_router.include_router(module.router)

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def _startup() -> None:
    await seed_default_restaurant()
    logger.info("Zivio AI backend started")


@app.on_event("shutdown")
async def _shutdown() -> None:
    mongo_client.close()
