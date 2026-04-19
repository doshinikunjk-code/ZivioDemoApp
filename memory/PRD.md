# Zivio AI - Desi Road Ordering System PRD

## Original Problem Statement
User shared 7 files of their existing Node.js/HTML application (Zivio AI - restaurant ordering demo for Desi Road, Brampton). Requested: voice AI with complete Indian accent, Hindi/Punjabi/English conversation support, background noise handling, 100% human touch with emotions, professional pitch-ready for approaching hotels in Brampton.

## Architecture
- **Backend**: FastAPI (Python) with emergentintegrations for Claude AI chat, httpx for ElevenLabs TTS proxy
- **Frontend**: React with custom CSS (faithful recreation of original dark/gold theme)
- **Database**: MongoDB (available but not actively used for chat sessions - sessions stored in-memory)
- **AI**: Claude Haiku 4.5 via Emergent LLM Key for chat, ElevenLabs for TTS

## User Personas
1. **Restaurant Owner** (pitch target) - Viewing the demo to see how AI ordering works
2. **Customer** (simulated in demo) - Ordering food in English, Punjabi, or Hindi
3. **Nik** (Zivio sales person) - Presenting the demo to restaurant owners

## Core Requirements (Static)
- AI ordering assistant for Desi Road restaurant
- Multi-language support: English, Punjabi (Gurmukhi), Hindi (Devanagari)
- Voice AI with Indian accent (ElevenLabs TTS + browser STT)
- Background noise filtering (confidence threshold + minimum word count)
- Human-touch AI responses with Indian fillers (ji, haan, achha, bilkul)
- Emotional AI responses (warm, appreciative, empathetic)
- Order detection and tracking from chat
- Customer memory (returning customer recognition via localStorage)
- Add-to-existing-order support (within 60 min window)
- Kitchen alert simulation on order confirmation
- Demo call simulation modal
- Business case presentation screens (Problem, Solution, Features, Compare, Kitchen, Campaign, Pricing, Get Started)

## What's Been Implemented (2026-04-19)
- Full React + FastAPI rebuild from original Node.js/HTML monolith
- Claude AI chat via Emergent LLM Key with session management
- ElevenLabs TTS proxy with Hindi primer for Indian accent
- Background noise filtering: confidence threshold (0.55+), minimum word count
- Conversation state machine: prevents restart on background noise
- Indian filler words in AI system prompt (ji, haan, achha, bilkul, zaroor)
- Emotional AI responses (warm, appreciative)
- Order item detection from chat in multiple languages
- Order deduplication logic
- Order confirmation with kitchen ticket display
- All 8 presentation screens faithfully recreated
- Demo call modal with speech recognition
- Language tab switching (Auto/English/Punjabi/Hindi)
- Quick suggestion buttons
- Responsive design
- Browser SpeechSynthesis fallback for TTS

## Known Limitations
- ElevenLabs TTS may return 500 if the API key is on free tier and blocked by abuse detection
- Browser SpeechSynthesis fallback works but with less natural voice
- Chat sessions stored in-memory (not persisted across server restarts)

## Prioritized Backlog
### P0 (Critical)
- None remaining

### P1 (Important)
- Persist chat sessions to MongoDB for durability
- Add ElevenLabs paid key or alternative TTS service
- WhatsApp Business API integration for real ordering

### P2 (Nice to have)
- Analytics dashboard for demo engagement tracking
- Multiple restaurant configuration support
- Real kitchen alert integration (WhatsApp API or printer)
- Google Review automation integration
- Daily special campaign scheduler

## Next Tasks
1. Upgrade ElevenLabs to paid tier for reliable TTS
2. Add WhatsApp Business API integration
3. Add analytics tracking for pitch demos
4. Make restaurant configurable (not just Desi Road)
