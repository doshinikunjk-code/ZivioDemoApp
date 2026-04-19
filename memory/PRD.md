# Zivio AI PRD — Updated 2026-02-XX (Phase 10)

## Original Problem
Professional multi-industry Voice AI ordering demo (Desi Road restaurant base, extended to Dentist, Pharmacy, Pizza, Doctor, Skilled Trades, and now **Ceremony Indian Cuisine**) for pitching Brampton businesses. Supports English / Hindi / Punjabi with human-like tone, WhatsApp ordering, **live Twilio phone-call IVR**, kitchen alerts, admin panel, analytics. ElevenLabs TTS + Claude Haiku 4.5 via Emergent LLM key.

## All Phases Complete (100% test pass each)
- **Phase 1-9**: MVP → multi-industry switcher → unified pricing → VAD → Voice IVR → hash-cache → signature validation → modular refactor
- **Phase 10**: Ceremony Indian Cuisine template + dynamic upselling + customer chasing + more-human IVR voice + voice clone script ← current

## Phase 10 Details (shipped today)
### 1. Ceremony Indian Cuisine template (7th prototype)
- New entry `ceremony` in `/app/frontend/src/utils/businessTemplates.js` with:
  - Logo name: **Ceremony Indian Cuisine**, tagline *Celebrate the Taste of the India*
  - Full menu extracted from the owner's menu card (30+ items across breakfast, curries, breads, chinese corner, drinks, desserts, platters)
  - Tonight's special: **Non-veg Platter $26.99**
  - **Theme CSS vars** (orange `#EF6B2E` + cream + navy accent) applied via `useEffect` in `App.js` → `document.documentElement.style.setProperty(...)` with clean reset on template change.
  - Distinctive Features + Compare rows highlighting *Smart Upselling* and *Your own cloned voice*

### 2. Dynamic upselling (LLM system-prompt level)
- System prompt now includes explicit pairing rules but phrased as examples so the LLM composes contextually:
  - Curry → Naan / Paratha
  - Biryani → Mango Lassi / Raita
  - Starters-only → nudge toward main
  - 2+ items → ask about dessert (Gulab Jamun / Kulfi)
- **Only ONE upsell per reply. Never push. If declined, move on.** (Verified in live LLM replies.)

### 3. Customer "chasing" follow-ups
- If caller pauses / hesitates ("umm", "let me think", "hmm") → AI offers help: *"Take your time — want me to share tonight's special?"*
- If idle mid-order → *"Anything else, or should I finalize?"*
- If unsure → surface the special dynamically

### 4. More-human phone voice
- IVR system prompt now explicitly encourages natural fillers (*"mmm"*, *"one sec"*, *"okay"*, *"sure"*) and varied replies.
- Twilio `<Gather>` upgraded: `enhanced="true"` (Google Enhanced Speech Model) + `profanityFilter="false"` for better Hinglish/Punjabi transcription.
- **For truly human voice on calls: user must clone their voice** → /app/VOICE_CLONE_SCRIPT.md

### 5. Voice clone script
- `/app/VOICE_CLONE_SCRIPT.md` — 90-second read-aloud script in English + Hindi + Punjabi, recording tips (phone mic, quiet room, smile-while-reading), ElevenLabs Instant Clone upload steps, and exact Admin Panel paste instructions.

## Backlog (prioritized)
- **P1** Real Google Review automation via Place ID
- **P2** LRU eviction for `chat_sessions` dict
- **P2** Daily WhatsApp campaign scheduler
- **P2** Multi-tenant live support
- **P3** Post-call WhatsApp reorder link (Brampton pitch enhancer)
- **P3** Push to GitHub → Railway deploy (user will trigger via Save to Github + Railway)

## Twilio setup user must complete to go live
User owns Twilio voice-enabled number **+1 437 523 6468**.
1. Paste `TWILIO_ACCOUNT_SID` + `TWILIO_AUTH_TOKEN` into Admin → WhatsApp Integration (or `/app/backend/.env`).
2. Twilio Console → Phone Numbers → +1 437 523 6468 → **A CALL COMES IN** → Webhook: `https://voice-order-hub-2.preview.emergentagent.com/api/webhook/twilio/voice` (POST).
3. Dial the number.

Signature validation auto-activates when `TWILIO_AUTH_TOKEN` is set.

## For best voice quality on both web + phone
User should clone their own voice via `/app/VOICE_CLONE_SCRIPT.md` and paste voice IDs per language in Admin → Voice Configuration. Default ElevenLabs stock voice is the reason the current call sounds synthetic.
