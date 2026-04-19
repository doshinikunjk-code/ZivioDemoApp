# Zivio AI PRD — Updated 2026-02-XX (Phase 7)

## Original Problem
Professional multi-industry Voice AI ordering demo (Desi Road restaurant base, extended to Dentist, Pharmacy, Pizza, Doctor, Skilled Trades) for pitching Brampton businesses. Supports English / Hindi / Punjabi with human-like tone, WhatsApp ordering, kitchen alerts, admin panel, analytics. ElevenLabs TTS + Claude Haiku 4.5 chat via Emergent LLM key.

## All Phases Complete (100% test pass)
- **Phase 1**: Core MVP — chat, TTS, orders
- **Phase 2**: Admin Panel, WhatsApp stub, Alerts, Analytics
- **Phase 3**: Custom Demo Bar, Polish
- **Phase 4**: Voice fix — removed Hindi "ji" primer, echo fix, faster + natural voice
- **Phase 5**: Phone (437) 331-5615, per-language voice IDs, Punjabi voice clone support
- **Phase 6**: Multi-industry prototype switcher (6 templates)
- **Phase 7**: VAD noise-filter + unified $599 pricing ← current

## Phase 7 Details (shipped today)
1. **Voice Activity Detection (VAD)** — `/app/frontend/src/utils/vad.js`
   - Opens mic with `echoCancellation + noiseSuppression + autoGainControl`
   - Calibrates ambient noise floor for 400 ms (70th percentile of samples)
   - Speech threshold = max(noiseFloor × 3, 0.025)
   - Sustained speech detection: 180 ms on / 550 ms off hysteresis
   - Rejects transcripts where peak energy never exceeded threshold (background chatter)
   - Blocks mic start while AI is speaking (prevents echo loop)
2. **Mic UI feedback** — calibrating / listening / speaking states with live level meter
3. **Unified pricing** — all 6 industry templates now **$599/month** (was $499/$599/$699/$799 mixed)
4. **Stale test fixed** — `/app/backend/tests/test_zivio_phase6_templates.py` no longer restores $799

## Known Backlog / Future
- **P1** Twilio WhatsApp live wiring (needs user credentials: Account SID + Auth Token + WhatsApp number)
- **P1** Google Review automation via Place ID (currently UI-only stub)
- **P2** Voice IVR (Twilio phone calls — customer dials in, talks to AI live)
- **P2** Daily WhatsApp campaign scheduler
- **P2** Multi-tenant live (multiple real restaurants in parallel)
- Refactor: server.py (662 lines) → split into routers (restaurant / chat / tts / orders / whatsapp / analytics)

## Known: ElevenLabs supports Punjabi but needs voice clone for native pronunciation (user must clone Punjabi voice on their ElevenLabs account and paste voice ID into Admin Panel).
