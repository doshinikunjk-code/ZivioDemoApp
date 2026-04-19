"""Phase 10 — Ceremony template + dynamic upselling + chasing + IVR enhanced gather."""
import os
import re
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://voice-order-hub-2.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"


# ---------------- Regression: core endpoints ----------------
class TestRegression:
    def test_api_root(self):
        r = requests.get(f"{API}/", timeout=20)
        assert r.status_code == 200

    def test_restaurant_default(self):
        r = requests.get(f"{API}/restaurant/default", timeout=20)
        assert r.status_code == 200
        assert "name" in r.json()

    def test_analytics_summary(self):
        r = requests.get(f"{API}/analytics/summary", timeout=20)
        assert r.status_code == 200

    def test_orders_list(self):
        r = requests.get(f"{API}/orders", timeout=20)
        assert r.status_code == 200

    def test_voice_status(self):
        r = requests.get(f"{API}/voice/status", timeout=20)
        assert r.status_code == 200
        data = r.json()
        assert "webhook_url" in data

    def test_tts_endpoint_and_cache(self):
        payload = {"text": f"Hello Ceremony test {uuid.uuid4().hex[:6]}", "voice_id": "mActWQg9kibLro6Z2ouY"}
        r1 = requests.post(f"{API}/tts", json=payload, timeout=60)
        assert r1.status_code == 200
        assert r1.headers.get("X-Cache") in ("MISS", "HIT")
        # second call should be HIT
        r2 = requests.post(f"{API}/tts", json=payload, timeout=30)
        assert r2.status_code == 200
        assert r2.headers.get("X-Cache") == "HIT"


# ---------------- System prompt content ----------------
class TestSystemPrompt:
    def test_chat_prompt_has_dynamic_upselling_and_chasing(self):
        from backend.core import build_system_prompt  # type: ignore
        cfg = {"name": "T", "city": "B", "menu": [], "special_name": "X", "special_desc": "Y",
               "location": "", "phone": "", "hours": ""}
        p = build_system_prompt(cfg, is_call=False)
        assert "DYNAMIC UPSELLING" in p
        assert "CHASING" in p or "FOLLOW-UPS" in p
        assert "one upsell" in p.lower() or "one upsell per" in p.lower()

    def test_call_prompt_has_human_fillers(self):
        from backend.core import build_system_prompt  # type: ignore
        cfg = {"name": "T", "city": "B", "menu": [], "special_name": "X", "special_desc": "Y",
               "location": "", "phone": "", "hours": ""}
        p = build_system_prompt(cfg, is_call=True)
        low = p.lower()
        assert "mmm" in low and "one sec" in low
        assert "DYNAMIC UPSELLING" in p
        assert "CHASING" in p


# ---------------- Voice IVR TwiML enhanced ----------------
class TestVoiceIVRTwiML:
    def test_voice_inbound_twiml_has_enhanced_and_profanity_filter(self):
        # POST with no form body — handler tolerant (form vars default)
        r = requests.post(f"{API}/webhook/twilio/voice", data={"CallSid": f"TEST{uuid.uuid4().hex[:10]}", "From": "+15551234567"}, timeout=30)
        assert r.status_code == 200
        body = r.text
        assert "<Gather" in body
        assert 'enhanced="true"' in body
        assert 'profanityFilter="false"' in body


# ---------------- Dynamic upselling + chasing via /api/chat ----------------
def _chat(session_id: str, message: str) -> str:
    r = requests.post(f"{API}/chat", json={"session_id": session_id, "message": message}, timeout=60)
    assert r.status_code == 200, r.text
    data = r.json()
    return (data.get("response") or data.get("reply") or "").lower()


class TestDynamicUpselling:
    def test_butter_chicken_suggests_naan(self):
        sid = f"upsell_bc_{uuid.uuid4().hex[:6]}"
        reply = _chat(sid, "One butter chicken please")
        assert any(k in reply for k in ["naan", "paratha", "bread"]), f"no bread upsell in reply: {reply}"

    def test_biryani_suggests_lassi_or_raita(self):
        sid = f"upsell_br_{uuid.uuid4().hex[:6]}"
        reply = _chat(sid, "Chicken biryani please")
        assert any(k in reply for k in ["lassi", "raita", "yogurt", "cool"]), f"no cooling drink upsell: {reply}"

    def test_starter_prompts_main(self):
        sid = f"upsell_pt_{uuid.uuid4().hex[:6]}"
        reply = _chat(sid, "Paneer tikka only")
        assert any(k in reply for k in ["main", "curry", "biryani", "rice", "to go with", "anything else"]), \
            f"no main-course nudge: {reply}"


class TestChasing:
    def test_hesitation_gets_gentle_followup(self):
        sid = f"chase_{uuid.uuid4().hex[:6]}"
        reply = _chat(sid, "umm let me think")
        # Should NOT be generic 'how can I help'
        assert "how can i help" not in reply
        assert any(k in reply for k in [
            "take your time", "bestseller", "special", "suggest", "recommend",
            "today's", "popular", "if you like", "happy to",
        ]), f"reply not a chase: {reply}"
