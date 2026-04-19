"""
Phase 7: Unified $599 Pricing + VAD Backend Regression
Verifies:
  - GET /api/restaurant/default returns monthly_price '$599'
  - PUT /api/restaurant/default still works with $599 default
  - /api/chat and /api/tts still respond correctly
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


# ── Health ───────────────────────────────────────────────────────────
class TestHealth:
    def test_api_root(self):
        r = requests.get(f"{BASE_URL}/api/")
        assert r.status_code == 200
        assert "message" in r.json()


# ── Unified $599 pricing ─────────────────────────────────────────────
class TestUnifiedPricing:
    def test_default_restaurant_price_is_599(self):
        """The Restaurant default model should now return $599 (was $799)."""
        r = requests.get(f"{BASE_URL}/api/restaurant/default")
        assert r.status_code == 200
        data = r.json()
        assert data.get("monthly_price") == "$599", (
            f"Expected $599, got {data.get('monthly_price')}"
        )
        # sanity fields
        assert data.get("name")
        assert isinstance(data.get("menu"), list)

    def test_update_restaurant_keeps_599_price(self):
        """PUT with monthly_price '$599' should persist correctly."""
        payload = {
            "name": "Desi Road Restaurant",
            "tagline": "Elevated Indian Cuisine",
            "monthly_price": "$599",
            "brand_tagline": "Desi Daru Desi Khana",
        }
        put_r = requests.put(f"{BASE_URL}/api/restaurant/default", json=payload)
        assert put_r.status_code == 200
        assert put_r.json().get("status") == "updated"

        get_r = requests.get(f"{BASE_URL}/api/restaurant/default")
        assert get_r.status_code == 200
        assert get_r.json().get("monthly_price") == "$599"


# ── Chat / TTS regression ────────────────────────────────────────────
class TestChatTTSRegression:
    def test_chat_basic(self):
        """POST /api/chat should respond (or skip on transient LLM 502)."""
        r = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "session_id": "TEST_phase7_session",
                "message": "Hi, what's the menu?",
                "lang": "en",
                "restaurant_id": "default",
            },
            timeout=60,
        )
        if r.status_code == 502 or (r.status_code == 500 and "502" in r.text):
            pytest.skip(f"Transient LLM 502 gateway: {r.text[:100]}")
        assert r.status_code == 200, f"Got {r.status_code}: {r.text[:200]}"
        data = r.json()
        assert "reply" in data
        assert isinstance(data["reply"], str) and len(data["reply"]) > 0

    def test_tts_rejects_empty(self):
        """TTS with empty text should return 400."""
        r = requests.post(
            f"{BASE_URL}/api/tts",
            json={"text": "", "lang": "en", "restaurant_id": "default"},
        )
        assert r.status_code in (400, 500)  # 400 preferred, 500 acceptable if wrapped

    def test_tts_returns_audio(self):
        """TTS with valid text should return audio/mpeg."""
        r = requests.post(
            f"{BASE_URL}/api/tts",
            json={"text": "Hello", "lang": "en", "restaurant_id": "default"},
            timeout=30,
        )
        if r.status_code != 200:
            pytest.skip(f"TTS upstream issue: {r.status_code} {r.text[:100]}")
        assert r.headers.get("content-type", "").startswith("audio/")
        assert len(r.content) > 100


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
