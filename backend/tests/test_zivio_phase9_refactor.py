"""Phase 9 — full backend regression after monolith refactor into routers
+ TTS hash-cache + X-Twilio-Signature validation.

Public endpoints only; no auth.
"""
import os
import time

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://voice-order-hub-2.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"


@pytest.fixture(scope="module")
def client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# ─────────────────────────── Health / Root ───────────────────────────
class TestHealth:
    def test_root(self, client):
        r = client.get(f"{API}/")
        assert r.status_code == 200


# ─────────────────────────── Restaurant ──────────────────────────────
class TestRestaurant:
    def test_get_default(self, client):
        r = client.get(f"{API}/restaurant/default")
        assert r.status_code == 200
        d = r.json()
        assert d["id"] == "default"
        # unified pricing must survive the refactor
        assert d.get("monthly_price") == "$599"
        # twilio voice number must persist
        assert d.get("twilio_voice_number") == "+14375236468"
        assert isinstance(d.get("menu"), list) and len(d["menu"]) > 0

    def test_put_default_no_change(self, client):
        cur = client.get(f"{API}/restaurant/default").json()
        # Echo back name to confirm PUT path works
        payload = {"name": cur["name"]}
        r = client.put(f"{API}/restaurant/default", json=payload)
        assert r.status_code == 200, r.text
        after = client.get(f"{API}/restaurant/default").json()
        assert after["name"] == cur["name"]

    def test_list_restaurants(self, client):
        r = client.get(f"{API}/restaurants")
        assert r.status_code == 200
        assert isinstance(r.json(), list)


# ─────────────────────────── Chat ────────────────────────────────────
class TestChat:
    def test_reset(self, client):
        r = client.post(f"{API}/chat/reset", json={"session_id": "TEST_phase9_sess"})
        assert r.status_code == 200

    def test_chat_hello(self, client):
        r = client.post(f"{API}/chat", json={
            "session_id": "TEST_phase9_sess",
            "message": "Hello",
            "restaurant_id": "default",
        })
        assert r.status_code == 200, r.text
        data = r.json()
        # Endpoint returns {"reply": "..."}
        assert "reply" in data and isinstance(data["reply"], str) and len(data["reply"]) > 0


# ─────────────────────────── Orders ──────────────────────────────────
class TestOrders:
    created_id = None

    def test_create_order(self, client):
        payload = {
            "restaurant_id": "default",
            "customer_name": "TEST_Phase9",
            "customer_phone": "+15551230000",
            "items": ["Plumbing Service Call x1 - $89"],
            "session_id": "TEST_phase9_sess",
            "language": "en",
        }
        r = client.post(f"{API}/orders", json=payload)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "order_id" in data
        assert data.get("status") == "confirmed"
        TestOrders.created_id = data["order_id"]

    def test_list_orders(self, client):
        r = client.get(f"{API}/orders?restaurant_id=default")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_update_order_status(self, client):
        assert TestOrders.created_id, "order must be created first"
        # status is a query param
        r = client.put(f"{API}/orders/{TestOrders.created_id}/status?status=ready")
        assert r.status_code == 200, r.text


# ─────────────────────────── WhatsApp ────────────────────────────────
class TestWhatsApp:
    def test_status(self, client):
        r = client.get(f"{API}/whatsapp/status")
        assert r.status_code == 200
        assert "configured" in r.json()

    def test_send_returns_200_even_if_not_configured(self, client):
        r = client.post(f"{API}/whatsapp/send", json={
            "restaurant_id": "default",
            "to": "+15551239999",
            "message": "TEST_phase9 hello",
        })
        assert r.status_code == 200
        assert "sent" in r.json()


# ─────────────────────────── Alerts ──────────────────────────────────
class TestAlerts:
    def test_kitchen_test(self, client):
        r = client.post(f"{API}/alerts/kitchen/test", json={"restaurant_id": "default"})
        assert r.status_code == 200

    def test_reception_test(self, client):
        r = client.post(f"{API}/alerts/reception/test", json={"restaurant_id": "default"})
        assert r.status_code == 200


# ─────────────────────────── Reviews ─────────────────────────────────
class TestReviews:
    def test_request(self, client):
        r = client.post(f"{API}/reviews/request", json={
            "order_id": TestOrders.created_id or "TEST_noorder",
            "customer_phone": "+15550000000",
            "restaurant_id": "default",
        })
        assert r.status_code == 200

    def test_schedule(self, client):
        # schedule takes order_id as a QUERY param
        oid = TestOrders.created_id or "TEST_noorder"
        r = client.post(f"{API}/reviews/schedule?order_id={oid}")
        # 200 for a real order, or 404 if order not found — both are valid behavior
        assert r.status_code in (200, 404), r.text


# ─────────────────────────── Analytics ───────────────────────────────
class TestAnalytics:
    def test_track(self, client):
        r = client.post(f"{API}/analytics/track", json={
            "restaurant_id": "default",
            "event_type": "TEST_phase9_event",
            "metadata": {"x": 1},
        })
        assert r.status_code == 200

    def test_summary(self, client):
        r = client.get(f"{API}/analytics/summary?restaurant_id=default")
        assert r.status_code == 200
        d = r.json()
        assert isinstance(d, dict)

    def test_events(self, client):
        r = client.get(f"{API}/analytics/events?restaurant_id=default")
        assert r.status_code == 200
        assert isinstance(r.json(), list)


# ─────────────────────────── TTS hash-cache ──────────────────────────
class TestTTSCache:
    def test_tts_miss_then_hit(self, client):
        payload = {"text": "hello world phase nine cache test", "lang": "en", "restaurant_id": "default"}
        t0 = time.time()
        r1 = client.post(f"{API}/tts", json=payload)
        d1 = time.time() - t0
        if r1.status_code != 200:
            pytest.skip(f"TTS upstream unavailable: {r1.status_code} {r1.text[:200]}")
        assert r1.headers.get("content-type", "").startswith("audio/mpeg")
        assert len(r1.content) > 0
        assert r1.headers.get("X-Cache") == "MISS"

        t1 = time.time()
        r2 = client.post(f"{API}/tts", json=payload)
        d2 = time.time() - t1
        assert r2.status_code == 200
        assert r2.headers.get("X-Cache") == "HIT"
        assert len(r2.content) == len(r1.content)
        # HIT should be meaningfully faster (no upstream call).
        assert d2 < d1, f"HIT {d2:.2f}s should be < MISS {d1:.2f}s"

    def test_tts_different_text_misses(self, client):
        payload = {"text": f"unique text {time.time()}", "lang": "en", "restaurant_id": "default"}
        r = client.post(f"{API}/tts", json=payload)
        if r.status_code != 200:
            pytest.skip(f"TTS upstream unavailable: {r.status_code}")
        assert r.headers.get("X-Cache") == "MISS"

    def test_tts_different_voice_id_misses(self, client):
        # Same text but explicit different voice_id → different cache key
        text = "cache isolation text phase nine"
        base = {"text": text, "lang": "en", "restaurant_id": "default"}
        r1 = client.post(f"{API}/tts", json={**base, "voice_id": "mActWQg9kibLro6Z2ouY"})
        if r1.status_code != 200:
            pytest.skip(f"TTS upstream unavailable: {r1.status_code}")
        # Second call same voice → HIT
        r1b = client.post(f"{API}/tts", json={**base, "voice_id": "mActWQg9kibLro6Z2ouY"})
        assert r1b.headers.get("X-Cache") == "HIT"
        # Third call different voice → MISS (or upstream error — then skip)
        r2 = client.post(f"{API}/tts", json={**base, "voice_id": "21m00Tcm4TlvDq8ikWAM"})
        if r2.status_code != 200:
            pytest.skip(f"Alternate voice unavailable: {r2.status_code}")
        assert r2.headers.get("X-Cache") == "MISS"


# ─────────────────────────── Voice IVR ───────────────────────────────
class TestVoiceIVR:
    def test_voice_inbound(self, client):
        # Twilio posts form-encoded data. No signature in dev → allowed.
        r = requests.post(
            f"{API}/webhook/twilio/voice",
            data={"CallSid": "TEST_phase9_call", "From": "+15550001111"},
            timeout=30,
        )
        assert r.status_code == 200, r.text
        assert r.headers.get("content-type", "").startswith("application/xml")
        body = r.text
        assert "<Response>" in body
        assert "<Gather" in body
        # Either <Play> (ElevenLabs worked) or <Say> (Polly fallback)
        assert ("<Play>" in body) or ("<Say" in body)

    def test_voice_respond(self, client):
        r = requests.post(
            f"{API}/webhook/twilio/voice/respond?session_id=call_TEST_phase9_call&lang=en",
            data={"SpeechResult": "I want butter chicken", "Confidence": "0.9"},
            timeout=60,
        )
        assert r.status_code == 200, r.text
        assert "<Response>" in r.text

    def test_voice_status(self, client):
        r = client.get(f"{API}/voice/status")
        assert r.status_code == 200
        d = r.json()
        assert "configured" in d
        assert d.get("webhook_url") == "/api/webhook/twilio/voice"


# ─────────────────────────── Signature validation (dev mode) ─────────
class TestTwilioSignatureDevMode:
    """In dev (no TWILIO_AUTH_TOKEN) webhooks must succeed without signature."""

    def test_voice_webhook_no_signature_allowed(self, client):
        r = requests.post(f"{API}/webhook/twilio/voice", data={"CallSid": "TEST_sig", "From": "+1"})
        assert r.status_code == 200

    def test_whatsapp_webhook_no_signature_allowed(self, client):
        r = requests.post(f"{API}/whatsapp/webhook", data={"From": "+1", "Body": "hi"})
        assert r.status_code == 200
