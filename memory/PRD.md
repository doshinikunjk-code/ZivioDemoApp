# Zivio AI - Desi Road Ordering System PRD

## Original Problem Statement
User shared 7 files of existing Node.js/HTML app (Zivio AI - restaurant ordering demo for Desi Road, Brampton). Requested: voice AI with Indian accent, Hindi/Punjabi/English, background noise handling, 100% human touch, professional pitch. Phase 2: configurable restaurant, WhatsApp integration, kitchen/reception alerts, Google Review automation, analytics dashboard.

## Architecture
- **Backend**: FastAPI (Python) with emergentintegrations for Claude AI, httpx for ElevenLabs TTS, Twilio for WhatsApp
- **Frontend**: React with custom CSS (dark/gold theme)
- **Database**: MongoDB (restaurants, orders, analytics collections)
- **AI**: Claude Haiku 4.5 via Emergent LLM Key, ElevenLabs paid plan for TTS
- **Integrations**: Twilio WhatsApp (ready-to-connect), Google Review (ready-to-connect)

## What's Been Implemented

### Phase 1 (2026-04-19)
- Full React + FastAPI rebuild from original Node.js/HTML
- Claude AI chat with Indian fillers (ji, haan, achha, bilkul)
- ElevenLabs TTS with Hindi primer for Indian accent
- Background noise filtering (confidence threshold + min word count)
- Order detection in English/Punjabi/Hindi
- All 8 presentation screens
- Demo call modal, language switching, quick suggestions

### Phase 2 (2026-04-19)
- **Restaurant Configuration Admin Panel**: Full CRUD for name, tagline, city, phone, location, hours, logo, menu items (add/remove), special of the day, brand tagline, monthly price
- **Dynamic AI Prompts**: System prompt auto-generated from restaurant config in MongoDB
- **Order Persistence**: All orders stored in MongoDB with status tracking
- **Twilio WhatsApp Integration** (ready-to-connect): Send/receive WhatsApp messages, webhook endpoint for incoming messages, auto-reply with AI
- **Kitchen Alerts**: Auto WhatsApp alert to kitchen phone on order confirmation
- **Reception Alerts**: Auto WhatsApp alert to reception on order confirmation
- **Google Review Automation**: Auto review request to customer after order, configurable Google Place ID and review URL
- **Analytics Dashboard**: Total orders, conversations, revenue estimate, messages exchanged, WhatsApp messages sent, kitchen alerts, review requests, orders by language, recent orders table
- **Test Alert Buttons**: Test kitchen/reception alerts from admin panel
- **ElevenLabs TTS Working**: Paid plan enabled, TTS returns 200 with audio

## Test Results
- Phase 1: 100% (11/11 backend, all frontend)
- Phase 2: 100% (15/15 backend, all frontend)

## MongoDB Collections
- `restaurants`: Restaurant configurations (seeded with Desi Road default)
- `orders`: All orders with status, alerts, review tracking
- `analytics`: Event tracking for all system activity

## Prioritized Backlog
### P0 - None remaining
### P1
- Connect real Twilio credentials for live WhatsApp ordering
- Add Twilio phone number for voice calls (IVR)
- Admin panel: add new restaurant (multi-tenant)
### P2
- Daily special campaign scheduler (auto broadcast at 11am)
- Customer loyalty tracking (visit count, preferences)
- Real-time order status updates (WebSocket)
- Staff management and permissions
- Revenue reports with charts (Recharts)
