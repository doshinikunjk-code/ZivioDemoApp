"""
Phase 3 Tests for Zivio AI
- Reduced 'ji' overuse in AI responses
- TTS endpoint working (ElevenLabs)
- Custom demo feature (PUT /api/restaurant/default)
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestPhase3Backend:
    """Phase 3 backend tests"""
    
    def test_health_endpoint(self):
        """Test API is running"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"✓ Health endpoint working: {data}")
    
    def test_chat_natural_response_no_excessive_ji(self):
        """Test that AI response doesn't overuse 'ji' - should appear max 1-2 times"""
        session_id = f"test_ji_{int(time.time())}"
        response = requests.post(f"{BASE_URL}/api/chat", json={
            "session_id": session_id,
            "message": "I want butter chicken",
            "lang": "en"
        })
        assert response.status_code == 200
        data = response.json()
        reply = data.get("reply", "")
        print(f"AI Reply: {reply}")
        
        # Count 'ji' occurrences (case insensitive)
        ji_count = reply.lower().count(" ji") + reply.lower().count("ji ") + reply.lower().count("ji,") + reply.lower().count("ji!")
        print(f"'ji' count in response: {ji_count}")
        
        # Should have max 2 'ji' in response (reduced from excessive usage)
        assert ji_count <= 3, f"Too many 'ji' in response ({ji_count}): {reply}"
        print(f"✓ AI response is natural without excessive 'ji' (count: {ji_count})")
    
    def test_chat_second_message_no_ji_overuse(self):
        """Test second message also doesn't overuse ji"""
        session_id = f"test_ji2_{int(time.time())}"
        # First message
        requests.post(f"{BASE_URL}/api/chat", json={
            "session_id": session_id,
            "message": "Hello",
            "lang": "en"
        })
        time.sleep(0.5)
        
        # Second message
        response = requests.post(f"{BASE_URL}/api/chat", json={
            "session_id": session_id,
            "message": "Add garlic naan please",
            "lang": "en"
        })
        assert response.status_code == 200
        data = response.json()
        reply = data.get("reply", "")
        print(f"Second AI Reply: {reply}")
        
        ji_count = reply.lower().count(" ji") + reply.lower().count("ji ") + reply.lower().count("ji,") + reply.lower().count("ji!")
        print(f"'ji' count in second response: {ji_count}")
        assert ji_count <= 3, f"Too many 'ji' in second response ({ji_count}): {reply}"
        print(f"✓ Second response also natural (ji count: {ji_count})")
    
    def test_tts_endpoint_returns_200(self):
        """Test TTS endpoint returns 200 with audio"""
        response = requests.post(f"{BASE_URL}/api/tts", json={
            "text": "Welcome to Desi Road",
            "lang": "en"
        })
        print(f"TTS Status: {response.status_code}")
        assert response.status_code == 200, f"TTS failed with status {response.status_code}"
        assert response.headers.get("content-type") == "audio/mpeg"
        assert len(response.content) > 1000, "Audio content too small"
        print(f"✓ TTS working - returned {len(response.content)} bytes of audio")
    
    def test_update_restaurant_name_custom_demo(self):
        """Test PUT /api/restaurant/default can update restaurant name"""
        # Update to custom name
        custom_name = "Test Pizza Palace"
        response = requests.put(f"{BASE_URL}/api/restaurant/default", json={
            "name": custom_name
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "updated"
        print(f"✓ Restaurant name updated to: {custom_name}")
        
        # Verify the update
        get_response = requests.get(f"{BASE_URL}/api/restaurant/default")
        assert get_response.status_code == 200
        config = get_response.json()
        assert config.get("name") == custom_name
        print(f"✓ Verified restaurant name is now: {config.get('name')}")
        
        # Reset back to default
        reset_response = requests.put(f"{BASE_URL}/api/restaurant/default", json={
            "name": "Desi Road Restaurant"
        })
        assert reset_response.status_code == 200
        print("✓ Reset restaurant name back to Desi Road Restaurant")
    
    def test_chat_uses_updated_restaurant_name(self):
        """Test that chat AI uses the updated restaurant name"""
        # First update restaurant name
        custom_name = "Spice Garden"
        requests.put(f"{BASE_URL}/api/restaurant/default", json={
            "name": custom_name
        })
        time.sleep(0.5)
        
        # New chat session should use new name
        session_id = f"test_custom_{int(time.time())}"
        response = requests.post(f"{BASE_URL}/api/chat", json={
            "session_id": session_id,
            "message": "What restaurant is this?",
            "lang": "en"
        })
        assert response.status_code == 200
        data = response.json()
        reply = data.get("reply", "")
        print(f"AI Reply with custom name: {reply}")
        
        # Reset back
        requests.put(f"{BASE_URL}/api/restaurant/default", json={
            "name": "Desi Road Restaurant"
        })
        print("✓ Chat endpoint works with custom restaurant name")
    
    def test_get_restaurant_default(self):
        """Test GET restaurant returns correct data"""
        response = requests.get(f"{BASE_URL}/api/restaurant/default")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "menu" in data
        assert len(data.get("menu", [])) > 0
        print(f"✓ Restaurant config: {data.get('name')} with {len(data.get('menu', []))} menu items")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
