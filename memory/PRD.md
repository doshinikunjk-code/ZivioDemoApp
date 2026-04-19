# Zivio AI PRD — Updated 2026-02-XX (Phase 9)

## Original Problem
Professional multi-industry Voice AI ordering demo (Desi Road restaurant base, extended to Dentist, Pharmacy, Pizza, Doctor, Skilled Trades) for pitching Brampton businesses. Supports English / Hindi / Punjabi with human-like tone, WhatsApp ordering, live **Twilio phone-call IVR**, kitchen alerts, admin panel, analytics. ElevenLabs TTS + Claude Haiku 4.5 via Emergent LLM key.

## All Phases Complete (100% test pass each)
- **Phase 1**: Core MVP — chat, TTS, orders
- **Phase 2**: Admin Panel, WhatsApp stub, Alerts, Analytics
- **Phase 3**: Custom Demo Bar, Polish
- **Phase 4**: Voice fix — removed "ji" primer, echo fix, faster + natural voice
- **Phase 5**: Phone (437) 331-5615, per-language voice IDs, Punjabi voice clone support
- **Phase 6**: Multi-industry prototype switcher (6 templates)
- **Phase 7**: VAD noise-filter + unified $599 pricing
- **Phase 8**: Twilio Voice IVR + double-read fix + expressive voice tuning
- **Phase 9**: TTS hash-cache + X-Twilio-Signature validation + server.py refactor ← current

## Phase 9 Details (shipped today)
### 1. Refactor: monolithic server.py (905 lines) → modular routers
```
/app/backend/
├── server.py           (37 lines — thin app factory)
├── core.py             (env, db, logger, chat_sessions, build_system_prompt, track_event)
├── models.py           (all Pydantic models)
├── seed.py             (DEFAULT_MENU + startup seeder)
├── twilio_helpers.py   (Twilio client + send_whatsapp + validate_twilio_signature)
└── routes/
    ├── __init__.py
    ├── health.py
    ├── restaurant.py
    ├── chat.py
    ├── tts.py          (with hash-cache — see #2)
    ├── orders.py
    ├── whatsapp.py     (webhook validates signature)
    ├── alerts.py
    ├── voice_ivr.py    (webhook validates signature)
    ├── reviews.py
    └── analytics.py
```
Zero behavior change. 57/57 tests pass (26 new + 31 regression).

### 2. TTS hash-cache on `/api/tts`
- Key = `sha256(clean_text | voice_id | model_id)`
- Storage: `OrderedDict` with LRU eviction — 300 entries, 600s TTL
- Response headers: `X-Cache: HIT | MISS` for observability
- Saves ElevenLabs quota when users tap "Listen" multiple times, or when same greeting/menu response replays.

### 3. X-Twilio-Signature validation on inbound webhooks
- `twilio_helpers.validate_twilio_signature(request, config)` — uses `twilio.request_validator.RequestValidator`
- URL reconstruction honors `x-forwarded-proto` / `x-forwarded-host` (Kubernetes ingress behind proxy)
- Applied to: `/api/webhook/twilio/voice`, `/api/webhook/twilio/voice/respond`, `/api/whatsapp/webhook`
- Env toggle: `TWILIO_VALIDATE_SIGNATURE=false` to disable (default true)
- Dev-mode behavior: no auth token → logs `WARNING: Twilio signature validation SKIPPED — no auth token configured (dev mode)` and proceeds. Prod ready.

## Backlog (prioritized)
- **P1** Real Google Review automation via Place ID (currently UI-only stub)
- **P2** LRU eviction for `chat_sessions` dict (unbounded memory growth on long uptime)
- **P2** Daily WhatsApp campaign scheduler
- **P2** Multi-tenant live support (multiple real restaurants in parallel)
- **P3** Post-call WhatsApp reorder link ("Tap to reorder the same in 2 clicks" — Brampton pitch enhancer)
- **P3** Polly fallback logging warn when used for Punjabi (currently silent)

## Twilio setup user must complete to go live
User owns Twilio voice-enabled number **+1 437 523 6468**.
1. Add `TWILIO_ACCOUNT_SID` + `TWILIO_AUTH_TOKEN` to `/app/backend/.env` (shared with WhatsApp).
2. Twilio Console → Phone Numbers → +1 437 523 6468 → **A CALL COMES IN** → Webhook → `https://voice-order-hub-2.preview.emergentagent.com/api/webhook/twilio/voice` (POST).
3. Dial the number.

Signature validation activates automatically once `TWILIO_AUTH_TOKEN` is set.

## Known: ElevenLabs supports Punjabi but needs a voice clone for native pronunciation. User can clone on ElevenLabs and paste voice IDs per language in Admin → Voice Configuration.
