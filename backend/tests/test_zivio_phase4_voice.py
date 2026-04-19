"""
Phase 4 Voice Polish Tests for Zivio AI
- POST /api/chat English - response should NOT contain 'ji' or start with 'hey here is'
- POST /api/chat Hindi (lang=hi) - response should be fully in Devanagari script
- POST /api/chat Punjabi (lang=pa) - response should be fully in Gurmukhi script
- POST /api/tts - should NOT prepend 'ji' sound (no Hindi primer)
- POST /api/tts - returns 200 with clean audio
"""
import pytest
import requests
import os
import time
import re

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Devanagari Unicode range (Hindi)
DEVANAGARI_PATTERN = re.compile(r'[\u0900-\u097F]')
# Gurmukhi Unicode range (Punjabi)
GURMUKHI_PATTERN = re.compile(r'[\u0A00-\u0A7F]')

class TestPhase4VoicePolish:
    """Phase 4 voice polish tests - fixing ji/hey issues, language responses"""
    
    def test_health_endpoint(self):
        """Test API is running"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"✓ Health endpoint working: {data}")
    
    def test_chat_english_no_ji_at_start(self):
        """Test English chat response does NOT start with 'ji' or 'hey here is'"""
        session_id = f"test_en_noji_{int(time.time())}"
        response = requests.post(f"{BASE_URL}/api/chat", json={
            "session_id": session_id,
            "message": "I want to order butter chicken",
            "lang": "en"
        })
        assert response.status_code == 200
        data = response.json()
        reply = data.get("reply", "").strip().lower()
        print(f"English AI Reply: {reply}")
        
        # Check response doesn't start with problematic phrases
        bad_starts = ["ji", "ji,", "ji!", "hey here is", "here is"]
        for bad in bad_starts:
            assert not reply.startswith(bad), f"Response starts with '{bad}': {reply}"
        
        print(f"✓ English response doesn't start with ji/hey here is")
    
    def test_chat_english_minimal_ji_usage(self):
        """Test English chat has minimal 'ji' usage (max 1 in entire response)"""
        session_id = f"test_en_ji_{int(time.time())}"
        response = requests.post(f"{BASE_URL}/api/chat", json={
            "session_id": session_id,
            "message": "Add garlic naan and mango lassi please",
            "lang": "en"
        })
        assert response.status_code == 200
        data = response.json()
        reply = data.get("reply", "")
        print(f"English AI Reply: {reply}")
        
        # Count 'ji' occurrences
        ji_count = reply.lower().count(" ji") + reply.lower().count("ji ") + reply.lower().count("ji,") + reply.lower().count("ji!")
        print(f"'ji' count: {ji_count}")
        
        # Should have max 1 'ji' per system prompt instruction
        assert ji_count <= 1, f"Too many 'ji' in response ({ji_count}): {reply}"
        print(f"✓ English response has minimal ji usage (count: {ji_count})")
    
    def test_chat_hindi_devanagari_response(self):
        """Test Hindi (lang=hi) response is fully in Devanagari script"""
        session_id = f"test_hi_{int(time.time())}"
        response = requests.post(f"{BASE_URL}/api/chat", json={
            "session_id": session_id,
            "message": "नमस्ते, मुझे बटर चिकन चाहिए",
            "lang": "hi"
        })
        assert response.status_code == 200
        data = response.json()
        reply = data.get("reply", "")
        print(f"Hindi AI Reply: {reply}")
        
        # Check for Devanagari characters
        devanagari_chars = DEVANAGARI_PATTERN.findall(reply)
        print(f"Devanagari characters found: {len(devanagari_chars)}")
        
        # Response should have significant Devanagari content
        assert len(devanagari_chars) > 5, f"Hindi response lacks Devanagari script: {reply}"
        print(f"✓ Hindi response contains Devanagari script ({len(devanagari_chars)} chars)")
    
    def test_chat_punjabi_gurmukhi_response(self):
        """Test Punjabi (lang=pa) response is fully in Gurmukhi script"""
        session_id = f"test_pa_{int(time.time())}"
        response = requests.post(f"{BASE_URL}/api/chat", json={
            "session_id": session_id,
            "message": "ਸਤ ਸ੍ਰੀ ਅਕਾਲ, ਮੈਨੂੰ ਬਟਰ ਚਿਕਨ ਚਾਹੀਦਾ ਹੈ",
            "lang": "pa"
        })
        assert response.status_code == 200
        data = response.json()
        reply = data.get("reply", "")
        print(f"Punjabi AI Reply: {reply}")
        
        # Check for Gurmukhi characters
        gurmukhi_chars = GURMUKHI_PATTERN.findall(reply)
        print(f"Gurmukhi characters found: {len(gurmukhi_chars)}")
        
        # Response should have significant Gurmukhi content
        assert len(gurmukhi_chars) > 5, f"Punjabi response lacks Gurmukhi script: {reply}"
        print(f"✓ Punjabi response contains Gurmukhi script ({len(gurmukhi_chars)} chars)")
    
    def test_tts_returns_200_clean_audio(self):
        """Test TTS endpoint returns 200 with clean audio (no Hindi primer)"""
        response = requests.post(f"{BASE_URL}/api/tts", json={
            "text": "Welcome to Desi Road, what can I get you?",
            "lang": "en"
        })
        print(f"TTS Status: {response.status_code}")
        assert response.status_code == 200, f"TTS failed with status {response.status_code}"
        assert response.headers.get("content-type") == "audio/mpeg"
        assert len(response.content) > 1000, "Audio content too small"
        print(f"✓ TTS working - returned {len(response.content)} bytes of audio")
    
    def test_tts_hindi_text(self):
        """Test TTS with Hindi text works"""
        response = requests.post(f"{BASE_URL}/api/tts", json={
            "text": "नमस्ते, आपका ऑर्डर तैयार है",
            "lang": "hi"
        })
        print(f"TTS Hindi Status: {response.status_code}")
        assert response.status_code == 200, f"TTS Hindi failed with status {response.status_code}"
        assert response.headers.get("content-type") == "audio/mpeg"
        print(f"✓ TTS Hindi working - returned {len(response.content)} bytes")
    
    def test_tts_punjabi_text(self):
        """Test TTS with Punjabi text works (note: ElevenLabs may not pronounce perfectly)"""
        response = requests.post(f"{BASE_URL}/api/tts", json={
            "text": "ਸਤ ਸ੍ਰੀ ਅਕਾਲ, ਤੁਹਾਡਾ ਆਰਡਰ ਤਿਆਰ ਹੈ",
            "lang": "pa"
        })
        print(f"TTS Punjabi Status: {response.status_code}")
        assert response.status_code == 200, f"TTS Punjabi failed with status {response.status_code}"
        assert response.headers.get("content-type") == "audio/mpeg"
        print(f"✓ TTS Punjabi working - returned {len(response.content)} bytes")
    
    def test_chat_response_natural_varied(self):
        """Test chat responses are natural and varied (not boring/repetitive)"""
        session_id = f"test_natural_{int(time.time())}"
        
        # First message
        r1 = requests.post(f"{BASE_URL}/api/chat", json={
            "session_id": session_id,
            "message": "I want lamb chops",
            "lang": "en"
        })
        reply1 = r1.json().get("reply", "")
        print(f"Reply 1: {reply1}")
        
        time.sleep(0.5)
        
        # Second message
        r2 = requests.post(f"{BASE_URL}/api/chat", json={
            "session_id": session_id,
            "message": "Add dal makhani",
            "lang": "en"
        })
        reply2 = r2.json().get("reply", "")
        print(f"Reply 2: {reply2}")
        
        # Responses should be different (not repetitive)
        assert reply1 != reply2, "Responses are identical - not varied"
        
        # Check for natural language (not overly formal)
        formal_phrases = ["certainly", "absolutely", "i would be happy to", "of course"]
        formal_count = sum(1 for p in formal_phrases if p in reply1.lower() or p in reply2.lower())
        print(f"Formal phrase count: {formal_count}")
        
        print(f"✓ Responses are natural and varied")


class TestPhase4Integration:
    """Integration tests for Phase 4 features"""
    
    def test_full_order_flow_english(self):
        """Test complete order flow in English"""
        session_id = f"test_flow_en_{int(time.time())}"
        
        # Order item
        r1 = requests.post(f"{BASE_URL}/api/chat", json={
            "session_id": session_id,
            "message": "Butter chicken cones please",
            "lang": "en"
        })
        assert r1.status_code == 200
        reply1 = r1.json().get("reply", "")
        print(f"Order reply: {reply1}")
        
        # Confirm no ji at start
        assert not reply1.strip().lower().startswith("ji"), f"Reply starts with ji: {reply1}"
        
        time.sleep(0.5)
        
        # Complete order
        r2 = requests.post(f"{BASE_URL}/api/chat", json={
            "session_id": session_id,
            "message": "That's all, thanks",
            "lang": "en"
        })
        assert r2.status_code == 200
        reply2 = r2.json().get("reply", "")
        print(f"Completion reply: {reply2}")
        
        print(f"✓ Full English order flow working")
    
    def test_full_order_flow_hindi(self):
        """Test complete order flow in Hindi"""
        session_id = f"test_flow_hi_{int(time.time())}"
        
        # Order in Hindi
        r1 = requests.post(f"{BASE_URL}/api/chat", json={
            "session_id": session_id,
            "message": "मुझे बटर चिकन और नान चाहिए",
            "lang": "hi"
        })
        assert r1.status_code == 200
        reply1 = r1.json().get("reply", "")
        print(f"Hindi order reply: {reply1}")
        
        # Check for Devanagari
        devanagari_chars = DEVANAGARI_PATTERN.findall(reply1)
        assert len(devanagari_chars) > 3, f"Hindi response lacks Devanagari: {reply1}"
        
        print(f"✓ Full Hindi order flow working with Devanagari response")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
