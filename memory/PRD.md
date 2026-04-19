# Zivio AI - Desi Road Ordering System PRD

## Original Problem Statement
Voice AI ordering demo for Desi Road restaurant, Brampton. Indian accent, Hindi/Punjabi/English, background noise handling, human touch, professional pitch for hotels.

## Architecture
- **Backend**: FastAPI + emergentintegrations (Claude Haiku 4.5) + httpx (ElevenLabs TTS) + Twilio (WhatsApp)
- **Frontend**: React + custom CSS dark/gold theme
- **Database**: MongoDB (restaurants, orders, analytics)
- **Voice**: ElevenLabs paid plan, Riya Rao voice, 1.05x playback

## What's Been Implemented

### Phase 1: Core MVP
- React + FastAPI rebuild, Claude AI chat, ElevenLabs TTS, background noise filtering, order detection, 8 presentation screens, demo call modal

### Phase 2: Business Features
- Restaurant config admin panel, Twilio WhatsApp ready-to-connect, kitchen/reception alerts, Google Review automation, analytics dashboard, order persistence in MongoDB

### Phase 3: Polish & Custom Demo
- Reduced "ji" overuse — AI sounds natural and human
- Faster voice (1.05x playback speed)
- Fixed echo/double voiceover — single audio stream guaranteed
- Removed Emergent badge
- "Try with YOUR Restaurant" custom demo bar — hotel owners type name, AI adapts instantly

## Test Results: 100% across all phases
- Phase 1: 11/11 backend, all frontend
- Phase 2: 15/15 backend, all frontend
- Phase 3: 7/7 backend, all frontend

## Prioritized Backlog
### P1: Connect Twilio creds, add voice IVR, multi-tenant support
### P2: Daily campaign scheduler, loyalty tracking, WebSocket order updates, revenue charts
