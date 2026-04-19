# Zivio AI PRD — Updated 2026-02-XX (Phase 8)

## Original Problem
Professional multi-industry Voice AI ordering demo (Desi Road restaurant base, extended to Dentist, Pharmacy, Pizza, Doctor, Skilled Trades) for pitching Brampton businesses. Supports English / Hindi / Punjabi with human-like tone, WhatsApp ordering, kitchen alerts, admin panel, analytics, **live phone-call IVR**. ElevenLabs TTS + Claude Haiku 4.5 chat via Emergent LLM key.

## All Phases Complete (100% test pass each)
- **Phase 1**: Core MVP — chat, TTS, orders
- **Phase 2**: Admin Panel, WhatsApp stub, Alerts, Analytics
- **Phase 3**: Custom Demo Bar, Polish
- **Phase 4**: Voice fix — removed "ji" primer, echo fix, faster + natural voice
- **Phase 5**: Phone (437) 331-5615, per-language voice IDs, Punjabi voice clone support
- **Phase 6**: Multi-industry prototype switcher (6 templates)
- **Phase 7**: VAD noise-filter + unified $599 pricing
- **Phase 8**: Twilio Voice IVR + double-read fix + expressive voice tuning ← current

## Phase 8 Details (shipped today)
1. **Twilio Voice IVR (inbound phone calls)** — customer dials the Twilio voice number (+1 437 523 6468) and talks to the AI live:
   - `POST /api/webhook/twilio/voice` — inbound entry; greets caller with ElevenLabs audio + `<Gather input="speech">`.
   - `POST /api/webhook/twilio/voice/respond` — handles each speech turn; forwards SpeechResult to `LlmChat` (Claude Haiku 4.5, `is_call=True` system prompt) and responds with another audio <Play> + <Gather>.
   - `GET /api/tts-cache/{id}.mp3` — one-time serving of ElevenLabs MP3 for Twilio `<Play>` (in-memory OrderedDict with 120s TTL, 200 item cap).
   - `GET /api/voice/status` — admin health check.
   - Polly Neural (Raveena/Aditi) fallback when ElevenLabs fails — keeps Indian accent.
   - Admin Panel → new **Voice IVR** section with status pill + webhook URL instructions.
   - `RestaurantConfig.twilio_voice_number` now persisted.
2. **"Reads twice" bug fix** — root cause was the `speechSynthesis` fallback in `ChatPanel.speak()` firing in parallel with ElevenLabs audio. Fix:
   - Removed the fallback entirely (it was robotic anyway).
   - Added **epoch-based staleness** — each `speak()` bumps an epoch; in-flight stale fetches abort before playback.
   - Added **1.2s text-dedupe** — same text within the window is skipped (absorbs React StrictMode double-effects + `sendMessage` races).
   - Verified via network interception: exactly **1 POST /api/tts** per unique AI reply.
3. **More human Indian accent** — ElevenLabs voice_settings tuned: `stability: 0.38, similarity_boost: 0.88, style: 0.55, use_speaker_boost: true` (warmer, more expressive delivery in all 3 languages). User still owns per-language voice IDs (Admin Panel → Voice Configuration) for clone-grade quality.

## Backlog (prioritized)
- **P1** Real Google Review automation via Place ID (currently UI-only stub)
- **P1** Add `/api/tts` hash-cache so repeat "Listen" clicks don't burn ElevenLabs quota (flagged by testing agent)
- **P2** LRU eviction for `chat_sessions` dict (memory pressure on long uptime)
- **P2** Daily WhatsApp campaign scheduler
- **P2** Multi-tenant live (multiple real restaurants in parallel)
- **P2** Refactor `server.py` (now 905 lines) → split routers (restaurant / chat / tts / orders / whatsapp / voice_ivr / analytics)
- **P3** Validate `X-Twilio-Signature` on inbound webhooks before going to prod

## Twilio setup user must complete
User owns Twilio voice-enabled number **+1 437 523 6468**. To go live:
1. Add `TWILIO_ACCOUNT_SID` + `TWILIO_AUTH_TOKEN` to `/app/backend/.env` (or paste in Admin → WhatsApp section — they're shared).
2. Twilio Console → Phone Numbers → +1 437 523 6468 → **A CALL COMES IN** → Webhook → `https://voice-order-hub-2.preview.emergentagent.com/api/webhook/twilio/voice` (POST).
3. Dial the number from any phone and order.

## Known: ElevenLabs supports Punjabi but needs a voice clone for native pronunciation. User can clone their own voice on ElevenLabs and paste voice IDs per language in Admin → Voice Configuration.
