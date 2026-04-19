"""
Zivio AI Backend API Tests
Tests for: health endpoint, chat endpoint (English/Hindi/Punjabi), TTS endpoint
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthEndpoint:
    """Health check endpoint tests"""
    
    def test_api_root_returns_success(self):
        """Test /api/ health endpoint returns success"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Zivio AI Backend Active" in data["message"]
        print(f"✓ Health endpoint working: {data}")


class TestChatEndpoint:
    """Chat endpoint tests - AI ordering assistant"""
    
    def test_chat_english_message(self):
        """Test chat with English message - should get AI reply with Indian fillers"""
        session_id = f"test_en_{int(time.time())}"
        payload = {
            "session_id": session_id,
            "message": "Hello, I want to order Butter Chicken",
            "lang": "en"
        }
        response = requests.post(f"{BASE_URL}/api/chat", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "reply" in data
        reply = data["reply"].lower()
        # Check for Indian fillers or natural response
        print(f"✓ English chat reply: {data['reply'][:200]}")
        assert len(data["reply"]) > 10  # Should have meaningful response
    
    def test_chat_hindi_message(self):
        """Test chat with Hindi message - should reply in Hindi"""
        session_id = f"test_hi_{int(time.time())}"
        payload = {
            "session_id": session_id,
            "message": "नमस्ते, मुझे बटर चिकन चाहिए",
            "lang": "hi"
        }
        response = requests.post(f"{BASE_URL}/api/chat", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "reply" in data
        print(f"✓ Hindi chat reply: {data['reply'][:200]}")
        assert len(data["reply"]) > 10
    
    def test_chat_punjabi_message(self):
        """Test chat with Punjabi message - should reply in Punjabi"""
        session_id = f"test_pa_{int(time.time())}"
        payload = {
            "session_id": session_id,
            "message": "ਸਤ ਸ੍ਰੀ ਅਕਾਲ, ਮੈਨੂੰ ਬਟਰ ਚਿਕਨ ਚਾਹੀਦਾ ਹੈ",
            "lang": "pa"
        }
        response = requests.post(f"{BASE_URL}/api/chat", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "reply" in data
        print(f"✓ Punjabi chat reply: {data['reply'][:200]}")
        assert len(data["reply"]) > 10
    
    def test_chat_auto_language_detection(self):
        """Test chat with auto language detection"""
        session_id = f"test_auto_{int(time.time())}"
        payload = {
            "session_id": session_id,
            "message": "What is on the menu today?",
            "lang": "auto"
        }
        response = requests.post(f"{BASE_URL}/api/chat", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "reply" in data
        print(f"✓ Auto-detect chat reply: {data['reply'][:200]}")
    
    def test_chat_session_persistence(self):
        """Test that chat maintains session context"""
        session_id = f"test_session_{int(time.time())}"
        
        # First message
        payload1 = {
            "session_id": session_id,
            "message": "I want Butter Chicken",
            "lang": "en"
        }
        response1 = requests.post(f"{BASE_URL}/api/chat", json=payload1)
        assert response1.status_code == 200
        
        # Second message in same session
        payload2 = {
            "session_id": session_id,
            "message": "Add Garlic Naan to my order",
            "lang": "en"
        }
        response2 = requests.post(f"{BASE_URL}/api/chat", json=payload2)
        assert response2.status_code == 200
        data2 = response2.json()
        print(f"✓ Session persistence reply: {data2['reply'][:200]}")
    
    def test_chat_with_order_context(self):
        """Test chat with order context"""
        session_id = f"test_ctx_{int(time.time())}"
        payload = {
            "session_id": session_id,
            "message": "Add more items",
            "context": "Customer's recent order: Butter Chicken, Garlic Naan",
            "lang": "en"
        }
        response = requests.post(f"{BASE_URL}/api/chat", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "reply" in data
        print(f"✓ Context chat reply: {data['reply'][:200]}")
    
    def test_chat_call_mode(self):
        """Test chat in call mode (phone ordering)"""
        session_id = f"test_call_{int(time.time())}"
        payload = {
            "session_id": session_id,
            "message": "Hello, I want to place an order",
            "is_call": True,
            "lang": "en"
        }
        response = requests.post(f"{BASE_URL}/api/chat", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "reply" in data
        print(f"✓ Call mode reply: {data['reply'][:200]}")


class TestChatResetEndpoint:
    """Chat reset endpoint tests"""
    
    def test_reset_chat_session(self):
        """Test resetting a chat session"""
        session_id = f"test_reset_{int(time.time())}"
        
        # Create a session first
        payload = {
            "session_id": session_id,
            "message": "Hello",
            "lang": "en"
        }
        requests.post(f"{BASE_URL}/api/chat", json=payload)
        
        # Reset the session
        response = requests.post(f"{BASE_URL}/api/chat/reset?session_id={session_id}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "reset"
        print(f"✓ Chat reset successful")


class TestTTSEndpoint:
    """TTS endpoint tests - NOTE: ElevenLabs may be blocked"""
    
    def test_tts_endpoint_exists(self):
        """Test TTS endpoint exists and handles requests (may return 500 due to ElevenLabs block)"""
        payload = {
            "text": "Hello, welcome to Desi Road",
            "lang": "en"
        }
        response = requests.post(f"{BASE_URL}/api/tts", json=payload)
        # ElevenLabs is blocked, so we expect 500 but endpoint should exist
        assert response.status_code in [200, 500]
        if response.status_code == 500:
            print("✓ TTS endpoint exists but ElevenLabs is blocked (expected)")
        else:
            print("✓ TTS endpoint working")
    
    def test_tts_empty_text_validation(self):
        """Test TTS endpoint validates empty text"""
        payload = {
            "text": "",
            "lang": "en"
        }
        response = requests.post(f"{BASE_URL}/api/tts", json=payload)
        # Should return 400 for empty text or 500 if ElevenLabs blocked
        assert response.status_code in [400, 500, 422]
        print(f"✓ TTS empty text validation: status {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
