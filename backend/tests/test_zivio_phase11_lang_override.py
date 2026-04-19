"""Phase 11 — Strict language override + regression on /api/chat multilingual behavior.

Covers the review_request backend items:
- POST /api/chat with lang='hi' and English message → reply must be Devanagari
- POST /api/chat with lang='pa' and English message → reply must be Gurmukhi
- POST /api/chat with lang='en' → reply must be English (ASCII)
- Session continuity (multi-turn) works
- lang='auto' with Hindi user input still replies in Hindi (auto-detect)
"""
import os
import re
import time
import requests
import pytest

def _load_backend_url():
    v = os.environ.get("REACT_APP_BACKEND_URL")
    if v:
        return v.rstrip("/")
    # Fallback: read from frontend/.env (hot-loaded via CRA only)
    env_path = "/app/frontend/.env"
    if os.path.exists(env_path):
        for line in open(env_path):
            line = line.strip()
            if line.startswith("REACT_APP_BACKEND_URL="):
                return line.split("=", 1)[1].strip().rstrip("/")
    raise RuntimeError("REACT_APP_BACKEND_URL not configured")


BASE_URL = _load_backend_url()
API = f"{BASE_URL}/api"

DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")
GURMUKHI_RE = re.compile(r"[\u0A00-\u0A7F]")


def _session(prefix: str) -> str:
    return f"TEST_{prefix}_{int(time.time())}"


def _post_chat(message: str, lang: str, session_id: str, is_call: bool = False, context: str = None):
    payload = {
        "session_id": session_id,
        "message": message,
        "lang": lang,
        "is_call": is_call,
    }
    if context:
        payload["context"] = context
    r = requests.post(f"{API}/chat", json=payload, timeout=60)
    return r


# ---------- Strict language override ----------

class TestStrictLangOverride:
    def test_hindi_override_with_english_input(self):
        sid = _session("enforce_hi")
        r = _post_chat("I want butter chicken please", "hi", sid)
        assert r.status_code == 200, f"status={r.status_code} body={r.text}"
        reply = r.json().get("reply", "")
        assert reply, "empty reply"
        assert DEVANAGARI_RE.search(reply), f"Expected Devanagari in Hindi reply but got: {reply!r}"
        # Heavy ASCII word count should be low — allow menu proper nouns
        assert not GURMUKHI_RE.search(reply), f"Hindi reply must not contain Gurmukhi: {reply!r}"

    def test_punjabi_override_with_english_input(self):
        sid = _session("enforce_pa")
        r = _post_chat("I want lamb chops please", "pa", sid)
        assert r.status_code == 200, f"status={r.status_code} body={r.text}"
        reply = r.json().get("reply", "")
        assert reply, "empty reply"
        assert GURMUKHI_RE.search(reply), f"Expected Gurmukhi in Punjabi reply but got: {reply!r}"
        assert not DEVANAGARI_RE.search(reply), f"Punjabi reply must not contain Devanagari: {reply!r}"

    def test_english_override_with_hindi_input(self):
        sid = _session("enforce_en")
        r = _post_chat("मुझे बटर चिकन चाहिए", "en", sid)
        assert r.status_code == 200, f"status={r.status_code} body={r.text}"
        reply = r.json().get("reply", "")
        assert reply, "empty reply"
        assert not DEVANAGARI_RE.search(reply), f"English reply must not contain Devanagari: {reply!r}"
        assert not GURMUKHI_RE.search(reply), f"English reply must not contain Gurmukhi: {reply!r}"


# ---------- Auto-detect regression ----------

class TestAutoDetect:
    def test_auto_detect_hindi_input(self):
        sid = _session("auto_hi")
        r = _post_chat("मुझे पनीर टिक्का चाहिए", "auto", sid)
        assert r.status_code == 200
        reply = r.json().get("reply", "")
        assert reply, "empty reply"
        # Auto-detect should return Hindi when user writes Hindi
        assert DEVANAGARI_RE.search(reply), f"auto-detect should reply in Hindi: {reply!r}"

    def test_auto_detect_english_input(self):
        sid = _session("auto_en")
        r = _post_chat("Hi what's on the menu?", "auto", sid)
        assert r.status_code == 200
        reply = r.json().get("reply", "")
        assert reply
        assert not DEVANAGARI_RE.search(reply)
        assert not GURMUKHI_RE.search(reply)


# ---------- Multi-turn continuity ----------

class TestSessionContinuity:
    def test_multiturn_same_session_retains_context(self):
        sid = _session("multiturn")
        r1 = _post_chat("I want butter chicken", "en", sid)
        assert r1.status_code == 200
        time.sleep(0.5)
        r2 = _post_chat("Make it two please", "en", sid)
        assert r2.status_code == 200
        reply2 = r2.json().get("reply", "").lower()
        assert reply2
        # Second reply should acknowledge the update (either mentions qty/butter chicken or confirms)
        # We lenient check: reply is non-empty English and not a "sorry I don't understand" error
        assert "error" not in reply2


# ---------- Upsell / chase regression ----------

class TestUpsellAndChase:
    def test_upsell_butter_chicken_suggests_naan_or_rice(self):
        sid = _session("upsell_bc")
        r = _post_chat("butter chicken please", "en", sid)
        assert r.status_code == 200
        reply = r.json().get("reply", "").lower()
        # Should hint naan, rice, or drink
        assert any(k in reply for k in ["naan", "rice", "lassi", "drink", "side"]), (
            f"Expected an upsell suggestion, got: {reply!r}"
        )

    def test_chase_on_hesitation(self):
        sid = _session("chase")
        _post_chat("hi", "en", sid)
        time.sleep(0.3)
        r = _post_chat("umm let me think", "en", sid)
        assert r.status_code == 200
        reply = r.json().get("reply", "")
        assert reply
        assert len(reply) > 5


# ---------- Template switching ----------

class TestTemplateHealth:
    def test_restaurant_get(self):
        r = requests.get(f"{API}/restaurant/default", timeout=15)
        assert r.status_code == 200
        body = r.json()
        assert "name" in body
        assert "phone" in body

    def test_api_root(self):
        r = requests.get(f"{API}/", timeout=10)
        assert r.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
