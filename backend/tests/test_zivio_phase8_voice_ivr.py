"""
Phase 8 tests - Twilio Voice IVR + TTS expressive settings + double-read fix.
Covers:
  - POST /api/webhook/twilio/voice (inbound)
  - POST /api/webhook/twilio/voice/respond (speech turn + empty speech)
  - GET  /api/tts-cache/{id}.mp3 (valid + invalid)
  - GET  /api/voice/status
  - PUT  /api/restaurant/default persistence of twilio_voice_number
  - POST /api/tts sanity (expressive voice_settings still producing audio)
  - Regression: /api/restaurant/default price $599, /api/chat, /api/orders
"""
import os
import re
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://voice-order-hub-2.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"


@pytest.fixture(scope="module")
def client():
    s = requests.Session()
    return s


# ───────────────────────────── Twilio Voice IVR ─────────────────────────────

class TestTwilioVoiceInbound:
    def test_voice_inbound_returns_twiml(self, client):
        r = client.post(
            f"{API}/webhook/twilio/voice",
            data={"CallSid": "CA123testincbound", "From": "+14165551234"},
            timeout=45,
        )
        assert r.status_code == 200, r.text
        ct = r.headers.get("content-type", "")
        assert "xml" in ct.lower(), f"Expected XML content-type, got {ct}"
        body = r.text
        assert "<Response>" in body and "</Response>" in body
        assert "<Gather" in body and 'input="speech"' in body
        # Must have either <Play> (ElevenLabs) or <Say> (Polly fallback)
        assert ("<Play>" in body) or ("<Say" in body)
        # Fallback hangup for silence
        assert "<Hangup/>" in body

    def test_voice_inbound_play_url_is_valid_when_el_present(self, client):
        r = client.post(
            f"{API}/webhook/twilio/voice",
            data={"CallSid": "CA_play_url_test", "From": "+14165551234"},
            timeout=45,
        )
        assert r.status_code == 200
        body = r.text
        # If <Play> is used, the cached audio URL should be reachable
        m = re.search(r"<Play>(https?://[^<]+/api/tts-cache/[a-f0-9]+\.mp3)</Play>", body)
        if m:
            play_url = m.group(1)
            audio_r = requests.get(play_url, timeout=30)
            assert audio_r.status_code == 200, f"Cached audio not served: {audio_r.status_code}"
            assert "audio" in audio_r.headers.get("content-type", "").lower()
            assert len(audio_r.content) > 500, "Audio body too small"
        else:
            # Polly fallback path — must contain Indian-accent voice
            assert re.search(r'<Say[^>]*voice="Polly\.(Raveena-Neural|Aditi)"', body), body


class TestTwilioVoiceRespond:
    def test_respond_with_speech_returns_twiml(self, client):
        r = client.post(
            f"{API}/webhook/twilio/voice/respond",
            params={"session_id": "call_CA_resp_1", "lang": "en"},
            data={"SpeechResult": "I want butter chicken please", "Confidence": "0.95"},
            timeout=60,
        )
        assert r.status_code == 200, r.text
        body = r.text
        assert "<Response>" in body
        # Either Gather (mid-conversation) or Hangup (end) must be present
        assert ("<Gather" in body) or ("<Hangup/>" in body)
        assert ("<Play>" in body) or ("<Say" in body)

    def test_respond_with_empty_speech_is_graceful(self, client):
        r = client.post(
            f"{API}/webhook/twilio/voice/respond",
            params={"session_id": "call_CA_resp_empty", "lang": "en"},
            data={"SpeechResult": "", "Confidence": "0.0"},
            timeout=30,
        )
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        body = r.text
        assert "<Response>" in body
        assert "<Gather" in body, "Empty speech should re-prompt with another Gather"


# ───────────────────────────── TTS Cache ─────────────────────────────────────

class TestTTSCache:
    def test_cached_audio_after_voice_call(self, client):
        """Trigger an inbound /voice call, extract audio_id from <Play>, fetch it."""
        r = client.post(
            f"{API}/webhook/twilio/voice",
            data={"CallSid": "CA_cache_test", "From": "+14165551234"},
            timeout=45,
        )
        assert r.status_code == 200
        m = re.search(r"/api/tts-cache/([a-f0-9]+)\.mp3", r.text)
        if not m:
            pytest.skip("ElevenLabs not used (likely free-tier abuse block) — Play tag absent")
        audio_id = m.group(1)
        audio_r = client.get(f"{API}/tts-cache/{audio_id}.mp3", timeout=30)
        assert audio_r.status_code == 200
        assert "audio/mpeg" in audio_r.headers.get("content-type", "").lower()
        assert len(audio_r.content) > 500

    def test_cached_audio_invalid_id_returns_404(self, client):
        r = client.get(f"{API}/tts-cache/doesnotexist9999.mp3", timeout=15)
        assert r.status_code == 404


# ───────────────────────────── Voice status ──────────────────────────────────

class TestVoiceStatus:
    def test_voice_status_keys(self, client):
        r = client.get(f"{API}/voice/status", params={"restaurant_id": "default"}, timeout=15)
        assert r.status_code == 200
        data = r.json()
        for key in ["configured", "voice_number", "webhook_url", "elevenlabs_enabled"]:
            assert key in data, f"Missing key: {key}"
        assert data["webhook_url"].endswith("/api/webhook/twilio/voice")
        assert isinstance(data["configured"], bool)
        assert isinstance(data["elevenlabs_enabled"], bool)


# ─────────────────── Restaurant config: twilio_voice_number persistence ─────

class TestRestaurantVoiceNumber:
    def test_put_and_get_voice_number(self, client):
        # Set
        put = client.put(
            f"{API}/restaurant/default",
            json={"twilio_voice_number": "+14375236468"},
            timeout=15,
        )
        assert put.status_code == 200
        get = client.get(f"{API}/restaurant/default", timeout=15)
        assert get.status_code == 200
        assert get.json().get("twilio_voice_number") == "+14375236468"
        # Confirm /voice/status also reflects
        vs = client.get(f"{API}/voice/status", timeout=15).json()
        assert vs.get("voice_number") == "+14375236468"


# ───────────────────────────── TTS sanity ────────────────────────────────────

class TestTTSExpressive:
    def test_tts_endpoint_basic(self, client):
        r = client.post(
            f"{API}/tts",
            json={"text": "Hello from Desi Road!", "lang": "en", "restaurant_id": "default"},
            timeout=30,
        )
        # ElevenLabs free tier sometimes blocks - accept 200 or 500 with log warning
        if r.status_code == 500:
            pytest.skip(f"ElevenLabs TTS unavailable (possibly free-tier): {r.text[:120]}")
        assert r.status_code == 200
        assert "audio/mpeg" in r.headers.get("content-type", "").lower()
        assert len(r.content) > 500


# ───────────────────────────── Regression ────────────────────────────────────

class TestRegression:
    def test_restaurant_default_price(self, client):
        r = client.get(f"{API}/restaurant/default", timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert data.get("monthly_price") == "$599"

    def test_chat_endpoint(self, client):
        r = client.post(
            f"{API}/chat",
            json={
                "session_id": "regression_sess_phase8",
                "message": "Hi, what is the special today?",
                "lang": "en",
                "restaurant_id": "default",
            },
            timeout=60,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert "reply" in data
        assert isinstance(data["reply"], str) and len(data["reply"]) > 0

    def test_orders_create(self, client):
        r = client.post(
            f"{API}/orders",
            json={
                "restaurant_id": "default",
                "items": ["Butter Chicken Cones"],
                "session_id": "regression_sess_phase8",
                "language": "en",
                "customer_name": "TEST_regression",
            },
            timeout=30,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        # API returns order_id + status on create
        assert "order_id" in data and data["order_id"]
        assert data.get("status") == "confirmed"
